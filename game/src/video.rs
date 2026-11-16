//! A video of the demo: battles one after another at 60 frames a second, the field zoomed on the fight by a camera
//! (2× while the armies stand apart, up to 3× on the clash; sharp pixels at any zoom), the interface over it at 2×.
//! Raw RGB frames go to stdout for ffmpeg; the sounds with their times go to a JSON file, to mix the soundtrack.

use crate::gfx::Image;
use crate::playback::{Pose, Record, FR};
use sim::battle::Event;
use crate::render::{self, H, W};
use crate::Demo;
use std::io::Write;

pub const OW: i32 = W * 2;
pub const OH: i32 = H * 2;
const FPS: f32 = 60.0;
const HOLD: f32 = 96.0; // game frames the end plate stays before the next battle (the jingle plays out)
const FADE: f32 = 12.0; // game frames of the fade from and to black around a battle
const WING: f32 = 68.0; // video rows the interface's wing covers (34 px of art at 2×)

#[derive(Clone, Copy)]
struct Cam {
    cx: f32,
    cy: f32,
    z: f32,
}

/// Where the camera wants to be: on the clash — the units hit in the coming second and a half (and those biting
/// them from close by) — as close as 3×; with no blows near, on every standing unit. A gun far behind may be out
/// of the picture: its shot flies in.
fn target(rec: &Record, ff: f32) -> Cam {
    let f = (ff as i32).min(rec.frames() - 1);
    let shown = rec.shown(ff.min((rec.frames() - 1) as f32));
    let at = |id: usize| shown.iter().find(|s| s.id == id && s.pose != Pose::Dead).map(|s| (s.x, s.y));
    let mut ids = vec![];
    for r in ((f - 18).max(0) / FR) as usize..=(((f + 36) / FR) as usize).min(rec.rounds.len() - 1) {
        for m in rec.moments(r) {
            if m.frame < f - 18 || m.frame > f + 36 {
                continue;
            }
            if let Event::Hit { a, t, .. } = m.ev {
                ids.push(t);
                if let (Some(p), Some(q)) = (at(a), at(t)) {
                    if (p.0 - q.0).hypot(p.1 - q.1) < 90.0 {
                        ids.push(a);
                    }
                }
            }
        }
    }
    if ids.iter().filter(|&&i| at(i).is_some()).count() < 2 {
        ids = (0..rec.units.len()).collect();
    }
    let (mut x0, mut y0, mut x1, mut y1) = (f32::MAX, f32::MAX, f32::MIN, f32::MIN);
    for &id in &ids {
        let Some((x, y)) = at(id) else { continue };
        let u = &rec.units[id];
        let (hw, top) = if u.fp >= 2 || u.leader { (46.0, 96.0) } else { (26.0, 56.0) };
        x0 = x0.min(x - hw);
        x1 = x1.max(x + hw);
        y0 = y0.min(y - top);
        y1 = y1.max(y + 14.0);
    }
    if x0 > x1 {
        return Cam { cx: W as f32 / 2.0, cy: H as f32 / 2.0, z: 2.0 };
    }
    let m = 30.0;
    let (bw, bh) = (x1 - x0 + 2.0 * m, y1 - y0 + 2.0 * m);
    let z = (OW as f32 / bw).min((OH as f32 - WING) / bh).clamp(2.0, 3.0);
    // the box's middle sits in the middle of what the wing leaves open
    Cam { cx: (x0 + x1) / 2.0, cy: (y0 + y1) / 2.0 - WING / 2.0 / z, z }
}

fn clamp(c: Cam) -> Cam {
    let (hw, hh) = (OW as f32 / 2.0 / c.z, OH as f32 / 2.0 / c.z);
    Cam { cx: c.cx.clamp(hw, W as f32 - hw), cy: c.cy.clamp(hh, H as f32 - hh), z: c.z }
}

/// Sharp bilinear: each art pixel stays a solid block, only its edges are blended — so a zoom of 2.4 shows
/// neither blur nor pixels of uneven size.
fn axis(start: f32, n: i32, z: f32, size: i32) -> Vec<(i32, i32, f32)> {
    (0..n)
        .map(|k| {
            let p = start + (k as f32 + 0.5) / z - 0.5;
            let i = p.floor();
            let f = (((p - i) - 0.5) * z + 0.5).clamp(0.0, 1.0);
            let i = i as i32;
            (i.clamp(0, size - 1), (i + 1).clamp(0, size - 1), f)
        })
        .collect()
}

fn compose(field: &Image, hud: &Image, c: Cam, light: f32, out: &mut [u8]) {
    let xs = axis(c.cx - OW as f32 / 2.0 / c.z, OW, c.z, field.w);
    let ys = axis(c.cy - OH as f32 / 2.0 / c.z, OH, c.z, field.h);
    for (y, &(y0, y1, fy)) in ys.iter().enumerate() {
        let row = &mut out[y * OW as usize * 3..(y + 1) * OW as usize * 3];
        for (x, &(x0, x1, fx)) in xs.iter().enumerate() {
            let (a, b, cc, d) = (field.get(x0, y0), field.get(x1, y0), field.get(x0, y1), field.get(x1, y1));
            let h = hud.get(x as i32 / 2, y as i32 / 2);
            let ha = h[3] as f32 / 255.0;
            for k in 0..3 {
                let top = a[k] as f32 + (b[k] as f32 - a[k] as f32) * fx;
                let bot = cc[k] as f32 + (d[k] as f32 - cc[k] as f32) * fx;
                let v = top + (bot - top) * fy;
                row[x * 3 + k] = ((v * (1.0 - ha) + h[k] as f32 * ha) * light).round().clamp(0.0, 255.0) as u8;
            }
        }
    }
}

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
        let mut cam = clamp(target(&demo.rec, 0.0));
        let frames = (span * FPS / 24.0).ceil() as i32;
        for k in 0..frames {
            let ff = k as f32 * 24.0 / FPS;
            let want = clamp(target(&demo.rec, ff.min(total - 1.0)));
            cam.z += (want.z - cam.z) * 0.03;
            cam.cx += (want.cx - cam.cx) * 0.06;
            cam.cy += (want.cy - cam.cy) * 0.06;
            cam = clamp(cam);
            demo.view.frame = ff.min(total + 24.0);
            let mut field = Image::new(W, H);
            render::draw_field(&mut field, &demo.assets, &demo.rec, &demo.sparks, &demo.view);
            let mut hud = Image::clear(W, H);
            render::draw_hud(&mut hud, &demo.assets, &demo.rec, &demo.view);
            let light = (ff / FADE).min((span - ff) / FADE).clamp(0.0, 1.0);
            compose(&field, &hud, cam, light, &mut buf);
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
