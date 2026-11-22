//! The camera over the field, for the window and for the video: it holds the clash — the units hit in the coming
//! second and a half (and those biting them from close by) — zooming from the whole field (twice the screen's art
//! each way: at 1080p pixel for pixel) up to as close as the player's level lets it;
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

/// The output the camera fills: its size, the picture under the camera (a screen's background, or the battlefield,
/// bigger), the zoom range, the rows the interface's wing covers at the top, and how the interface is laid on (its
/// whole factor and left edge).
#[derive(Clone, Copy)]
pub struct Frame {
    pub w: i32,
    pub h: i32,
    /// The picture under the camera, in art pixels.
    pub fw: i32,
    pub fh: i32,
    /// Output pixels per art pixel: the whole picture at `zmin`; `zbase` — the interface's canvas filling the output
    /// (the camera's levels are counted in it).
    pub zmin: f32,
    pub zmax: f32,
    pub zbase: f32,
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
        Frame { w, h, fw: W, fh: H, zmin: base, zmax: base * 1.5, zbase: base, wing: 34.0 * s as f32, hud_scale: s, hud_x0: (w - W * s) / 2 }
    }

    /// The same output over a picture of fw×fh (the battlefield): the whole of it at the widest, the closest as
    /// close as over the interface's own canvas.
    pub fn over(mut self, fw: i32, fh: i32) -> Frame {
        self.fw = fw;
        self.fh = fh;
        self.zmin = (self.w as f32 / fw as f32).max(self.h as f32 / fh as f32);
        self.zmax = (self.zbase * 1.5).max(self.zmin);
        self
    }

    /// Where an output pixel falls on the interface's own 960×540 canvas.
    pub fn hud_point(&self, x: i32, y: i32) -> (i32, i32) {
        ((x - self.hud_x0).div_euclid(self.hud_scale), y.div_euclid(self.hud_scale))
    }
}

/// The whole field, as wide as the output allows.
pub fn whole(fr: &Frame) -> Cam {
    clamp(Cam { cx: fr.fw as f32 / 2.0, cy: fr.fh as f32 / 2.0, z: fr.zmin }, fr)
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

/// Where the battle's camera wants to be at frame `ff` with the player's level: 0 — the whole field, else the clash
/// with the camera coming at most `zooms[level]` times as close as the interface's canvas filling the output.
pub fn at_level(rec: &Record, ff: f32, fr: &Frame, level: u8, zooms: &[f32]) -> Cam {
    match zooms.get(level as usize) {
        Some(&k) if level > 0 => {
            let mut f = *fr;
            f.zmax = (f.zbase * k).max(f.zmin);
            target(rec, ff.min((rec.frames() - 1) as f32), &f)
        }
        _ => whole(fr),
    }
}

/// Kept inside the field: no edge of the output looks past it.
pub fn clamp(c: Cam, fr: &Frame) -> Cam {
    let (hw, hh) = (fr.w as f32 / 2.0 / c.z, fr.h as f32 / 2.0 / c.z);
    let (fw, fh) = (fr.fw as f32, fr.fh as f32);
    let cx = if hw * 2.0 >= fw { fw / 2.0 } else { c.cx.clamp(hw, fw - hw) };
    let cy = if hh * 2.0 >= fh { fh / 2.0 } else { c.cy.clamp(hh, fh - hh) };
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

/// One axis of the sampling: for each output pixel, the two art pixels it falls between and the weight of the second
/// (0–256) — 0 or 256 inside an art pixel, between only on its edge.
fn axis(start: f32, n: i32, z: f32, size: i32) -> Vec<(i32, i32, u32)> {
    (0..n)
        .map(|k| {
            let p = start + (k as f32 + 0.5) / z - 0.5;
            let i = p.floor();
            let f = (((p - i) - 0.5) * z + 0.5).clamp(0.0, 1.0);
            let i = i as i32;
            (i.clamp(0, size - 1), (i + 1).clamp(0, size - 1), (f * 256.0).round() as u32)
        })
        .collect()
}

fn lerp(a: [u8; 3], b: [u8; 3], f: u32) -> [u8; 3] {
    let m = |p: u8, q: u8| ((p as u32 * (256 - f) + q as u32 * f + 128) >> 8) as u8;
    [m(a[0], b[0]), m(a[1], b[1]), m(a[2], b[2])]
}

/// The output picture: the field under the camera, the interface over it, all dimmed by `light` (a fade). `out`
/// holds `channels` bytes a pixel (3 for a video's RGB, 4 for the window's RGBA). Two passes: each art row the
/// output needs is stretched across the output's width once, then each output row is put together from two of them
/// (most rows from one) — a screen of 4K costs a few milliseconds, not a hundred.
pub fn compose(field: &Image, hud: &Image, c: Cam, light: f32, out: &mut [u8], fr: &Frame, channels: usize) {
    let xs = axis(c.cx - fr.w as f32 / 2.0 / c.z, fr.w, c.z, field.w);
    let ys = axis(c.cy - fr.h as f32 / 2.0 / c.z, fr.h, c.z, field.h);
    let w = fr.w as usize;
    let r0 = ys.iter().map(|y| y.0).min().unwrap_or(0);
    let r1 = ys.iter().map(|y| y.1).max().unwrap_or(0);
    let mut rows = vec![[0u8; 3]; (r1 - r0 + 1) as usize * w];
    rows.par_chunks_mut(w).enumerate().for_each(|(k, row)| {
        let src = &field.px[(r0 as usize + k) * field.w as usize..][..field.w as usize];
        for (o, &(x0, x1, fx)) in row.iter_mut().zip(&xs) {
            let (a, b) = (src[x0 as usize], src[x1 as usize]);
            *o = match fx {
                0 => [a[0], a[1], a[2]],
                256 => [b[0], b[1], b[2]],
                _ => lerp([a[0], a[1], a[2]], [b[0], b[1], b[2]], fx),
            };
        }
    });
    let hx: Vec<i32> = (0..fr.w).map(|x| (x - fr.hud_x0).div_euclid(fr.hud_scale)).collect();
    let lit = (light.clamp(0.0, 1.0) * 256.0).round() as u32;
    out.par_chunks_mut(w * channels).enumerate().take(fr.h as usize).for_each(|(y, row)| {
        let (y0, y1, fy) = ys[y];
        let ra = &rows[(y0 - r0) as usize * w..][..w];
        let rb = &rows[(y1 - r0) as usize * w..][..w];
        let hy = (y as i32).div_euclid(fr.hud_scale);
        let hrow = (0..hud.h).contains(&hy).then(|| &hud.px[(hy * hud.w) as usize..][..hud.w as usize]);
        for x in 0..w {
            let mut v = match fy {
                0 => ra[x],
                256 => rb[x],
                _ => lerp(ra[x], rb[x], fy),
            };
            if let Some(hr) = hrow {
                if (0..hud.w).contains(&hx[x]) {
                    let h = hr[hx[x] as usize];
                    let a = h[3] as u32;
                    if a > 0 {
                        for k in 0..3 {
                            v[k] = ((v[k] as u32 * (255 - a) + h[k] as u32 * a + 127) / 255) as u8;
                        }
                    }
                }
            }
            if lit < 256 {
                for p in &mut v {
                    *p = ((*p as u32 * lit + 128) >> 8) as u8;
                }
            }
            row[x * channels..x * channels + 3].copy_from_slice(&v);
            if channels == 4 {
                row[x * 4 + 3] = 255;
            }
        }
    });
}
