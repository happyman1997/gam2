//! A video of the demo: battles one after another at 60 frames a second, the field zoomed on the fight by a camera
//! (2× while the armies stand apart, up to 3× on the clash; sharp pixels at any zoom), the interface over it at 2×.
//! Raw RGB frames go to stdout for ffmpeg; the sounds with their times go to a JSON file, to mix the soundtrack.

use crate::camera::{self, Frame};
use crate::gfx::Image;
use crate::render::{self, FH, FW, H, W};
use crate::Demo;
use std::io::Write;

pub const OW: i32 = W * 2;
pub const OH: i32 = H * 2;
const FPS: f32 = 60.0;
const HOLD: f32 = 96.0; // game frames the end plate stays before the next battle (the jingle plays out)
const FADE: f32 = 12.0; // game frames of the fade from and to black around a battle
const WING: f32 = 68.0; // video rows the interface's wing covers (34 px of art at 2×)

/// The video's output: 1920×1080, the field from 1× (all of it) to 3×, the interface at 2×.
const FRAME: Frame = Frame { w: OW, h: OH, fw: FW, fh: FH, zmin: 1.0, zmax: 3.0, zbase: 2.0, wing: WING, hud_scale: 2, hud_x0: 0 };

/// The battles of `seeds` one after another as raw 1920×1080 RGB frames to stdout; the sounds to `sound_path`.
pub fn run(demo: &mut Demo, seeds: &[u64], sound_path: &str) {
    let mut out = std::io::stdout().lock();
    let mut buf = vec![0u8; (OW * OH * 3) as usize];
    let mut sound = vec![];
    let mut beds = vec![];
    let mut t0 = 0.0f32; // seconds of video before this battle
    let mut n = 0;
    for &seed in seeds {
        demo.restart(seed);
        let total = demo.rec.frames() as f32;
        let span = total + 24.0 + HOLD;
        for c in &demo.cues {
            sound.push(serde_json::json!({"t": t0 + c.frame as f32 / 24.0, "frame": c.frame, "battle": seed, "name": c.name, "gain": c.gain, "x": c.x}));
        }
        let swarm_gone = (0..demo.rec.frames())
            .find(|&f| !demo.rec.units.iter().enumerate().any(|(i, u)| u.side == 1 && demo.rec.state_at(i, f).alive))
            .unwrap_or(demo.rec.frames());
        beds.push(serde_json::json!([t0, t0 + swarm_gone as f32 / 24.0]));
        let mut cam = camera::target(&demo.rec, 0.0, &FRAME);
        let frames = (span * FPS / 24.0).ceil() as i32;
        for k in 0..frames {
            let ff = k as f32 * 24.0 / FPS;
            let want = camera::target(&demo.rec, ff.min(total - 1.0), &FRAME);
            camera::follow(&mut cam, want, 1.0 / FPS, &FRAME);
            demo.view.frame = ff.min(total + 24.0);
            let mut field = Image::new(FW, FH);
            render::draw_field(&mut field, &demo.assets, &demo.rec, &demo.sparks, &demo.view);
            let mut hud = Image::clear(W, H);
            render::draw_hud(&mut hud, &demo.assets, &demo.rec, &demo.view);
            let light = (ff / FADE).min((span - ff) / FADE).clamp(0.0, 1.0);
            camera::compose(&field, &hud, cam, light, &mut buf, &FRAME, 3);
            out.write_all(&buf).expect("stdout");
            n += 1;
        }
        eprintln!("бой {seed}: ходов {}, победил {:?}, кадров {frames}", demo.rec.rounds.len(), demo.rec.outcome.winner);
        t0 += frames as f32 / FPS;
    }
    let doc = serde_json::json!({"seconds": t0, "cues": sound, "bed": beds});
    std::fs::write(sound_path, serde_json::to_string(&doc).unwrap()).expect("write");
    eprintln!("{n} кадров, {t0:.1} с; звуки — {sound_path}");
}
