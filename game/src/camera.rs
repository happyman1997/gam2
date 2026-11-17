//! The camera over the field, for the window and for the video: it holds the clash — the units hit in the coming
//! second and a half (and those biting them from close by) — zooming from the whole field up to half as close again;
//! with no blows near, it takes in every standing unit. The picture is put together at the output's own size: the
//! field sampled sharp-bilinear (each art pixel a solid block, only its edges blended, so any zoom shows neither
//! blur nor pixels of uneven size), the interface laid over it at a whole factor.

use crate::gfx::Image;
use crate::playback::{Pose, Record, FR};
use crate::render::{H, W};
use rayon::prelude::*;
use sim::battle::Event;

#[derive(Clone, Copy)]
pub struct Cam {
    /// The art pixel at the middle of the output.
    pub cx: f32,
    pub cy: f32,
    /// Output pixels per art pixel.
    pub z: f32,
}

/// The output the camera fills: its size, the zoom range, the rows the interface's wing covers at the top, and
/// how the interface is laid on (its whole factor and left edge).
#[derive(Clone, Copy)]
pub struct Frame {
    pub w: i32,
    pub h: i32,
    pub zmin: f32,
    pub zmax: f32,
    pub wing: f32,
    pub hud_scale: i32,
    pub hud_x0: i32,
}

impl Frame {
    /// An output of w×h: the whole field covers it at the widest, half as close again at the nearest; the interface
    /// at the largest whole factor that fits, centred.
    pub fn fit(w: i32, h: i32) -> Frame {
        let base = (w as f32 / W as f32).max(h as f32 / H as f32);
        let s = ((w / W).min(h / H)).max(1);
        Frame { w, h, zmin: base, zmax: base * 1.5, wing: 34.0 * s as f32, hud_scale: s, hud_x0: (w - W * s) / 2 }
    }

    /// Where an output pixel falls on the interface's own 960×540 canvas.
    pub fn hud_point(&self, x: i32, y: i32) -> (i32, i32) {
        ((x - self.hud_x0).div_euclid(self.hud_scale), y.div_euclid(self.hud_scale))
    }
}

/// The whole field, as wide as the output allows.
pub fn whole(fr: &Frame) -> Cam {
    clamp(Cam { cx: W as f32 / 2.0, cy: H as f32 / 2.0, z: fr.zmin }, fr)
}

/// Where the camera wants to be at frame `ff`.
pub fn target(rec: &Record, ff: f32, fr: &Frame) -> Cam {
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
        return whole(fr);
    }
    let m = 30.0;
    let (bw, bh) = (x1 - x0 + 2.0 * m, y1 - y0 + 2.0 * m);
    let z = (fr.w as f32 / bw).min((fr.h as f32 - fr.wing) / bh).clamp(fr.zmin, fr.zmax);
    // the box's middle sits in the middle of what the wing leaves open
    clamp(Cam { cx: (x0 + x1) / 2.0, cy: (y0 + y1) / 2.0 - fr.wing / 2.0 / z, z }, fr)
}

/// Kept inside the field: no edge of the output looks past it.
pub fn clamp(c: Cam, fr: &Frame) -> Cam {
    let (hw, hh) = (fr.w as f32 / 2.0 / c.z, fr.h as f32 / 2.0 / c.z);
    let cx = if hw * 2.0 >= W as f32 { W as f32 / 2.0 } else { c.cx.clamp(hw, W as f32 - hw) };
    let cy = if hh * 2.0 >= H as f32 { H as f32 / 2.0 } else { c.cy.clamp(hh, H as f32 - hh) };
    Cam { cx, cy, z: c.z }
}

/// The camera eases toward where it wants to be, `secs` after the last step: the pan in about a quarter of a
/// second, the zoom in about half.
pub fn follow(cam: &mut Cam, want: Cam, secs: f32, fr: &Frame) {
    let k = |rate: f32| 1.0 - (-rate * secs).exp();
    cam.z += (want.z - cam.z) * k(1.8);
    cam.cx += (want.cx - cam.cx) * k(3.7);
    cam.cy += (want.cy - cam.cy) * k(3.7);
    *cam = clamp(*cam, fr);
}

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

/// The output picture: the field under the camera, the interface over it, all dimmed by `light` (a fade). `out`
/// holds `channels` bytes a pixel (3 for a video's RGB, 4 for the window's RGBA).
pub fn compose(field: &Image, hud: &Image, c: Cam, light: f32, out: &mut [u8], fr: &Frame, channels: usize) {
    let xs = axis(c.cx - fr.w as f32 / 2.0 / c.z, fr.w, c.z, field.w);
    let ys = axis(c.cy - fr.h as f32 / 2.0 / c.z, fr.h, c.z, field.h);
    let stride = fr.w as usize * channels;
    out.par_chunks_mut(stride).enumerate().take(fr.h as usize).for_each(|(y, row)| {
        let (y0, y1, fy) = ys[y];
        let (_, hy) = fr.hud_point(0, y as i32);
        for (x, &(x0, x1, fx)) in xs.iter().enumerate() {
            let (a, b, cc, d) = (field.get(x0, y0), field.get(x1, y0), field.get(x0, y1), field.get(x1, y1));
            let hx = (x as i32 - fr.hud_x0).div_euclid(fr.hud_scale);
            let h = if (0..hud.w).contains(&hx) && (0..hud.h).contains(&hy) { hud.get(hx, hy) } else { [0, 0, 0, 0] };
            let ha = h[3] as f32 / 255.0;
            for k in 0..3 {
                let top = a[k] as f32 + (b[k] as f32 - a[k] as f32) * fx;
                let bot = cc[k] as f32 + (d[k] as f32 - cc[k] as f32) * fx;
                let v = top + (bot - top) * fy;
                row[x * channels + k] = ((v * (1.0 - ha) + h[k] as f32 * ha) * light).round().clamp(0.0, 255.0) as u8;
            }
            if channels == 4 {
                row[x * 4 + 3] = 255;
            }
        }
    });
}
