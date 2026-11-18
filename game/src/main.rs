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
                                    g.apply(Act::Pick(i, Some(0)));
                                }
                                _ => g.apply(Act::Take(i)),
                            }
                        }
                        g.apply(Act::LeaveRewards);
                    }
                    Screen::Shop(_) => {
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
            // a run may be lost in its first battle (the seed is the clock's): then no spoils were seen
            assert!(seen.contains("battle"), "{seen:?}");
            eprintln!("{cls:?}: {seen:?}, battles won {}", g.run.as_ref().map(|r| r.stats.won).unwrap_or(0));
        }
        let _ = std::fs::remove_dir_all(&tmp);
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
