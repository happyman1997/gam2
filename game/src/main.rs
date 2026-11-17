// A shipped Windows build opens as a game, without a console window beside it (a debug build keeps its console).
#![cfg_attr(all(windows, not(debug_assertions)), windows_subsystem = "windows")]
//! gam2, the tech demo: one battle — the Inventor's start against the Devourer's — run by the simulation and played
//! back with the game's pixel art at 960×540, scaled by a whole factor.
//!
//!   cargo run -p game --release                       a window (Space pause, Tab speed, End to the end, R new battle)
//!   cargo run -p game --release -- --shot 120 a.png   frame 120 to a PNG (×2), no window needed
//!   cargo run -p game --release -- --strip out.png    a strip of frames across the battle, for a look
//!   cargo run -p game --release -- --frames dir 2     every 2nd frame of the battle to dir/0000.png…
//!   cargo run -p game --release -- --cues cues.json   the battle's sounds with their frames
//!   cargo run -p game --release -- --video sound.json 184 142 | ffmpeg -f rawvideo -pix_fmt rgb24 -s 1920x1080 -r 60 -i - …
//!                                                     battles 184 and 142 as a 60 fps video with a camera (see video.rs)

mod assets;
mod camera;
#[cfg(feature = "audio")]
mod audio;
mod gfx;
mod playback;
mod render;
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
            view: render::View { frame: 0.0, speed: 1, paused: false, hover: None },
            #[cfg(feature = "audio")]
            audio: None,
        })
    }

    pub fn restart(&mut self, seed: u64) {
        self.rec = playback::record(seed);
        self.sparks = self.rec.sparks();
        self.cues = self.rec.cues();
        self.view.frame = 0.0;
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
            let swarm_alive = self.rec.units.iter().enumerate().any(|(i, u)| u.side == 1 && self.rec.state_at(i, now).alive);
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
    let args: Vec<String> = std::env::args().collect();
    let seed = args.iter().position(|a| a == "--seed").and_then(|i| args.get(i + 1)).and_then(|s| s.parse().ok()).unwrap_or(184);
    let mut demo = match Demo::new(seed) {
        Ok(d) => d,
        Err(e) => {
            eprintln!("не загрузились ресурсы: {e}");
            std::process::exit(1);
        }
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
    window::run(demo, seed);
    #[cfg(not(feature = "window"))]
    eprintln!("собрано без окна: --shot N file.png или --strip file.png");
}
