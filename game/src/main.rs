// A shipped Windows build opens as a game, without a console window beside it (a debug build keeps its console).
#![cfg_attr(all(windows, not(debug_assertions)), windows_subsystem = "windows")]
//! gam2: the game's skeleton — the menu, the class and the leader, a run of fifteen battles with its forks, spoils,
//! trader, events and camps (game.rs, screens.rs; the run itself is sim::run) — drawn with the game's pixel art at
//! 960×540, scaled by a whole factor. The tech demo's battle (the Inventor's start against the Devourer's) stays for
//! the tools below.
//!
//!   cargo run -p game --release                       the game, full screen (Esc pause, F11 or Alt+Enter a window;
//!                                                     in battle Space pause, Tab speed, End to the end, C camera)
//!   cargo run -p game --release -- --screens dir      every screen to a PNG (1920×1080), no window needed
//!   cargo run -p game --release -- --shot 120 a.png   frame 120 of the demo battle to a PNG (×2)
//!   cargo run -p game --release -- --strip out.png    a strip of frames across the demo battle, for a look
//!   cargo run -p game --release -- --frames dir 2     every 2nd frame of the demo battle to dir/0000.png…
//!   cargo run -p game --release -- --cues cues.json   the demo battle's sounds with their frames
//!   cargo run -p game --release -- --video sound.json 184 142 | ffmpeg -f rawvideo -pix_fmt rgb24 -s 1920x1080 -r 60 -i - …
//!                                                     battles 184 and 142 as a 60 fps video with a camera (see video.rs)

mod assets;
mod camera;
mod game;
#[cfg(feature = "audio")]
mod audio;
mod gfx;
mod playback;
mod render;
mod screens;
mod shots;
mod text;
mod ui;
mod video;
#[cfg(feature = "window")]
mod window;

use std::path::Path;

pub struct Demo {
    pub assets: assets::Assets,
    pub rec: playback::Record,
    pub sparks: (Vec<playback::Number>, Vec<playback::Effect>),
    pub cues: Vec<playback::Cue>,
    pub view: render::View,
    #[cfg(feature = "audio")]
    pub audio: Option<audio::Audio>,
}

impl Demo {
    pub fn new(seed: u64) -> Result<Self, String> {
        let assets = assets::Assets::load()?;
        let rec = playback::record(seed);
        let sparks = rec.sparks();
        let cues = rec.cues();
        Ok(Demo {
            assets,
            rec,
            sparks,
            cues,
            view: render::View { frame: 0.0, speed: 1, paused: false, hover: None, end: None },
            #[cfg(feature = "audio")]
            audio: None,
        })
    }

    pub fn restart(&mut self, seed: u64) {
        self.load(playback::record(seed));
    }

    /// A battle to play back from its start.
    pub fn load(&mut self, rec: playback::Record) {
        self.rec = rec;
        self.sparks = self.rec.sparks();
        self.cues = self.rec.cues();
        self.view.frame = 0.0;
        self.view.paused = false;
    }

    /// One tick of 1/24 s; the sounds whose moment it passed are played (at most a few a tick, and one of a kind,
    /// so a fast-forwarded swarm stays a sound and not a wall of noise).
    pub fn tick(&mut self) {
        if self.view.paused {
            return;
        }
        let before = self.view.frame as i32;
        self.view.frame = (self.view.frame + self.view.speed as f32).min((self.rec.frames() + 24) as f32);
        let now = self.view.frame as i32;
        #[cfg(feature = "audio")]
        if let Some(a) = &mut self.audio {
            let swarm_alive = self.rec.units.iter().enumerate().any(|(i, u)| !u.machine && self.rec.state_at(i, now).alive);
            a.bed(swarm_alive && now < self.rec.frames());
            let mut played: Vec<&str> = vec![];
            for c in self.cues.iter().filter(|c| c.frame > before && c.frame <= now) {
                if played.contains(&c.name) || played.len() >= 4 {
                    continue;
                }
                a.play(c.name, c.gain, c.x);
                played.push(c.name);
            }
        }
        #[cfg(not(feature = "audio"))]
        let _ = (before, now);
    }

    /// A sound of the interface (a button, a key).
    pub fn ui_sound(&mut self, _name: &str) {
        #[cfg(feature = "audio")]
        if let Some(a) = &mut self.audio {
            a.play(_name, 0.0, 480.0);
        }
    }

    pub fn draw(&self, cv: &mut gfx::Image) {
        render::draw(cv, &self.assets, &self.rec, &self.sparks, &self.view);
    }
}

/// A fatal error, said where the player sees it: a shipped Windows build has no console, so a message box too —
/// not a game that silently does not open.
pub fn fatal(msg: &str) -> ! {
    eprintln!("{msg}");
    message_box(msg);
    std::process::exit(1);
}

#[cfg(windows)]
fn message_box(text: &str) {
    #[link(name = "user32")]
    extern "system" {
        fn MessageBoxW(hwnd: *mut std::ffi::c_void, text: *const u16, caption: *const u16, kind: u32) -> i32;
    }
    let wide = |s: &str| s.encode_utf16().chain(Some(0)).collect::<Vec<u16>>();
    let (t, c) = (wide(text), wide("gam2"));
    // SAFETY: both strings are NUL-terminated UTF-16 that outlive the call; no owner window. 0x10: the error icon.
    unsafe {
        MessageBoxW(std::ptr::null_mut(), t.as_ptr(), c.as_ptr(), 0x10);
    }
}

#[cfg(not(windows))]
fn message_box(_text: &str) {}

fn scaled(cv: &gfx::Image, k: i32) -> gfx::Image {
    let mut out = gfx::Image::new(cv.w * k, cv.h * k);
    for y in 0..out.h {
        for x in 0..out.w {
            out.px[(y * out.w + x) as usize] = cv.get(x / k, y / k);
        }
    }
    out
}

fn main() {
    // a panic in a build without a console: the player gets its text in a box, to send to us
    #[cfg(all(windows, not(debug_assertions)))]
    std::panic::set_hook(Box::new(|info| message_box(&format!("Игра упала с ошибкой:\n\n{info}"))));
    let args: Vec<String> = std::env::args().collect();
    let seed = args.iter().position(|a| a == "--seed").and_then(|i| args.get(i + 1)).and_then(|s| s.parse().ok()).unwrap_or(184);
    let mut demo = match Demo::new(seed) {
        Ok(d) => d,
        Err(e) => fatal(&format!("Не загрузились ресурсы игры (папка assets рядом с game.exe):\n{e}")),
    };
    if let Some(i) = args.iter().position(|a| a == "--shot") {
        let f: f32 = args.get(i + 1).and_then(|s| s.parse().ok()).unwrap_or(0.0);
        let path = args.get(i + 2).cloned().unwrap_or_else(|| "shot.png".into());
        demo.view.frame = if f < 0.0 { (demo.rec.frames() + 24) as f32 } else { f };
        let mut cv = gfx::Image::new(render::W, render::H);
        demo.draw(&mut cv);
        scaled(&cv, 2).save(Path::new(&path)).expect("save");
        println!("{path}: frame {} of {}, rounds {}, winner {:?}", demo.view.frame, demo.rec.frames(), demo.rec.rounds.len(), demo.rec.outcome.winner);
        return;
    }
    if let Some(i) = args.iter().position(|a| a == "--strip") {
        let path = args.get(i + 1).cloned().unwrap_or_else(|| "strip.png".into());
        let total = demo.rec.frames() + 24;
        let picks: Vec<i32> = (0..6).map(|k| k * (total - 1) / 5).collect();
        let mut strip = gfx::Image::new(render::W * 2, render::H * 3);
        for (n, &fr) in picks.iter().enumerate() {
            demo.view.frame = fr as f32;
            let mut cv = gfx::Image::new(render::W, render::H);
            demo.draw(&mut cv);
            strip.blit(&cv, (n as i32 % 2) * render::W, (n as i32 / 2) * render::H, false, 1.0);
        }
        strip.save(Path::new(&path)).expect("save");
        println!("{path}: frames {picks:?}, rounds {}, winner {:?}", demo.rec.rounds.len(), demo.rec.outcome.winner);
        return;
    }
    if let Some(i) = args.iter().position(|a| a == "--cues") {
        // the battle's sounds with their frames (24 fps), as JSON — to mix a soundtrack for a video
        let path = args.get(i + 1).cloned().unwrap_or_else(|| "cues.json".into());
        let v: Vec<serde_json::Value> = demo.cues.iter().map(|c| serde_json::json!({"frame": c.frame, "name": c.name, "gain": c.gain, "x": c.x})).collect();
        std::fs::write(&path, serde_json::to_string(&v).unwrap()).expect("write");
        println!("{path}: {} cues", v.len());
        return;
    }
    if let Some(i) = args.iter().position(|a| a == "--video") {
        let path = args.get(i + 1).cloned().unwrap_or_else(|| "sound.json".into());
        let seeds: Vec<u64> = args[i + 2..].iter().map_while(|s| s.parse().ok()).collect();
        video::run(&mut demo, if seeds.is_empty() { &[184, 142] } else { &seeds }, &path);
        return;
    }
    if let Some(i) = args.iter().position(|a| a == "--screens") {
        // every screen of the game to a PNG (shots.rs)
        let dir = args.get(i + 1).cloned().unwrap_or_else(|| "screens".into());
        shots::run(demo, &dir);
        return;
    }
    if let Some(i) = args.iter().position(|a| a == "--frames") {
        // every `step`-th frame of the whole battle at ×1, for a GIF
        let dir = args.get(i + 1).cloned().unwrap_or_else(|| "frames".into());
        let step: i32 = args.get(i + 2).and_then(|s| s.parse().ok()).unwrap_or(2);
        std::fs::create_dir_all(&dir).expect("dir");
        let total = demo.rec.frames() + 24;
        let mut n = 0;
        for fr in (0..total).step_by(step as usize) {
            demo.view.frame = fr as f32;
            let mut cv = gfx::Image::new(render::W, render::H);
            demo.draw(&mut cv);
            cv.save(&Path::new(&dir).join(format!("{n:04}.png"))).expect("save");
            n += 1;
        }
        println!("{dir}: {n} frames");
        return;
    }
    #[cfg(feature = "window")]
    window::run(demo);
    #[cfg(not(feature = "window"))]
    eprintln!("собрано без окна: --shot N file.png или --strip file.png");
}

#[cfg(test)]
mod tests {
    use crate::{camera, gfx, playback, render};
    use sim::data;

    /// Every start army against every other on a few seeds: the playback, its sounds and numbers, the camera and
    /// the drawing of a spread of frames go through without a panic.
    #[test]
    fn battles_play_back() {
        // GAME_FUZZ=N plays N seeds of every pair and draws every 3rd frame (slow; for a hunt, not for CI)
        let deep: u64 = std::env::var("GAME_FUZZ").ok().and_then(|s| s.parse().ok()).unwrap_or(0);
        let assets = crate::assets::Assets::load().expect("assets");
        let armies = [
            data::start_otets(), data::start_izobretatel(), data::start_manyak(), data::start_zodchiy(),
            data::start_matka(), data::start_razum(), data::start_pozhiratel(), data::start_kukushka(),
        ];
        let fr = camera::Frame::fit(1366, 768);
        for (i, a) in armies.iter().enumerate() {
            for (j, b) in armies.iter().enumerate() {
                for seed in 0..deep.max(2) {
                    let rec = playback::record_of(seed * 1000 + (i * 8 + j) as u64, a, b);
                    let sparks = rec.sparks();
                    let _ = rec.cues();
                    let total = rec.frames() + 24;
                    let mut cv = gfx::Image::new(render::W, render::H);
                    let mut view = render::View { frame: 0.0, speed: 1, paused: false, hover: None, end: None };
                    let n = if deep > 0 { total / 3 } else { 16 };
                    for k in 0..n {
                        let f = k as f32 * total as f32 / n as f32 + 0.37;
                        view.frame = f;
                        render::draw(&mut cv, &assets, &rec, &sparks, &view);
                        let _ = camera::target(&rec, f.min((rec.frames() - 1) as f32), &fr);
                    }
                }
            }
        }
    }
}

#[cfg(test)]
mod flow {
    use crate::game::{Game, Screen};
    use crate::screens::Act;
    use crate::{gfx, render};
    use sim::run::{Class, Reward};

    fn settle(g: &mut Game) {
        for _ in 0..12 {
            g.step_fade(0.05);
        }
    }

    /// If a place is asked for (a module, a mutation): the picker is drawn, the first place taken.
    fn place_first(g: &mut Game) {
        if let Some(tg) = g.targeting.clone() {
            frame(g);
            let to = g.run.as_ref().unwrap().targets(&tg.offer).into_iter().next().expect("a picker with no place");
            g.apply(Act::Place(to));
            assert!(g.targeting.is_none());
            frame(g);
        }
    }

    fn frame(g: &mut Game) {
        let mut field = gfx::Image::new(render::W, render::H);
        let mut hud = gfx::Image::clear(render::W, render::H);
        if g.in_battle() {
            let d = &g.demo;
            render::draw_field(&mut field, &d.assets, &d.rec, &d.sparks, &d.view);
        } else {
            g.draw_bg(&mut field);
        }
        g.draw_ui(&mut hud);
        g.ui.end(0.05);
    }

    /// A boss beaten: the leader's growth among the spoils, two cards; a click on one and the leader has grown, the
    /// battle body with it.
    #[test]
    fn the_leader_grows_after_a_boss() {
        use sim::run::{BattleResult, Kind, Run};
        for (cls, leader) in [(Class::Foundry, 0), (Class::Swarm, 0)] {
            let mut g = Game::new(crate::Demo::new(184).unwrap());
            let mut run = Run::new(cls, leader, 7);
            run.fight = 4;
            let mut boss = run.path[0].clone();
            boss.kind = Kind::Boss;
            let list = run.after_battle(&boss, &BattleResult { won: true, dead: vec![], kills: 5 });
            let i = list.iter().position(|r| matches!(r, Reward::Growth(_))).expect("no growth after a boss");
            let Reward::Growth(keys) = &list[i] else { unreachable!() };
            let keys = keys.clone();
            assert_eq!(keys.len(), 2);
            g.run = Some(run);
            g.screen = Screen::Rewards { list: list.into_iter().map(|r| (r, false)).collect(), pick: None };
            frame(&mut g);
            g.apply(Act::OpenFind(i));
            settle(&mut g);
            frame(&mut g);
            // the first card (left of the middle)
            g.ui.mx = 340;
            g.ui.my = 300;
            frame(&mut g);
            g.ui.mouse_down();
            g.ui.mouse_up();
            frame(&mut g);
            assert!(matches!(g.screen, Screen::Rewards { pick: None, .. }), "{cls:?}: the card did not take");
            let r = g.run.as_ref().unwrap();
            assert_eq!(r.growth, vec![keys[0].clone()]);
            // what each growth changes is checked in sim/tests/run.rs
        }
    }

    /// The workshop at the camp, by the mouse: a module picked up and put into another golem's free cell, then one
    /// melted into another of the same golem; back after the camp's choice made, the choice is not offered again.
    #[test]
    fn the_workshop_by_the_mouse() {
        use crate::game::CampStage;
        use sim::run::{Find, Offer, Run, Target, MELT};
        let mut g = Game::new(crate::Demo::new(184).unwrap());
        let mut run = Run::new(Class::Foundry, 1, 9);
        let module = |k: &str| Offer { key: k.into(), units: vec![], price: 0, find: Find::Module(k.into()) };
        let mech = run.army.iter().position(|m| m.t.name == "Механик").unwrap();
        let gun = run.army.iter().position(|m| m.t.name == "Орудие").unwrap();
        assert!(run.take_find(&module("flail"), Some(&Target::Member(mech))));
        assert!(run.take_find(&module("mortar"), Some(&Target::Member(gun))));
        run.money = 10;
        g.run = Some(run);
        g.screen = Screen::Camp { stage: CampStage::Choose, said: String::new() };
        frame(&mut g);
        g.apply(Act::Workshop);
        for _ in 0..14 {
            frame(&mut g);
        }
        // where a cell is on the screen (as the workshop lays the golems out)
        let cell = |g: &Game, member: usize, j: usize| {
            let r = g.run.as_ref().unwrap();
            let golems: Vec<usize> = (0..r.army.len()).filter(|&i| r.army[i].t.golem || !r.army[i].mods.is_empty()).collect();
            let n = golems.iter().position(|&i| i == member).unwrap() as i32;
            (36 + (n % 2) * 312 + 70 + j as i32 * 42 + 18, 116 + (n / 2) * 80 + 30 + 18)
        };
        let click = |g: &mut Game, (x, y): (i32, i32)| {
            g.ui.mx = x;
            g.ui.my = y;
            frame(g);
            g.ui.mouse_down();
            g.ui.mouse_up();
            frame(g);
        };
        let at = cell(&g, mech, 0);
        click(&mut g, at);
        assert!(matches!(g.screen, Screen::Camp { stage: CampStage::Workshop { held: Some(_) }, .. }), "the module not picked up");
        let at = cell(&g, gun, 1);
        click(&mut g, at);
        let r = g.run.as_ref().unwrap();
        assert!(r.army[mech].mods.is_empty() && r.army[gun].mods.len() == 2, "the flail did not move: {:?}", r.army[gun].mods);
        // the flail (second cell) melted into the mortar (first)
        let (at_flail, at_mortar) = (cell(&g, gun, 1), cell(&g, gun, 0));
        click(&mut g, at_flail);
        click(&mut g, at_mortar);
        let r = g.run.as_ref().unwrap();
        assert_eq!(r.army[gun].mods, vec!["mortar".to_string()]);
        assert_eq!(r.army[gun].level(0), 2);
        assert_eq!(r.money, 10 - MELT);
        // after the camp's choice the workshop's «back» goes to the camp's end, not to the choice again
        g.screen = Screen::Camp { stage: CampStage::Workshop { held: None }, said: "done".into() };
        g.apply(Act::CampBack);
        assert!(matches!(g.screen, Screen::Camp { stage: CampStage::Done, .. }));
    }

    /// The swarm's evolutions from its spoils, by the mouse: the first evolution of the first form bought for its
    /// biomass, a second click on it does nothing.
    #[test]
    fn evolution_by_the_mouse() {
        use sim::run::{Run, EVO_PRICE};
        let mut g = Game::new(crate::Demo::new(184).unwrap());
        let mut run = Run::new(Class::Swarm, 0, 4);
        run.money = 50;
        let form = run.forms().into_iter().find(|f| !Run::evolutions(f).is_empty()).expect("a form with evolutions");
        let key = Run::evolutions(&form)[0].key.clone();
        g.run = Some(run);
        g.screen = Screen::Rewards { list: vec![], pick: None };
        frame(&mut g);
        g.apply(Act::Evolution);
        for _ in 0..14 {
            frame(&mut g);
        }
        // the first tile of the first row, as the overlay lays them out
        for _ in 0..2 {
            g.ui.mx = 40 + 200 + 106;
            g.ui.my = 24 + 70 + 26;
            frame(&mut g);
            g.ui.mouse_down();
            g.ui.mouse_up();
            frame(&mut g);
        }
        let r = g.run.as_ref().unwrap();
        assert!(r.breeds.contains(&(form.clone(), key.clone())), "{form}: {key} not bought");
        assert_eq!(r.money, 50 - EVO_PRICE, "bought twice, or not paid");
        g.apply(Act::CloseOverlay);
        assert!(g.overlays.is_empty());
    }

    /// A monkey at the keyboard and the mouse: random clicks all over the screen, random keys, battles wound to their
    /// end now and then — thousands of frames from the menu on, every screen drawn. Nothing may panic, and the game
    /// must keep moving (`GAME_MONKEY=N` runs N monkeys, each a few thousand frames).
    #[test]
    #[ignore]
    fn monkey() {
        use crate::ui::Key;
        let tmp = std::env::temp_dir().join(format!("gam2-monkey-{}", std::process::id()));
        std::env::set_var("APPDATA", &tmp);
        let runs: u64 = std::env::var("GAME_MONKEY").ok().and_then(|s| s.parse().ok()).unwrap_or(2);
        let keys = [Key::Enter, Key::Space, Key::Tab, Key::End, Key::R, Key::C, Key::Digit(1), Key::Digit(2), Key::Digit(3), Key::Digit(4)];
        for seed in 0..runs {
            let mut x = seed.wrapping_mul(0x9E37_79B9_7F4A_7C15) | 1;
            let mut rnd = move |n: u64| {
                x ^= x << 13;
                x ^= x >> 7;
                x ^= x << 17;
                x % n.max(1)
            };
            let mut g = Game::new(crate::Demo::new(184).unwrap());
            let mut screens = std::collections::BTreeMap::new();
            let mut last_run = None;
            for _ in 0..3000 {
                if let Some(r) = &g.run {
                    if last_run != Some(r.seed) {
                        last_run = Some(r.seed);
                        eprintln!("monkey {seed}: a run of {:?}, leader {}, seed {}", r.class, r.leader, r.seed);
                    }
                }
                *screens.entry(format!("{:?}", std::mem::discriminant(&g.screen))).or_insert(0) += 1;
                match rnd(100) {
                    0..=69 => {
                        g.ui.mx = rnd(960) as i32;
                        g.ui.my = rnd(540) as i32;
                        frame(&mut g);
                        g.ui.mouse_down();
                        g.ui.mouse_up();
                    }
                    70..=79 => g.key(keys[rnd(keys.len() as u64) as usize]),
                    80..=83 => g.key(Key::Esc),
                    _ => {
                        g.ui.mx = rnd(960) as i32;
                        g.ui.my = rnd(540) as i32;
                    }
                }
                // a battle runs out now and then (in the window it plays on its own)
                if g.in_battle() && rnd(8) == 0 {
                    g.demo.view.frame = (g.demo.rec.frames() + 24) as f32;
                }
                g.step_fade(0.05);
                frame(&mut g);
                if g.quit {
                    g.quit = false;
                }
            }
            eprintln!("monkey {seed}: {} screens, {:?}", screens.len(), screens);
        }
        let _ = std::fs::remove_dir_all(&tmp);
    }

    /// A random player: whole runs of all eight leaders to their end, every screen's choice made at random by its own
    /// acts — roads, spoils, cards, places, growth, the trader, events, the camp, the workshop's cells, evolutions —
    /// each screen drawn after each act, the run checked after each step (`GAME_PLAYER=N` seeds a leader, 2 by default).
    #[test]
    #[ignore]
    fn random_player() {
        use crate::game::{CampStage, Overlay};
        use sim::run::{Run, MAX_LEVEL};
        let tmp = std::env::temp_dir().join(format!("gam2-player-{}", std::process::id()));
        std::env::set_var("APPDATA", &tmp);
        let seeds: u64 = std::env::var("GAME_PLAYER").ok().and_then(|s| s.parse().ok()).unwrap_or(2);
        let check = |g: &Game, what: &str| {
            let r = g.run.as_ref().unwrap();
            assert!(r.money >= 0, "{what}: money {}", r.money);
            assert!(r.army.iter().any(|m| r.is_leader(m)), "{what}: no leader");
            for m in &r.army {
                assert!(m.mods.len() <= r.cells(m), "{what}: {} has {} modules in {} cells", m.t.name, m.mods.len(), r.cells(m));
                assert!((0..m.mods.len()).all(|j| (1..=MAX_LEVEL).contains(&m.level(j))), "{what}: a level out of I–III");
                let mut k = m.mods.clone();
                k.sort();
                k.dedup();
                assert_eq!(k.len(), m.mods.len(), "{what}: a module twice on {}", m.t.name);
            }
        };
        for cls in [Class::Foundry, Class::Swarm] {
            for leader in 0..4 {
                for seed in 0..seeds {
                    let mut x = (seed + 1) * 7919 + leader as u64 * 104729 + cls as u64;
                    let mut rnd = move |n: usize| {
                        x ^= x << 13;
                        x ^= x >> 7;
                        x ^= x << 17;
                        (x % n.max(1) as u64) as usize
                    };
                    let mut g = Game::new(crate::Demo::new(184).unwrap());
                    g.run = Some(Run::new(cls, leader, 1000 + seed));
                    g.screen = Screen::Fork;
                    let mut steps = 0;
                    loop {
                        steps += 1;
                        assert!(steps < 300, "{cls:?} {leader} {seed}: a run that does not end");
                        frame(&mut g);
                        let what = format!("{cls:?} leader {leader} seed {seed} step {steps}");
                        match &g.screen {
                            Screen::Fork => {
                                let n = g.run.as_ref().unwrap().path.len();
                                g.apply(Act::Road(rnd(n)));
                            }
                            Screen::Battle { .. } => {
                                g.demo.view.frame = (g.demo.rec.frames() + 24) as f32;
                                frame(&mut g);
                                g.battle_done();
                            }
                            Screen::Rewards { list, .. } => {
                                let list: Vec<Reward> = list.iter().map(|(r, _)| r.clone()).collect();
                                for (i, r) in list.iter().enumerate() {
                                    match r {
                                        Reward::Find(o) => {
                                            g.apply(Act::OpenFind(i));
                                            frame(&mut g);
                                            let pick = rnd(o.len() + 1);
                                            g.apply(Act::Pick(i, (pick < o.len()).then_some(pick)));
                                        }
                                        Reward::Growth(k) => {
                                            g.apply(Act::OpenFind(i));
                                            frame(&mut g);
                                            g.apply(Act::Pick(i, Some(rnd(k.len()))));
                                        }
                                        _ if rnd(4) > 0 => g.apply(Act::Take(i)),
                                        _ => {}
                                    }
                                    frame(&mut g);
                                    // a module or a mutation: a place at random, or given up
                                    if let Some(tg) = g.targeting.clone() {
                                        let to = g.run.as_ref().unwrap().targets(&tg.offer);
                                        g.apply(if to.is_empty() || rnd(5) == 0 { Act::CancelTarget } else { Act::Place(to[rnd(to.len())].clone()) });
                                        frame(&mut g);
                                    }
                                }
                                if cls == Class::Swarm && rnd(2) == 0 {
                                    evolve(&mut g, &mut rnd);
                                }
                                g.apply(Act::LeaveRewards);
                            }
                            Screen::Shop(shop) => {
                                let (no, na) = (shop.offers.len(), shop.artifacts.len());
                                for _ in 0..3 {
                                    match rnd(3) {
                                        0 => g.apply(Act::BuyOffer(rnd(no))),
                                        1 => g.apply(Act::BuyArtifact(rnd(na))),
                                        _ => g.apply(Act::BuyService),
                                    }
                                    frame(&mut g);
                                    if let Some(tg) = g.targeting.clone() {
                                        let to = g.run.as_ref().unwrap().targets(&tg.offer);
                                        g.apply(if to.is_empty() { Act::CancelTarget } else { Act::Place(to[rnd(to.len())].clone()) });
                                        frame(&mut g);
                                    }
                                }
                                g.apply(Act::LeaveStop);
                            }
                            Screen::Event { id, .. } => {
                                let can: Vec<usize> = (0..3).filter(|&o| g.run.as_ref().unwrap().event_can(*id, o)).collect();
                                g.apply(Act::EventChoose(can[rnd(can.len())]));
                                frame(&mut g);
                                g.apply(Act::LeaveStop);
                            }
                            Screen::Camp { .. } => {
                                if cls == Class::Foundry {
                                    g.apply(Act::Workshop);
                                    frame(&mut g);
                                    for _ in 0..12 {
                                        let r = g.run.as_ref().unwrap();
                                        let m = rnd(r.army.len());
                                        let j = rnd(r.cells(&r.army[m]) + 1);
                                        g.apply(Act::Socket(m, j));
                                        frame(&mut g);
                                        check(&g, &format!("{what} workshop"));
                                    }
                                    g.apply(Act::CampBack);
                                    assert!(matches!(g.screen, Screen::Camp { stage: CampStage::Choose, .. }));
                                } else if rnd(2) == 0 {
                                    evolve(&mut g, &mut rnd);
                                }
                                frame(&mut g);
                                if rnd(2) == 0 && (cls == Class::Swarm || g.run.as_ref().unwrap().broken() > 0) {
                                    g.apply(Act::CampRest);
                                } else {
                                    g.apply(Act::CampUp);
                                    frame(&mut g);
                                    let n = g.run.as_ref().unwrap().army.len();
                                    g.apply(Act::CampPick(rnd(n)));
                                }
                                frame(&mut g);
                                g.apply(Act::LeaveStop);
                            }
                            Screen::End { .. } => break,
                            _ => panic!("{what}: an unexpected screen"),
                        }
                        settle(&mut g);
                        check(&g, &what);
                    }
                    let r = g.run.as_ref().unwrap();
                    eprintln!("{cls:?} leader {leader} seed {seed}: {} after {} battles, army {}, growth {:?}", if r.over == Some(true) { "won" } else { "lost" }, r.stats.won, r.army.len(), r.growth);
                    assert!(g.overlays.is_empty() || matches!(g.overlays[..], [Overlay::Evolution]), "overlays left: {}", g.overlays.len());
                }
            }
        }
        let _ = std::fs::remove_dir_all(&tmp);

        // the swarm's evolutions: the overlay opened, an evolution clicked at random (a form, one of its own), closed
        fn evolve(g: &mut Game, rnd: &mut impl FnMut(usize) -> usize) {
            g.apply(Act::Evolution);
            frame(g);
            let r = g.run.as_ref().unwrap();
            let forms: Vec<String> = r.forms().into_iter().filter(|f| !Run::evolutions(f).is_empty()).collect();
            if !forms.is_empty() {
                let f = forms[rnd(forms.len())].clone();
                let e = Run::evolutions(&f);
                let k = e[rnd(e.len())].key.clone();
                g.apply(Act::Evolve(f, k));
                frame(g);
            }
            g.apply(Act::CloseOverlay);
            frame(g);
        }
    }

    /// The battle's camera by the player: the wheel and + / − step its level (down to the whole field, kept in the
    /// settings, a note says it), C turns it off and back on at the same level; each level comes no closer than its
    /// own limit, the farthest shows the whole field.
    #[test]
    fn the_camera_zooms_out() {
        use crate::camera::{self, Frame};
        use crate::game::ZOOMS;
        use crate::ui::Key;
        let tmp = std::env::temp_dir().join(format!("gam2-zoom-{}", std::process::id()));
        std::env::set_var("APPDATA", &tmp);
        let mut g = Game::new(crate::Demo::new(184).unwrap());
        g.run = Some(sim::run::Run::new(Class::Foundry, 1, 3));
        g.screen = Screen::Fork;
        g.apply(Act::Road(0));
        settle(&mut g);
        frame(&mut g);
        assert!(g.in_battle());
        g.settings.set_cam_level(2);
        // two notches of the wheel toward the player: farther twice
        g.ui.wheel = -2;
        frame(&mut g);
        assert_eq!(g.settings.cam_level(), 0, "two notches farther from «обычно» is the whole field");
        assert!(g.cam_note.is_some());
        // no farther than the whole field
        g.key(Key::ZoomOut);
        frame(&mut g);
        assert_eq!(g.settings.cam_level(), 0);
        g.key(Key::ZoomIn);
        frame(&mut g);
        g.key(Key::ZoomIn);
        frame(&mut g);
        g.key(Key::ZoomIn);
        frame(&mut g);
        assert_eq!(g.settings.cam_level(), 3);
        // C: off, and on again at the same level
        g.key(Key::C);
        frame(&mut g);
        assert_eq!(g.settings.cam_level(), 0);
        g.key(Key::C);
        frame(&mut g);
        assert_eq!(g.settings.cam_level(), 3);
        // kept for the next game
        assert_eq!(crate::game::Settings::load().cam_level(), 3);
        // under the pause the wheel does nothing
        g.overlays.push(crate::game::Overlay::Pause);
        g.ui.wheel = 1;
        frame(&mut g);
        assert_eq!(g.settings.cam_level(), 3);
        g.overlays.clear();
        // each level no closer than its limit, the farthest the whole field
        let rec = &g.demo.rec;
        let fr = Frame::fit(1920, 1080);
        for f in (0..rec.frames()).step_by(7) {
            assert_eq!(camera::at_level(rec, f as f32, &fr, 0, &ZOOMS).z, fr.zmin);
            for l in 1..=4u8 {
                let c = camera::at_level(rec, f as f32, &fr, l, &ZOOMS);
                assert!(c.z >= fr.zmin - 1e-3 && c.z <= fr.zmin * ZOOMS[l as usize] + 1e-3, "level {l}: z {}", c.z);
            }
        }
        let _ = std::fs::remove_dir_all(&tmp);
    }

    /// The army as in the strategy games of old: every body in the list (a swarm's kind a row, how many of it), a
    /// click picks one and shows its sheet, the wheel goes down a long list and down a long sheet; every trait and
    /// ability has its words.
    #[test]
    fn every_body_of_the_army_can_be_seen() {
        use crate::screens::{ability_line, army_rows, trait_words, ARMY_ROWS};
        use sim::model::{Ability, Dmg, Trait};
        use sim::run::{Find, Offer, Run};
        // the words: none left as its key
        let traits = [
            Trait::Zaslon, Trait::Probivnoy, Trait::Caster, Trait::Pitanie, Trait::Zamykanie, Trait::ZharGorna, Trait::Navodka,
            Trait::Naladka, Trait::NoAttack, Trait::FireResist75, Trait::Mindless, Trait::PoisonImmune, Trait::Unstoppable,
            Trait::Fear { die: 8, radius: 2 }, Trait::Leader, Trait::Staya, Trait::Devour, Trait::Stroy, Trait::Flyer,
            Trait::Venom { die: 4 }, Trait::BurstAcid { die: 4 }, Trait::Charge, Trait::Thorns { die: 3 }, Trait::CurlUp, Trait::Leap,
            Trait::TwinBlades, Trait::Glow, Trait::HiveMind, Trait::Grows, Trait::Infects, Trait::Changeling, Trait::Viviparous,
            Trait::Spitter,
        ];
        for tr in &traits {
            let (n, l) = trait_words(tr);
            assert!(!n.starts_with("tr.") && !l.starts_with("tr.") && !l.contains('{'), "{tr:?}: «{n}» «{l}»");
        }
        let abilities = [
            Ability::Volley { every: 3, die: 6, bonus: 1, dmg: Dmg::Fire }, Ability::Repair { every: 2, amount: 3 },
            Ability::Bolt { every: 2, die: 6, bonus: 0, dmg: Dmg::Shock, range: 1 }, Ability::Flail, Ability::Plates(3), Ability::PointBlank,
            Ability::Intercept, Ability::Flash { every: 3 }, Ability::Spit { every: 3, die: 4 }, Ability::Brood { every: 3, n: 2 },
            Ability::Mark { every: 2 }, Ability::Overload { every: 2 }, Ability::Fireball { every: 3, die: 4, bonus: 0, range: 5 },
            Ability::Quake { every: 3, die: 8, bonus: 2, radius: 1 }, Ability::Augment, Ability::Tinker { every: 3 },
        ];
        for ab in &abilities {
            let l = ability_line(ab);
            assert!(!l.starts_with("ab.") && !l.contains('{'), "{ab:?}: «{l}»");
        }
        // a swarm of many kinds: more rows than the list shows
        let tmp = std::env::temp_dir().join(format!("gam2-army-{}", std::process::id()));
        std::env::set_var("APPDATA", &tmp);
        let mut g = Game::new(crate::Demo::new(184).unwrap());
        let mut run = Run::new(Class::Swarm, 0, 3);
        let bodies = sim::data::FORMS.iter().flat_map(|f| [sim::data::swarm(sim::data::Caste::Worker, *f), sim::data::swarm(sim::data::Caste::Soldier, *f)]).collect();
        run.recruit(&Offer { key: "x".into(), units: bodies, price: 0, find: Find::Units });
        let rows = army_rows(&run);
        assert!(rows.len() > ARMY_ROWS);
        assert_eq!(rows.iter().map(|r| r.1).sum::<usize>(), run.army.len(), "a body missing from the list");
        g.run = Some(run);
        g.screen = Screen::Fork;
        g.apply(Act::Army);
        for _ in 0..12 {
            frame(&mut g);
        }
        // the second row clicked: its sheet
        g.ui.mx = 24 + 18 + 100;
        g.ui.my = 24 + 54 + 40 + 18;
        frame(&mut g);
        g.ui.mouse_down();
        g.ui.mouse_up();
        frame(&mut g);
        assert_eq!(g.army_sel, 1);
        // the wheel over the list: down to its end and no farther
        for _ in 0..40 {
            g.ui.wheel = -1;
            frame(&mut g);
        }
        assert_eq!(g.army_top, rows.len() - ARMY_ROWS);
        // the wheel over the sheet: down its lines, no farther than its last
        let lines = crate::screens::army_items(g.run.as_ref().unwrap())[1].lines().len();
        g.ui.mx = 600;
        g.ui.my = 300;
        for _ in 0..20 {
            g.ui.wheel = -1;
            frame(&mut g);
        }
        assert_eq!(g.sheet_top, lines.saturating_sub(1));
        let _ = std::fs::remove_dir_all(&tmp);
    }

    /// Every body can be looked at closer: a right click on a road shows its enemy, on a leader — the leader and its
    /// army, on a recruit — the recruit; a click on a fighter in battle — every fighter with how it stands now (the
    /// battle waits under it); «Сдаться» and «В меню» ask first.
    #[test]
    fn everything_can_be_looked_at() {
        use crate::game::{Ask, Overlay};
        use sim::run::Run;
        let tmp = std::env::temp_dir().join(format!("gam2-look-{}", std::process::id()));
        std::env::set_var("APPDATA", &tmp);
        let mut g = Game::new(crate::Demo::new(184).unwrap());
        let rclick = |g: &mut Game, x: i32, y: i32| {
            g.ui.mx = x;
            g.ui.my = y;
            frame(g);
            g.ui.rmouse_down();
            g.ui.rmouse_up();
            frame(g);
        };
        // a leader and its army
        g.screen = Screen::Leaders { class: Class::Foundry, chosen: 0 };
        for _ in 0..10 {
            frame(&mut g);
        }
        rclick(&mut g, 14 + 236 + 100, 250);
        assert_eq!(g.overlays.last(), Some(&Overlay::Inspect), "no leader's sheet");
        let (title, items) = g.inspect.clone().unwrap();
        assert_eq!(title, crate::text::t("leader.0.1.name"));
        assert!(items[0].t.has(sim::model::Trait::Leader), "the leader not first");
        g.apply(Act::CloseOverlay);
        // a road's enemy
        let run = Run::new(Class::Foundry, 1, 3);
        let first = run.path.iter().position(|n| n.kind.is_battle()).unwrap();
        let enemy_n = run.path[first].enemy.len();
        g.run = Some(run);
        g.screen = Screen::Fork;
        for _ in 0..12 {
            frame(&mut g);
        }
        let n = g.run.as_ref().unwrap().path.len() as i32;
        let (cw, gap) = (262, 26);
        let x0 = (960 - n * cw - (n - 1) * gap) / 2;
        rclick(&mut g, x0 + first as i32 * (cw + gap) + cw / 2, 300);
        assert_eq!(g.overlays.last(), Some(&Overlay::Inspect), "no enemy's sheet");
        let (_, items) = g.inspect.clone().unwrap();
        assert!(items.iter().all(|i| i.foe));
        assert_eq!(items.iter().map(|i| i.n).sum::<usize>(), enemy_n);
        g.apply(Act::CloseOverlay);
        // a fighter in battle
        g.apply(Act::Road(first));
        settle(&mut g);
        frame(&mut g);
        assert!(g.in_battle());
        g.demo.view.frame = 40.0;
        let s = g.demo.rec.shown(40.0).into_iter().find(|s| s.pose != crate::playback::Pose::Dead).unwrap();
        g.field_mouse = Some((s.x, s.y - 10.0));
        g.ui.mx = 480;
        g.ui.my = 300;
        frame(&mut g);
        g.ui.mouse_down();
        g.ui.mouse_up();
        frame(&mut g);
        assert_eq!(g.overlays.last(), Some(&Overlay::Inspect), "no fighter's sheet");
        let (_, items) = g.inspect.clone().unwrap();
        let it = &items[g.army_sel];
        assert_eq!(it.t.name, g.demo.rec.units[s.id].name, "another fighter picked");
        assert!(it.state.is_some(), "no state in battle");
        // the battle waits
        let f = g.demo.view.frame;
        g.tick();
        assert_eq!(g.demo.view.frame, f);
        g.apply(Act::CloseOverlay);
        // to the menu asks first
        g.apply(Act::Ask(Ask::ToMenu));
        assert!(matches!(g.overlays.last(), Some(Overlay::Confirm(Ask::ToMenu))));
        frame(&mut g);
        g.key(crate::ui::Key::Enter);
        frame(&mut g);
        settle(&mut g);
        assert!(matches!(g.screen, Screen::Menu), "«yes» did not go to the menu");
        let _ = std::fs::remove_dir_all(&tmp);
    }

    /// A run of each class walked through every kind of screen by the screens' own acts — roads, battles, spoils,
    /// the find, the trader, events, the camp — each screen drawn on the way, to its end.
    #[test]
    fn a_run_through_the_screens() {
        let tmp = std::env::temp_dir().join(format!("gam2-test-{}", std::process::id()));
        std::env::set_var("APPDATA", &tmp);
        for (cls, leader) in [(Class::Foundry, 1), (Class::Swarm, 2)] {
            let mut g = Game::new(crate::Demo::new(184).unwrap());
            frame(&mut g);
            g.apply(Act::StartRun(cls, leader));
            settle(&mut g);
            let mut seen = std::collections::BTreeSet::new();
            for step in 0..200 {
                frame(&mut g);
                let name = match &g.screen {
                    Screen::Fork => "fork",
                    Screen::Battle { .. } => "battle",
                    Screen::Rewards { .. } => "rewards",
                    Screen::Shop(_) => "shop",
                    Screen::Event { .. } => "event",
                    Screen::Camp { .. } => "camp",
                    Screen::End { .. } => "end",
                    _ => "other",
                };
                seen.insert(name);
                match &g.screen {
                    Screen::Fork => {
                        let path = &g.run.as_ref().unwrap().path;
                        // a stop when there is one (every other time), else the first battle
                        let i = path.iter().position(|n| !n.kind.is_battle()).filter(|_| step % 2 == 0).unwrap_or(0);
                        g.apply(Act::Road(i));
                    }
                    Screen::Battle { .. } => {
                        g.demo.view.frame = (g.demo.rec.frames() + 24) as f32;
                        frame(&mut g);
                        g.battle_done();
                    }
                    Screen::Rewards { list, .. } => {
                        let list: Vec<Reward> = list.iter().map(|(r, _)| r.clone()).collect();
                        for (i, r) in list.iter().enumerate() {
                            match r {
                                Reward::Find(_) => {
                                    g.apply(Act::OpenFind(i));
                                    frame(&mut g);
                                    // a click on a card under the pause does not reach it
                                    g.overlays.push(crate::game::Overlay::Pause);
                                    g.ui.mx = 226;
                                    g.ui.my = 276;
                                    frame(&mut g);
                                    g.ui.mouse_down();
                                    g.ui.mouse_up();
                                    frame(&mut g);
                                    assert!(matches!(g.screen, Screen::Rewards { pick: Some(_), .. }), "a click went through the pause");
                                    g.overlays.clear();
                                    // and with the pause gone, the same click takes the card
                                    frame(&mut g);
                                    g.ui.mouse_down();
                                    g.ui.mouse_up();
                                    frame(&mut g);
                                    assert!(matches!(g.screen, Screen::Rewards { pick: None, .. }), "the click on the card did not take it");
                                    g.ui.mx = -1;
                                    // a module or a mutation asks where it goes: the first place offered
                                    place_first(&mut g);
                                }
                                Reward::Growth(keys) => {
                                    // the leader's growth: the second card, by a click
                                    g.apply(Act::OpenFind(i));
                                    frame(&mut g);
                                    g.ui.mx = 600;
                                    g.ui.my = 300;
                                    frame(&mut g);
                                    g.ui.mouse_down();
                                    g.ui.mouse_up();
                                    frame(&mut g);
                                    g.ui.mx = -1;
                                    assert!(matches!(g.screen, Screen::Rewards { pick: None, .. }), "the growth card did not take");
                                    assert!(g.run.as_ref().unwrap().growth.contains(&keys[1]), "the leader did not grow");
                                    seen.insert("growth");
                                }
                                _ => g.apply(Act::Take(i)),
                            }
                        }
                        g.apply(Act::LeaveRewards);
                    }
                    Screen::Shop(_) => {
                        // a part of the trader's (the third good) goes somewhere too
                        g.run.as_mut().unwrap().money += 40;
                        g.apply(Act::BuyOffer(2));
                        place_first(&mut g);
                        g.apply(Act::BuyOffer(0));
                        g.apply(Act::BuyArtifact(0));
                        g.apply(Act::BuyService);
                        frame(&mut g);
                        g.apply(Act::LeaveStop);
                    }
                    Screen::Event { id, .. } => {
                        let o = (0..3).find(|&o| g.run.as_ref().unwrap().event_can(*id, o)).unwrap();
                        g.apply(Act::EventChoose(o));
                        frame(&mut g);
                        g.apply(Act::LeaveStop);
                    }
                    Screen::Camp { .. } => {
                        g.apply(Act::CampUp);
                        frame(&mut g);
                        g.apply(Act::CampPick(0));
                        frame(&mut g);
                        g.apply(Act::LeaveStop);
                    }
                    Screen::End { .. } => break,
                    _ => panic!("an unexpected screen"),
                }
                settle(&mut g);
            }
            assert!(seen.contains("end"), "{cls:?}: the run did not end: {seen:?}");
            let r = g.run.as_ref().unwrap();
            eprintln!("  modules {}, breeds {}", r.army.iter().map(|m| m.mods.len()).sum::<usize>(), r.breeds.len());
            // a run left for the menu and taken up again, then given up
            g.apply(Act::StartRun(cls, leader));
            settle(&mut g);
            assert!(matches!(g.screen, Screen::Fork) && g.saved.is_some(), "a new run is saved at its first fork");
            let fight = g.run.as_ref().unwrap().next_fight();
            g.apply(Act::ToMenu);
            settle(&mut g);
            assert!(matches!(g.screen, Screen::Menu) && g.run.is_none());
            frame(&mut g);
            g.apply(Act::Continue);
            settle(&mut g);
            assert!(matches!(g.screen, Screen::Fork), "«Продолжить» brings the fork back");
            assert_eq!(g.run.as_ref().unwrap().next_fight(), fight);
            frame(&mut g);
            // «Сдаться» asks first: no, then yes
            g.apply(Act::Ask(crate::game::Ask::Surrender));
            assert!(matches!(g.overlays.last(), Some(crate::game::Overlay::Confirm(_))), "giving up without asking");
            g.apply(Act::CloseOverlay);
            assert!(g.run.as_ref().unwrap().over.is_none(), "«no» gave the run up");
            g.apply(Act::Ask(crate::game::Ask::Surrender));
            g.apply(Act::Confirmed(crate::game::Ask::Surrender));
            settle(&mut g);
            assert!(matches!(g.screen, Screen::End { victory: false }) && g.saved.is_none(), "giving up ends the run and forgets it");
            frame(&mut g);
            // a run may be lost in its first battle (the seed is the clock's): then no spoils were seen
            assert!(seen.contains("battle"), "{seen:?}");
            eprintln!("{cls:?}: {seen:?}, battles won {}", g.run.as_ref().map(|r| r.stats.won).unwrap_or(0));
        }
        let _ = std::fs::remove_dir_all(&tmp);
    }
}

#[cfg(test)]
mod finds {
    /// Every find of finds.ron has its icon in the atlases and its words.
    #[test]
    fn every_find_has_an_icon_and_words() {
        let a = crate::assets::Assets::load().unwrap();
        let f = sim::data::finds();
        let keys = f.modules.iter().map(|m| ("module", &m.key)).chain(f.mutations.iter().map(|m| ("swarm", &m.key)));
        for (atlas, k) in keys {
            assert!(a.icons.contains_key(&format!("{atlas}/{k}")), "no icon {atlas}/{k}");
            for w in [format!("find.{k}"), format!("find.{k}.l")] {
                assert_ne!(crate::text::t(&w), w, "no words for {w}");
            }
        }
    }
}

#[cfg(test)]
mod bench {
    /// What a frame costs: the field, the interface, the camera's composing at 1080p, 1440p and 4K
    /// (`cargo test --release -p game frame_cost -- --ignored --nocapture`); COMPOSE_DUMP=dir also writes the composed
    /// pictures, to compare a change of compose against.
    #[test]
    #[ignore]
    fn frame_cost() {
        use crate::{camera, gfx, render};
        use std::time::Instant;
        let demo = crate::Demo::new(184).unwrap();
        let mut field = gfx::Image::new(render::W, render::H);
        let (mut tf, mut th) = (0.0, 0.0);
        for k in 0..30 {
            let v = render::View { frame: 300.0 + k as f32, speed: 1, paused: false, hover: None, end: None };
            let t = Instant::now();
            render::draw_field(&mut field, &demo.assets, &demo.rec, &demo.sparks, &v);
            tf += t.elapsed().as_secs_f64();
            let t = Instant::now();
            let mut hud = gfx::Image::clear(render::W, render::H);
            render::draw_hud(&mut hud, &demo.assets, &demo.rec, &v);
            th += t.elapsed().as_secs_f64();
        }
        println!("field {:.1} ms, hud {:.1} ms", tf * 1000.0 / 30.0, th * 1000.0 / 30.0);
        let hud = gfx::Image::clear(render::W, render::H);
        for (w, h) in [(1920, 1080), (2560, 1440), (3840, 2160)] {
            let fr = camera::Frame::fit(w, h);
            let mut buf = vec![0u8; (w * h * 4) as usize];
            let cam = camera::target(&demo.rec, 300.0, &fr);
            let t = Instant::now();
            for _ in 0..30 {
                camera::compose(&field, &hud, cam, 1.0, &mut buf, &fr, 4);
            }
            println!("compose {w}x{h}: {:.1} ms", t.elapsed().as_secs_f64() * 1000.0 / 30.0);
        }
        // the composed pictures, to compare a rewrite of compose against (COMPOSE_DUMP=dir)
        if let Some(dir) = std::env::var_os("COMPOSE_DUMP") {
            let mut hud = gfx::Image::clear(render::W, render::H);
            let v = render::View { frame: 300.0, speed: 1, paused: false, hover: None, end: None };
            render::draw_hud(&mut hud, &demo.assets, &demo.rec, &v);
            let mut n = 0;
            for (w, h) in [(1920, 1080), (2560, 1440), (1366, 768), (1000, 700)] {
                let fr = camera::Frame::fit(w, h);
                for f in [0.0, 150.0, 300.0, 333.3] {
                    let mut cam = camera::target(&demo.rec, f, &fr);
                    cam.cx += 0.37;
                    for (ch, light) in [(4usize, 1.0f32), (3, 0.6)] {
                        let mut buf = vec![0u8; (w * h) as usize * ch];
                        camera::compose(&field, &hud, cam, light, &mut buf, &fr, ch);
                        std::fs::write(std::path::Path::new(&dir).join(format!("{n}.raw")), &buf).unwrap();
                        n += 1;
                    }
                }
            }
        }
    }
}
