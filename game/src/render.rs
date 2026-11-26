//! A frame of the demo: the field with the units in depth order, the effects and numbers over them, the swarm's
//! thin wing on top (the tug of war, the counts, the turn, the speed buttons with their keys), the leaders' health
//! with the crown, and at the end the plate across the dimmed field.

use crate::assets::{Align, Assets, Font};
use crate::gfx::Image;
use crate::playback::{Effect, Number, NumStyle, Pose, Record, CH, CW, FLY, FR, S_BURN, STATUS_GLYPHS, X0, Y0};
use sim::Event;
use std::sync::OnceLock;

/// A line of pixels from (x0, y0) to (x1, y1), each once.
fn px_line(out: &mut Vec<(i32, i32)>, x0: i32, y0: i32, x1: i32, y1: i32) {
    let n = (x1 - x0).abs().max((y1 - y0).abs()).max(1);
    for k in 0..=n {
        let p = (x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n);
        if out.last() != Some(&p) {
            out.push(p);
        }
    }
}

/// A small hash of a cell, for the look of what lies on it to differ from cell to cell.
fn cell_hash(c: usize) -> u32 {
    let mut h = (c as u32).wrapping_mul(0x9E37_79B9) ^ 0x5bd1_e995;
    h ^= h >> 15;
    h = h.wrapping_mul(0x2c1b_3c6d);
    h ^ (h >> 12)
}

/// Webs on a cell (50×34), eight kinds: a few threads from a knot somewhere off the middle out to the edges (so webs of
/// neighbouring cells run into one another), one or two sagging rings between them — (x, y, strength) of each pixel.
fn web_pixels(kind: u32) -> &'static [(i32, i32, f32)] {
    static P: OnceLock<Vec<Vec<(i32, i32, f32)>>> = OnceLock::new();
    &P.get_or_init(|| {
        (0..8u32)
            .map(|v| {
                let h = cell_hash(v as usize * 7919 + 13);
                let (cx, cy) = (20 + (h % 11) as i32, 13 + ((h >> 4) % 9) as i32);
                let ends = [(0, 0), (24, 0), (49, 0), (49, 16), (49, 33), (26, 33), (0, 33), (0, 18)];
                // five to eight threads: the ones whose bit is clear are missing
                let keep: Vec<usize> = (0..8).filter(|&k| (h >> (8 + k)) & 1 == 1 || k % 3 == 0).collect();
                let mut spokes = vec![];
                for &k in &keep {
                    px_line(&mut spokes, cx, cy, ends[k].0, ends[k].1);
                }
                let mut rings = vec![];
                let fs: &[f32] = if (h >> 20) & 1 == 1 { &[0.36, 0.7] } else { &[0.5] };
                for &f in fs {
                    let pts: Vec<(i32, i32)> = keep
                        .iter()
                        .enumerate()
                        .map(|(n, &k)| {
                            let g = if n % 2 == 1 { f * 0.84 } else { f };
                            ((cx as f32 + (ends[k].0 - cx) as f32 * g).round() as i32, (cy as f32 + (ends[k].1 - cy) as f32 * g).round() as i32)
                        })
                        .collect();
                    for n in 0..pts.len() {
                        // a strand here and there is broken
                        if (h >> (n % 12)) & 7 == 0 {
                            continue;
                        }
                        let (a, b) = (pts[n], pts[(n + 1) % pts.len()]);
                        px_line(&mut rings, a.0, a.1, b.0, b.1);
                    }
                }
                let mut out: Vec<(i32, i32, f32)> = spokes.into_iter().map(|(x, y)| (x, y, 0.22)).collect();
                out.extend(rings.into_iter().map(|(x, y)| (x, y, 0.3)));
                out
            })
            .collect()
    })[kind as usize % 8]
}

/// A pixel to lay on the field: where, its colour, how strongly.
type Px = (i32, i32, [u8; 3], f32);

/// Colours of a pool on the field, lit to dark: a glint, the lit upper rim, the dark lower rim, the gloss, the body —
/// and how strongly each lies over the ground.
struct Pool {
    cols: [[u8; 3]; 5],
    alpha: [f32; 5],
}

const HONEY: Pool = Pool { cols: [[255, 248, 210], [255, 226, 140], [96, 52, 8], [255, 190, 60], [178, 104, 14]], alpha: [0.9, 0.7, 0.5, 0.45, 0.34] };
/// The swarm's slime: thin, yellow-green, a wet shine on it.
const GOO: Pool = Pool { cols: [[236, 255, 196], [196, 226, 120], [44, 60, 14], [168, 206, 84], [112, 144, 44]], alpha: [0.85, 0.55, 0.45, 0.32, 0.26] };
/// A machine's oil: near black, a cold rainbow sheen on its bulge.
const OIL: Pool = Pool { cols: [[214, 196, 255], [96, 84, 118], [6, 4, 10], [64, 112, 140], [16, 14, 22]], alpha: [0.9, 0.7, 0.8, 0.55, 0.78] };

/// Slime fire has dried, a dry shell's fallen: a dull grey-brown crust, no shine on it.
const CRUST: Pool = Pool { cols: [[170, 156, 134], [140, 126, 104], [40, 32, 26], [118, 106, 88], [84, 74, 62]], alpha: [0.5, 0.55, 0.5, 0.4, 0.42] };

/// A layer of a round as pixels of the field: one pool over all `cells` (each cell a soft blob, the blobs summed and
/// cut at a level — neighbouring cells run into one pool, a lone one is a puddle), its outline lumpy, a darker rim
/// along its lower edge, a sheen and a glint or two. Made once a round for each `slot` and kept.
fn pool_layer(cells: &[usize], pool: &Pool, slot: u8) -> std::rc::Rc<Vec<Px>> {
    type Layer = (u64, std::rc::Rc<Vec<Px>>);
    thread_local!(static KEPT: std::cell::RefCell<std::collections::HashMap<u8, Layer>> = std::cell::RefCell::new(Default::default()));
    // kept by what is covered (a new battle in the same place must not see the old one's pools)
    let key = cells.iter().fold(1469598103934665603u64, |h, &c| (h ^ c as u64).wrapping_mul(1099511628211));
    if let Some(l) = KEPT.with(|k| k.borrow().get(&slot).filter(|l| l.0 == key).map(|l| l.1.clone())) {
        return l;
    }
    let cols = sim::battle::W;
    let cells: Vec<(f32, f32)> = cells.iter().map(|&c| (X0 + ((c as i32 % cols) as f32 + 0.5) * CW, Y0 + ((c as i32 / cols) as f32 + 0.5) * CH)).collect();
    let mut out = vec![];
    if !cells.is_empty() {
        let (x0, x1) = (cells.iter().map(|c| c.0).fold(f32::MAX, f32::min) as i32 - 40, cells.iter().map(|c| c.0).fold(f32::MIN, f32::max) as i32 + 40);
        let (y0, y1) = (cells.iter().map(|c| c.1).fold(f32::MAX, f32::min) as i32 - 30, cells.iter().map(|c| c.1).fold(f32::MIN, f32::max) as i32 + 30);
        let (w, h) = (x1 - x0 + 1, y1 - y0 + 1);
        let mut f = vec![0f32; (w * h) as usize];
        for &(cx, cy) in &cells {
            for y in (cy as i32 - 40).max(y0)..=(cy as i32 + 40).min(y1) {
                for x in (cx as i32 - 56).max(x0)..=(cx as i32 + 56).min(x1) {
                    let (dx, dy) = ((x as f32 - cx) / 28.0, (y as f32 - cy) / 19.0);
                    f[((y - y0) * w + x - x0) as usize] += (-(dx * dx + dy * dy)).exp();
                }
            }
        }
        let at = |x: i32, y: i32| if x < x0 || y < y0 || x > x1 || y > y1 { 0.0 } else { f[((y - y0) * w + x - x0) as usize] };
        for y in y0..=y1 {
            for x in x0..=x1 {
                let v = at(x, y);
                // the outline lumpy: the level wanders a little, in blocks of three pixels (a pixel-art edge)
                let n = (cell_hash(((x / 3) * 7919 + (y / 3) * 104_729) as usize) % 100) as f32 / 100.0;
                let level = 0.72 + 0.12 * n;
                if v < level {
                    continue;
                }
                let lower_edge = at(x, y + 3) < level;
                let top_edge = at(x, y - 1) < level;
                // the gloss: a band a few pixels in from the upper-left of the pool, where the light falls on the bulge
                let gloss = at(x - 4, y - 4) < level && at(x, y - 2) >= level;
                let glint = v > 1.5 && cell_hash((x / 2 * 31 + y * 17) as usize).is_multiple_of(61);
                let k = if glint {
                    0
                } else if top_edge {
                    1
                } else if lower_edge {
                    2
                } else if gloss {
                    3
                } else {
                    4
                };
                out.push((x, y, pool.cols[k], pool.alpha[k]));
            }
        }
    }
    let l = std::rc::Rc::new(out);
    KEPT.with(|k| k.borrow_mut().insert(slot, (key, l.clone())));
    l
}

fn honey_layer(rec: &Record, r: usize) -> std::rc::Rc<Vec<Px>> {
    let cells: Vec<usize> = rec.rounds[r].honey.iter().enumerate().filter(|(_, &s)| s != -1).map(|(c, _)| c).collect();
    pool_layer(&cells, &HONEY, 0)
}

/// The earthquake's crack down a column: a jagged black split, a pale lip of broken earth on its left, chips of it
/// thrown up along the edge.
fn rift_line(cv: &mut Image, col: i32) {
    let cx = X0 + (col as f32 + 0.5) * CW;
    let mut x = cx;
    let (top, bottom) = (Y0 as i32 - 6, (Y0 + sim::battle::H as f32 * CH) as i32 + 6);
    let mut y = top;
    while y < bottom {
        let step = 5 + (cell_hash((y * 31 + col * 7) as usize) % 5) as i32;
        let nx = cx + ((cell_hash((y * 17 + col * 131) as usize) % 21) as f32 - 10.0);
        let mut pts = vec![];
        line(&mut pts, x, y as f32, nx, (y + step) as f32);
        for (px, py) in pts {
            let w = 1 + (cell_hash((py * 13 + col) as usize) % 3) as i32;
            for o in -w..=w {
                cv.blend_px(px + o, py, [12, 8, 14, 255], 0.92);
            }
            cv.blend_px(px - w - 1, py, [168, 150, 128, 255], 0.55);
            cv.blend_px(px + w + 1, py, [40, 30, 34, 255], 0.5);
            if cell_hash((py * 7 + px) as usize).is_multiple_of(23) {
                cv.blend_px(px - w - 3, py - 1, [140, 124, 104, 255], 0.7);
            }
        }
        x = nx;
        y += step;
    }
}

/// What lies on the field's ground at round `r`: the swarm's honey, then its web over it.
fn ground_layers(cv: &mut Image, rec: &Record, r: usize) {
    let round = &rec.rounds[r];
    let cols = sim::battle::W;
    // the fallen's slime and the machines' oil, the swarm's honey over them
    if !round.ground.is_empty() {
        let of = |k: u8| -> Vec<usize> { round.ground.iter().enumerate().filter(|(_, &g)| g == k).map(|(c, _)| c).collect() };
        for (cells, pool, slot) in [(of(sim::battle::GOO), &GOO, 1), (of(sim::battle::OIL), &OIL, 2), (of(sim::battle::CRUST), &CRUST, 3)] {
            for &(x, y, col, a) in pool_layer(&cells, pool, slot).iter() {
                cv.blend_px(x, y, [col[0], col[1], col[2], 255], a);
            }
        }
    }
    for c in 0..cols {
        if !round.rift.is_empty() && round.rift[c as usize] != 0 {
            rift_line(cv, c);
        }
    }
    for &(x, y, col, a) in honey_layer(rec, r).iter() {
        cv.blend_px(x, y, [col[0], col[1], col[2], 255], a);
    }
    for (c, _) in round.web.iter().enumerate().filter(|(_, &s)| s != -1) {
        let (x0, y0) = ((X0 + (c as i32 % cols) as f32 * CW) as i32, (Y0 + (c as i32 / cols) as f32 * CH) as i32);
        for &(x, y, a) in web_pixels(cell_hash(c) >> 3) {
            cv.blend_px(x0 + x, y0 + y, [232, 224, 208, 255], a);
        }
    }
}

/// Spilt oil burning: three tongues of fire on each burning cell, its light round it.
fn burning_ground(cv: &mut Image, a: &Assets, rec: &Record, r: usize, ff: f32) {
    let round = &rec.rounds[r];
    if round.flames.is_empty() {
        return;
    }
    let Some(fx) = a.fx.get("burn-body") else { return };
    let cols = sim::battle::W;
    for (c, _) in round.flames.iter().enumerate().filter(|(_, &v)| v > 0) {
        let (cx, cy) = (X0 + ((c as i32 % cols) as f32 + 0.5) * CW, Y0 + ((c as i32 / cols) as f32 + 0.5) * CH);
        for (n, (dx, dy)) in [(-13.0f32, 6.0f32), (11.0, 0.0), (0.0, 12.0)].iter().enumerate() {
            let k = ((ff * fx.fps / 24.0) as i32 + c as i32 * 5 + n as i32 * 3).rem_euclid(fx.frames);
            cv.blit_region(&fx.img, k * fx.w, 0, fx.w, fx.h, (cx + dx) as i32 - fx.pivot.0, (cy + dy) as i32 - fx.pivot.1, n == 1, 1.0);
        }
        cv.glow(cx, cy - 4.0, 52.0, [240, 138, 32], 0.35);
    }
}

/// Гроза over the field: the light gone slate-blue, rain slanting down in streaks, a white flash as lightning strikes.
fn storm(cv: &mut Image, ff: f32, flash: bool) {
    let (mr, mg, mb) = if flash { (1.18, 1.2, 1.26) } else { (0.76, 0.8, 0.93) };
    for p in cv.px.iter_mut() {
        p[0] = (p[0] as f32 * mr).min(255.0) as u8;
        p[1] = (p[1] as f32 * mg).min(255.0) as u8;
        p[2] = (p[2] as f32 * mb).min(255.0) as u8;
    }
    let (w, h) = (cv.w as f32, cv.h as f32);
    for k in 0..280usize {
        let hsh = cell_hash(k * 977 + 13);
        let speed = 30.0 + (hsh >> 8) as f32 % 12.0;
        let y = ((hsh >> 4) as f32 % h + ff * speed) % h;
        let x = (hsh % (cv.w as u32 + 300)) as f32 - 150.0 + y * 0.28;
        for j in 0..8 {
            let (px, py) = ((x + j as f32 * 0.28) as i32, (y + j as f32) as i32);
            if px >= 0 && (px as f32) < w {
                cv.blend_px(px, py, [176, 194, 228, 255], 0.3 + 0.03 * j as f32);
            }
        }
    }
}

/// Ночь over the field: dark and cold, but light round each of `lights` (x, y, radius) — what burns, what glows,
/// what flashes — in a few bands, as pixel art lights a night.
fn night(cv: &mut Image, lights: &[(f32, f32, f32)]) {
    const S: i32 = 8;
    let (lw, lh) = (cv.w / S + 2, cv.h / S + 2);
    let mut l = vec![0f32; (lw * lh) as usize];
    for &(x, y, r) in lights {
        let (gx0, gx1) = (((x - r) / S as f32).floor().max(0.0) as i32, (((x + r) / S as f32).ceil() as i32).min(lw - 1));
        let (gy0, gy1) = (((y - r) / S as f32).floor().max(0.0) as i32, (((y + r) / S as f32).ceil() as i32).min(lh - 1));
        for gy in gy0..=gy1 {
            for gx in gx0..=gx1 {
                let d = ((gx * S) as f32 - x).hypot((gy * S) as f32 - y) / r;
                if d < 1.0 {
                    let v = (1.0 - d).powf(1.3);
                    let c = &mut l[(gy * lw + gx) as usize];
                    *c = c.max(v);
                }
            }
        }
    }
    let w = cv.w;
    for j in 0..cv.h {
        let (gy, fy) = (j / S, (j % S) as f32 / S as f32);
        for i in 0..w {
            let (gx, fx) = (i / S, (i % S) as f32 / S as f32);
            let at = |x: i32, y: i32| l[(y * lw + x) as usize];
            let v = (at(gx, gy) * (1.0 - fx) + at(gx + 1, gy) * fx) * (1.0 - fy) + (at(gx, gy + 1) * (1.0 - fx) + at(gx + 1, gy + 1) * fx) * fy;
            let q = (v * 4.0).round() / 4.0;
            let p = &mut cv.px[(j * w + i) as usize];
            p[0] = (p[0] as f32 * (0.34 + 0.66 * q)) as u8;
            p[1] = (p[1] as f32 * (0.38 + 0.62 * q)) as u8;
            p[2] = (p[2] as f32 * (0.56 + 0.44 * q)) as u8;
        }
    }
}

/// A midge cloud: a faint dark haze, and in it a swirl of specks, each on its own small orbit, a few pale wings
/// catching the light; it thins as it fades (`k` 1 → 0).
fn midges(cv: &mut Image, x: f32, y: f32, ff: f32, id: usize, k: f32) {
    let (cx, cy) = (x, y - 16.0);
    for py in -8..=8i32 {
        for px in -14..=14i32 {
            let d = (px as f32 / 14.0).powi(2) + (py as f32 / 8.0).powi(2);
            if d <= 1.0 {
                cv.blend_px(cx as i32 + px, cy as i32 + py, [30, 24, 40, 255], 0.16 * (1.0 - d) * k);
            }
        }
    }
    let n = 30;
    for i in 0..n {
        let h = ((id * 31 + i * 17) % 97) as f32;
        let a = h * 0.61 + ff * (0.1 + (i % 5) as f32 * 0.03) * if i % 2 == 0 { 1.0 } else { -1.0 };
        let r = 0.25 + 0.75 * ((h * 0.37).sin() * 0.5 + 0.5);
        let px = cx + a.cos() * 13.0 * r;
        let py = cy + a.sin() * 8.0 * r + (ff * 0.3 + h).sin() * 1.5;
        let (col, al) = if i % 5 == 0 { ([170, 162, 196, 255], 0.8) } else { ([26, 20, 34, 255], 0.95) };
        cv.blend_px(px.round() as i32, py.round() as i32, col, al * k);
        // a wing beat: every other speck a pixel longer now and then
        if i % 2 == 1 && ((ff * 0.5) as usize + i).is_multiple_of(3) {
            cv.blend_px(px.round() as i32 + 1, py.round() as i32, col, al * k * 0.7);
        }
    }
}

/// The interface's canvas (and a screen's background).
pub const W: i32 = 960;
pub const H: i32 = 540;
/// The battlefield's: twice the interface's each way (sim::battle's 36×30 cells, 50×34 pixels each), so at 1080p
/// the whole field is shown pixel for pixel and the camera comes as close as before.
pub const FW: i32 = 1920;
pub const FH: i32 = 1080;

pub struct View {
    pub frame: f32,
    pub speed: u32,
    pub paused: bool,
    /// The button under the cursor, lit a little: one of the `Button`s.
    pub hover: Option<Button>,
    /// The end plate's button in a run: its words and its key (None: «новый бой», R — the demo's).
    pub end: Option<(String, String)>,
}

/// The clickable things of the battle screen.
#[derive(Clone, Copy, PartialEq, Debug)]
pub enum Button {
    Pause,
    Speed,
    ToEnd,
    NewBattle,
}

/// Where each button is, in art pixels (x0, y0, x1, y1); `NewBattle` only while the end plate is up.
pub fn button_at(rec: &Record, view: &View, x: i32, y: i32) -> Option<Button> {
    let end = view.frame as i32 - (rec.frames() - 1) > 12; // once the plate has settled
    let rects = [
        (Button::Pause, (722, 2, 798, 28)),
        (Button::Speed, (776, 2, 852, 28)),
        (Button::ToEnd, (830, 2, 966, 28)),
        (Button::NewBattle, (W / 2 - 84, PLATE_BUTTON_Y, W / 2 + 84, PLATE_BUTTON_Y + 26)),
    ];
    rects.iter().find(|(b, (x0, y0, x1, y1))| (*b != Button::NewBattle || end) && x >= *x0 && x < *x1 && y >= *y0 && y < *y1).map(|r| r.0)
}

const PLATE_BUTTON_Y: i32 = H / 2 + 74;

const INK: [u8; 3] = [236, 220, 196];
const MUTED: [u8; 3] = [170, 156, 180];
const ACID: [u8; 3] = [176, 244, 70];
const ACID_EDGE: [u8; 3] = [70, 150, 50];
const DARK: [u8; 3] = [40, 22, 8];

fn sprite_name(rec: &Record, id: usize, pose: Pose, f: i32) -> String {
    let info = &rec.units[id];
    let n = info.name.as_str();
    if info.machine {
        // the Foundry's bodies by name and size (a «smaller» frame is a size less): four frames of a walk
        let p = match pose {
            Pose::Idle => "idle".to_string(),
            Pose::Attack => "attack".to_string(),
            Pose::Dead => "broken".to_string(),
            Pose::Walk(k) => format!("walk{}", (k / 2) % 4), // four frames, each held two counts
        };
        return format!("{n}_{}_{p}", info.size);
    }
    let p = |dead: &str| match pose {
        Pose::Idle => "idle".to_string(),
        Pose::Attack => "attack".to_string(),
        Pose::Dead => dead.to_string(),
        Pose::Walk(k) => format!("walk{}", if info.fp >= 2 || info.leader { (k / 2) % 2 } else { k % 2 }),
    };
    match n {
        "Пожиратель" => format!("Пожиратель_{}_{}", rec.state_at(id, f).growth.min(3), p("dead")),
        "Матка" | "Разум улья" | "Чума" | "Личинка" => format!("{n}_{}", p("dead")),
        "Рабочая" => format!("Муравей (рабочая)_{}_{}", id % 4, p("dead")),
        "Солдат" => format!("Муравей (солдат)_{}_{}", id % 4, p("dead")),
        // the swarm's forms: four variants of each, the small ones scuttle a frame every count
        _ => format!("{n}_{}_{}", id % 4, p("dead")),
    }
}

/// The sprite to draw: the pose asked for, else the body standing (a body with no walk glides, one with no attack
/// pose strikes standing), else nothing.
fn sprite<'a>(a: &'a Assets, rec: &Record, id: usize, pose: Pose, f: i32) -> Option<(&'a crate::assets::Sprite, String)> {
    let name = sprite_name(rec, id, pose, f);
    if let Some(s) = a.sprites.get(&name) {
        return Some((s, name));
    }
    let idle = sprite_name(rec, id, Pose::Idle, f);
    a.sprites.get(&idle).map(|s| (s, idle))
}

const SLOTS: [(f32, f32); 4] = [(-11.0, -6.0), (11.0, -7.0), (-10.0, 8.0), (12.0, 7.0)];
/// A pack's three bodies: one in front, two a little behind it, left and right.
const PACK: [(f32, f32); 3] = [(1.0, 3.0), (-7.0, -3.0), (8.0, -4.0)];

/// How a unit moves on top of where it stands: the frame to draw, an offset, a flash.
struct Anim {
    pose: Pose,
    dx: f32,
    dy: f32,
    flash: f32,
}

/// The life on top of the battle's record (frame `ff`, the round's moments `ms`):
/// - standing, a body breathes: one pixel up and down, each at its own pace (a machine slower than a beast);
/// - an attack is a swing: it draws back for a moment, lunges at the target as the blow lands and settles back;
///   a shot or a discharge kicks the shooter back instead;
/// - a hit target flashes white and is knocked a couple of pixels away from the blow, then steadies;
/// - a killed one flashes and shudders for three frames before it falls (the fall itself: in the drawing loop).
fn animate(rec: &Record, ms: &[crate::playback::Moment], s: &crate::playback::Shown, ff: f32, at: &dyn Fn(usize) -> Option<(f32, f32)>) -> Anim {
    let info = &rec.units[s.id];
    let mut an = Anim { pose: s.pose, dx: 0.0, dy: 0.0, flash: 0.0 };
    let unit = |dx: f32, dy: f32| {
        let l = dx.hypot(dy).max(0.001);
        (dx / l, dy / l)
    };
    if let Some(k) = s.dead_at {
        let rel = ff - k as f32;
        if rel < 3.0 {
            an.pose = Pose::Idle;
            an.flash = 0.9 - rel * 0.2;
            an.dx = if (rel as i32) % 2 == 0 { -1.0 } else { 1.0 };
            return an;
        }
        // dropping to the ground: a little fall and a bounce
        an.dy = [-4.0, -2.0, -0.0, -1.0, 0.0][((rel - 3.0) as usize).min(4)];
        return an;
    }
    if s.pose == Pose::Dead {
        return an;
    }
    if s.pose == Pose::Idle {
        let slow = info.machine || info.fp >= 2;
        let period = if slow { 40.0 } else { 18.0 };
        let phase = (s.id as f32 * 0.37).fract();
        if ((ff / period) + phase).fract() >= 0.5 {
            an.dy = -1.0;
        }
    }
    let ranged = matches!(info.name.as_str(), "Мудрец" | "Орудие" | "Изобретатель");
    // its own blow nearest in time
    if let Some((m, t)) = ms
        .iter()
        .filter_map(|m| match m.ev {
            Event::Hit { a, t, .. } if a == s.id => Some((m, t)),
            _ => None,
        })
        .min_by(|p, q| (ff - p.0.frame as f32).abs().partial_cmp(&(ff - q.0.frame as f32).abs()).unwrap())
    {
        let rel = ff - m.frame as f32;
        if let Some((tx, ty)) = at(t) {
            let (ux, uy) = unit(tx - s.x, ty - s.y);
            let push = if ranged {
                if (0.0..4.0).contains(&rel) { -2.0 * (1.0 - rel / 4.0) } else { 0.0 }
            } else if (-5.0..-2.0).contains(&rel) {
                -1.5 // the wind-up
            } else if (-2.0..0.0).contains(&rel) {
                -1.5 + (rel + 2.0) / 2.0 * 6.0 // the lunge
            } else if (0.0..5.0).contains(&rel) {
                4.5 * (1.0 - rel / 5.0) // settling back
            } else {
                0.0
            };
            an.dx += ux * push;
            an.dy += uy * push * 0.6;
        }
    }
    // a blow it took
    for m in ms {
        if let Event::Hit { a, t, dmg } = m.ev {
            let rel = ff - m.frame as f32;
            if t != s.id || dmg <= 0 || !(0.0..5.0).contains(&rel) {
                continue;
            }
            an.flash = an.flash.max([0.75, 0.35, 0.0, 0.0, 0.0][rel as usize]); // two frames: a blink, not a glow
            if let Some((ax, ay)) = at(a) {
                let (ux, uy) = unit(s.x - ax, s.y - ay);
                let k = 2.5 * (1.0 - rel / 5.0) * if info.fp >= 2 { 0.5 } else { 1.0 };
                an.dx += ux * k;
                an.dy += uy * k * 0.6;
            }
        }
    }
    an
}

/// A standing body as drawn, for what is drawn on and over it: its middle, the top of its picture, its feet, the
/// picture's height, the states of all it stands for, the states its glyph row shows (0: none over it).
struct Marks {
    x: f32,
    top: f32,
    foot: f32,
    h: i32,
    body: u16,
    row: u16,
    leader: bool,
    id: usize,
}

/// A body killed this round, drawn once more over the effects: where its sprite went, its flash, where it fell,
/// how long ago.
struct Dying {
    sx: i32,
    sy: i32,
    flip: bool,
    flash: f32,
    x: f32,
    y: f32,
    golem: bool,
    big: bool,
    t: f32,
    name: String,
}

/// The dust a body raises as it falls: a ring of specks thrown out low along the ground and settling; a golem
/// throws dark grit and a few sparks.
fn dust(cv: &mut Image, x: f32, y: f32, t: f32, golem: bool, big: bool, seed: usize) {
    if !(0.0..10.0).contains(&t) {
        return;
    }
    let n = if big { 14 } else { 8 };
    let fade = 1.0 - t / 10.0;
    for i in 0..n {
        let h = (seed as u32).wrapping_mul(2654435761).wrapping_add(i as u32 * 40503);
        let ang = i as f32 / n as f32 * std::f32::consts::TAU + (h % 100) as f32 * 0.01;
        let speed = 1.2 + ((h >> 8) % 100) as f32 * 0.008 + if big { 0.8 } else { 0.0 };
        let d = speed * t.sqrt() * 3.2;
        let px = x + ang.cos() * d * 1.7;
        let py = y - 1.0 + ang.sin() * d * 0.55 - t * 0.25;
        let col = if golem { [132, 124, 116, 255] } else { [176, 158, 134, 255] }; // lighter than the ground, so it shows
        cv.blend_px(px as i32, py as i32, col, 0.9 * fade);
        cv.blend_px(px as i32 + 1, py as i32, col, 0.6 * fade);
        if big {
            cv.blend_px(px as i32, py as i32 - 1, col, 0.6 * fade);
            cv.blend_px(px as i32 + 1, py as i32 - 1, col, 0.4 * fade);
        }
        if golem && i % 3 == 0 && t < 5.0 {
            cv.blend_px(px as i32, (py - 2.0 - t) as i32, [255, 176, 64, 255], 1.0 - t / 5.0);
        }
    }
}

fn number(cv: &mut Image, a: &Assets, rec: &Record, n: &Number, f: i32, bars: &[(i32, i32, i32, i32)]) {
    let age = f - n.start;
    let life = if matches!(n.style, NumStyle::Crit) { 22 } else { 16 };
    if age < 0 || age >= life || f >= n.end {
        return;
    }
    // over the head (and over a leader's health), not on the body: the blow and who took it stay in sight
    let info = &rec.units[n.t];
    let head = sprite(a, rec, n.t, Pose::Idle, n.start).map(|(s, _)| s.oy).unwrap_or(40);
    let over = if info.leader { 22 } else { 3 };
    let tall = if matches!(n.style, NumStyle::Crit) { 24 } else { 16 };
    let (nx, ny) = (n.x, n.y - (head + over + tall) as f32 - n.k as f32 * 20.0); // a second number one line higher
    let t = (age as f32 / 4.0).min(1.0);
    let c1 = 1.70158;
    let pop = 1.0 + (c1 + 1.0) * (t - 1.0).powi(3) + c1 * (t - 1.0).powi(2); // out_back
    let dy = -6.0 * pop - (age - 8).max(0) as f32 * 0.5 + (1.0 - pop) * 6.0;
    let fade = if age < life - 5 { 1.0 } else { (life - age) as f32 / 5.0 };
    let (font, col, edge) = match n.style {
        NumStyle::Hit => ("title16", [214, 250, 110], [50, 96, 20]),
        NumStyle::Crit => ("title24", [246, 255, 206], [96, 150, 24]),
        NumStyle::Hurt => ("title16", [240, 160, 70], [100, 40, 10]),
        NumStyle::Heal => ("title16", [196, 250, 160], [40, 110, 40]),
        NumStyle::Poison => ("title16", [150, 230, 60], [30, 70, 10]),
        NumStyle::Miss => ("text16", [170, 166, 160], [50, 48, 52]),
        NumStyle::Status => ("text16", [200, 190, 255], [50, 40, 90]),
    };
    // never on a leader's health: a number that would cover one goes up over it
    let w = a.fonts[font].width(&n.text) / 2 + 2;
    let mut top = (ny + dy) as i32;
    for _ in 0..3 {
        let hit = bars.iter().find(|b| (nx as i32 - w) < b.2 && (nx as i32 + w) > b.0 && top < b.3 && top + tall > b.1);
        match hit {
            Some(b) => top = b.1 - tall - 2,
            None => break,
        }
    }
    a.fonts[font].draw(cv, &n.text, nx as i32, top, col, Some(edge), Align::Center, fade);
}

/// A bolt of lightning from the attacker to the target, drawn as pixels: it runs out from the staff ball (or the
/// arc's end) in three frames, crackles for four — redrawn every frame, the way lightning flickers — and fades in
/// two. A white core, a blue rim, a dim glow; two short forks.
fn bolt(cv: &mut Image, a: &Assets, rec: &Record, shown: &[crate::playback::Shown], e: &Effect, f: i32) {
    let Some((src, tgt)) = e.link else { return };
    // the Inventor's net: lightning that stands between two golems' chests for a moment, no running out
    let net = e.name == "tesla";
    let k = if net { f - e.start } else { f - (e.start - 3) };
    if !(0..8).contains(&k) {
        return;
    }
    let (Some(s), Some(t)) = (shown.iter().find(|s| s.id == src), shown.iter().find(|s| s.id == tgt)) else { return };
    let spr = sprite(a, rec, src, Pose::Attack, f).map(|(s, _)| s);
    let (mut ex, ey) = spr.and_then(|p| p.emit).unwrap_or((0, -30));
    if rec.units[src].side == 1 {
        ex = -ex;
    }
    let body = sprite(a, rec, tgt, Pose::Idle, f).map(|(p, _)| p.oy).unwrap_or(20);
    let from = if net {
        let own = sprite(a, rec, src, Pose::Idle, f).map(|(p, _)| p.oy).unwrap_or(20);
        (s.x, s.y - own as f32 * 0.5)
    } else {
        (s.x + ex as f32, s.y + ey as f32)
    };
    let to = (t.x, t.y - body as f32 * if net { 0.5 } else { 0.45 });
    let reach = if net { 1.0 } else { ((k + 1) as f32 / 3.0).min(1.0) };
    let fade = if k <= 6 { 1.0 } else { 0.55 };
    // the same bolt while it runs out, a new one each frame after
    let seed = (e.start as u32).wrapping_mul(2654435761) ^ (src as u32 * 97 + tgt as u32 * 13) ^ if k < 3 { 0 } else { k as u32 * 7919 };
    zigzag(cv, from, to, seed, reach, fade, k);
}

/// A bolt of lightning from `from` to `to`, run out to `reach` (0..1) of the way: a jagged white core, a blue rim, a dim
/// glow, two forks once it is all there, the ball it leaves flaring for its first frames (`k`, the bolt's frame).
fn zigzag(cv: &mut Image, from: (f32, f32), to: (f32, f32), seed: u32, reach: f32, fade: f32, k: i32) {
    let mut rnd = seed | 1;
    let mut next = move || {
        rnd ^= rnd << 13;
        rnd ^= rnd >> 17;
        rnd ^= rnd << 5;
        (rnd % 2001) as f32 / 1000.0 - 1.0
    };
    let (dx, dy) = (to.0 - from.0, to.1 - from.1);
    let len = dx.hypot(dy).max(1.0);
    let (px, py) = (-dy / len, dx / len);
    // midpoint displacement: each half bends less than the whole, so the kinks are big and small, never even
    let mut pts = vec![(from.0, from.1, 0.0f32), (to.0, to.1, 1.0f32)];
    let mut amp = (len * 0.12).clamp(3.0, 12.0);
    while pts.len() < 65 && len / (pts.len() as f32) > 5.0 {
        let mut nx = vec![pts[0]];
        for w in pts.windows(2) {
            let off = next() * amp;
            nx.push(((w[0].0 + w[1].0) / 2.0 + px * off, (w[0].1 + w[1].1) / 2.0 + py * off, (w[0].2 + w[1].2) / 2.0));
            nx.push(w[1]);
        }
        pts = nx;
        amp = (amp * 0.62).max(1.6); // the small kinks stay sharp: lightning is jagged all the way down
    }
    let n = pts.len() - 1;
    let mut core: Vec<(i32, i32)> = vec![];
    for w in pts.windows(2) {
        if w[0].2 >= reach {
            break;
        }
        let (mut x1, mut y1) = (w[1].0, w[1].1);
        if w[1].2 > reach {
            let q = (reach - w[0].2) / (w[1].2 - w[0].2);
            x1 = w[0].0 + (w[1].0 - w[0].0) * q;
            y1 = w[0].1 + (w[1].1 - w[0].1) * q;
        }
        line(&mut core, w[0].0, w[0].1, x1, y1);
    }
    let mut forks: Vec<(i32, i32)> = vec![];
    if reach >= 1.0 {
        for _ in 0..2 {
            let j = 1 + ((next() + 1.0) * 0.5 * (n - 2).max(1) as f32) as usize;
            let (bx, by, _) = pts[j.min(pts.len() - 2)];
            let ang = dy.atan2(dx) + next().signum() * (0.45 + 0.4 * next().abs());
            let l = 6.0 + 8.0 * next().abs();
            let mid = (bx + ang.cos() * l * 0.5 + next() * 2.0, by + ang.sin() * l * 0.5 + next() * 2.0);
            line(&mut forks, bx, by, mid.0, mid.1);
            line(&mut forks, mid.0, mid.1, bx + ang.cos() * l, by + ang.sin() * l);
        }
    }
    // rims around the core: one pixel of bright blue, then a dim glow — each pixel painted once
    let mut level: std::collections::HashMap<(i32, i32), u8> = Default::default();
    let glow: i32 = if fade < 1.0 { 0 } else { 2 };
    for &(x, y) in &core {
        for oy in -glow..=glow {
            for ox in -glow..=glow {
                let d = ox.abs() + oy.abs();
                if d > glow {
                    continue;
                }
                let l = (3 - d.min(2)) as u8; // 3 core, 2 rim, 1 glow
                let v = level.entry((x + ox, y + oy)).or_insert(0);
                *v = (*v).max(if d == 0 { 3 } else { l.min(2) });
            }
        }
    }
    for &(x, y) in &forks {
        let v = level.entry((x, y)).or_insert(0);
        *v = (*v).max(2);
    }
    for (&(x, y), &l) in &level {
        let (c, al) = match l {
            3 => ([236, 250, 255, 255], 1.0),
            2 => ([140, 214, 255, 255], 0.9),
            _ => ([60, 120, 240, 255], 0.4),
        };
        cv.blend_px(x, y, c, al * fade);
    }
    // the ball it leaves flares
    if k < 7 {
        for (ox, oy) in [(0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)] {
            cv.blend_px(from.0 as i32 + ox, from.1 as i32 + oy, [236, 250, 255, 255], if ox == 0 && oy == 0 { 1.0 } else { 0.7 });
        }
    }
}

/// The pixels of a line (Bresenham), appended.
fn line(out: &mut Vec<(i32, i32)>, x0: f32, y0: f32, x1: f32, y1: f32) {
    let (mut x, mut y, x1, y1) = (x0.round() as i32, y0.round() as i32, x1.round() as i32, y1.round() as i32);
    let (dx, dy) = ((x1 - x).abs(), -(y1 - y).abs());
    let (sx, sy) = (if x < x1 { 1 } else { -1 }, if y < y1 { 1 } else { -1 });
    let mut err = dx + dy;
    loop {
        out.push((x, y));
        if x == x1 && y == y1 {
            break;
        }
        let e2 = 2 * err;
        if e2 >= dy {
            err += dy;
            x += sx;
        }
        if e2 <= dx {
            err += dx;
            y += sy;
        }
    }
}

fn effect(cv: &mut Image, a: &Assets, e: &Effect, f: i32) {
    if e.link.is_some() {
        return; // a bolt, drawn by bolt()
    }
    if e.name == "sky" {
        // lightning out of the sky straight down on it, a white flare where it lands
        let k = f - e.start;
        if (0..6).contains(&k) {
            let seed = (e.start as u32).wrapping_mul(2654435761) ^ (e.x as u32 * 31) ^ if k < 2 { 0 } else { k as u32 * 7919 };
            zigzag(cv, (e.x + 40.0, e.y - 460.0), (e.x, e.y - 24.0), seed, 1.0, if k < 4 { 1.0 } else { 0.55 }, k + 7);
            cv.glow(e.x, e.y - 20.0, 60.0, [200, 230, 255], 0.7 - 0.1 * k as f32);
        }
        return;
    }
    if let Some(from) = e.from {
        missile(cv, a, e, from, f);
        return;
    }
    let Some(fx) = a.fx.get(e.name) else { return };
    let per = 24.0 / fx.fps; // game frames per effect frame
    let k = ((f - e.start) as f32 / per.max(0.01)) as i32;
    if f < e.start || k >= fx.frames {
        return;
    }
    // the tail of an effect (an explosion's smoke) thins out, so what happens inside it is not hidden for long
    let half = fx.frames as f32 * 0.45;
    let alpha = if (k as f32) < half { 1.0 } else { 1.0 - 0.75 * (k as f32 - half) / (fx.frames as f32 - half) };
    // a sheet drawn facing right, mirrored to face left: its pivot mirrored with it
    let px = if e.flip { fx.w - 1 - fx.pivot.0 } else { fx.pivot.0 };
    cv.blit_region(&fx.img, k * fx.w, 0, fx.w, fx.h, e.x as i32 - px, e.y as i32 - fx.pivot.1, e.flip, alpha);
}

/// Something thrown or shot, on its way from `from` to the effect's point over `FLY` frames: the Sage's fireball
/// (its sheet, turning over as it flies straight), the spitter's gob and the catapult's stone (a few pixels each,
/// on an arc, a speck of a trail behind).
fn missile(cv: &mut Image, a: &Assets, e: &Effect, from: (f32, f32), f: i32) {
    let k = f - e.start;
    if !(0..FLY).contains(&k) {
        return;
    }
    let t = k as f32 / FLY as f32;
    let arc = if e.name == "fireball" { 0.0 } else { 34.0 * 4.0 * t * (1.0 - t) };
    let (x, y) = (from.0 + (e.x - from.0) * t, from.1 + (e.y - from.1) * t - arc);
    match e.name {
        "fireball" => {
            if let Some(fx) = a.fx.get("fireball") {
                let n = ((k as f32 * fx.fps / 24.0) as i32).rem_euclid(fx.frames);
                let px = if e.flip { fx.w - 1 - fx.pivot.0 } else { fx.pivot.0 };
                cv.blit_region(&fx.img, n * fx.w, 0, fx.w, fx.h, x as i32 - px, y as i32 - fx.pivot.1, e.flip, 1.0);
                cv.glow(x, y, 26.0, [255, 138, 42], 0.5);
            }
        }
        _ => {
            // a gob of green spit, or a grey stone: a dark rim, a body, a light fleck on its top left
            let (rim, body, lit) = if e.name == "gob" {
                ([28, 48, 16, 255], [106, 174, 28, 255], [220, 255, 106, 255])
            } else {
                ([24, 20, 28, 255], [96, 90, 104, 255], [160, 154, 168, 255])
            };
            let (xi, yi) = (x as i32, y as i32);
            let (tx, ty) = ((from.0 + (e.x - from.0) * (t - 0.12).max(0.0)) as i32, (y + 3.0) as i32);
            cv.fill(tx, ty, 2, 2, [body[0], body[1], body[2], 140]);
            cv.fill(xi - 2, yi - 2, 5, 5, rim);
            cv.fill(xi - 1, yi - 1, 3, 3, body);
            cv.fill(xi - 1, yi - 1, 1, 1, lit);
        }
    }
}

#[allow(clippy::too_many_arguments)]
fn button(cv: &mut Image, a: &Assets, x0: i32, x1: i32, y: i32, lit: bool, hot: bool, text: &str, key: &str, alpha: f32, keys: f32) {
    let p = &a.ui[if lit { "button_amber_22" } else { "button_chitin_22" }];
    // the kit's 22 px button: 14 px of pad either side, the hexagon's points ~12 px, the middle repeats; under the
    // cursor it is lifted toward white
    let mut b = Image::clear((x1 - x0) + 28, p.img.h);
    b.three_slice(&p.img, 0, 0, (x1 - x0) + 28, 26, 26, (110, 116));
    if hot {
        b.lighten(0.22);
    }
    cv.blit(&b, x0 - 14, y, false, alpha);
    a.fonts["text16"].draw(cv, text, (x0 + x1) / 2, y + 7, if lit { DARK } else { INK }, if lit { None } else { Some([16, 12, 16]) }, Align::Center, alpha);
    if keys > 0.0 {
        keycap(cv, &a.fonts["text16"], (x0 + x1) / 2, y + 29, key, alpha * keys);
    }
}

fn keycap(cv: &mut Image, font: &Font, cx: i32, y: i32, t: &str, alpha: f32) {
    let w = font.width(t) + 12;
    let x = cx - w / 2;
    let a = (alpha * 255.0) as u8;
    cv.fill(x, y, w, 22, [26, 20, 32, a]);
    cv.fill(x + 1, y + 1, w - 2, 17, [74, 64, 86, a]);
    cv.fill(x + 2, y + 1, w - 4, 1, [114, 104, 126, a]);
    font.draw(cv, t, cx, y + 1, INK, None, Align::Center, alpha);
}

/// A leader's health, small: ten notches in a dark frame (lit in the side's colour, bevelled), a little crown
/// before them. Centred on (cx, y); about 52 px wide.
fn meter(cv: &mut Image, cx: i32, y: i32, lit: i32, swarm: bool) {
    let (hi, mid, lo) = if swarm {
        ([255, 150, 120, 255], [214, 64, 44, 255], [120, 26, 22, 255])
    } else {
        ([255, 226, 140, 255], [226, 160, 52, 255], [130, 82, 20, 255])
    };
    let x0 = cx - 20;
    cv.fill(x0 - 1, y - 3, 42, 7, [14, 10, 18, 255]);
    for k in 0..10 {
        let x = x0 + k * 4;
        if k < lit {
            cv.fill(x, y - 2, 3, 1, hi);
            cv.fill(x, y - 1, 3, 2, mid);
            cv.fill(x, y + 1, 3, 1, lo);
        } else {
            cv.fill(x, y - 2, 3, 4, [52, 44, 60, 255]);
        }
    }
    // the crown: three points on a band, gold, outlined
    let c0 = x0 - 10;
    cv.fill(c0 - 1, y - 4, 9, 8, [14, 10, 18, 255]);
    for (dx, dy) in [(0, -3), (3, -3), (6, -3)] {
        cv.fill(c0 + dx, y + dy, 1, 1, [255, 226, 140, 255]);
    }
    cv.fill(c0, y - 2, 7, 1, [255, 226, 140, 255]);
    cv.fill(c0, y - 1, 7, 2, [226, 160, 52, 255]);
    cv.fill(c0, y + 1, 7, 1, [130, 82, 20, 255]);
}

/// The whole battle on one 960×540 canvas (the debug pictures: --shot, --strip, --frames): the whole field, halved
/// (each pixel the mean of four), the interface over it.
pub fn draw(cv: &mut Image, a: &Assets, rec: &Record, sparks: &(Vec<Number>, Vec<Effect>), view: &View) {
    let mut field = Image::new(FW, FH);
    draw_field(&mut field, a, rec, sparks, view);
    for y in 0..cv.h.min(FH / 2) {
        for x in 0..cv.w.min(FW / 2) {
            let p = |dx: i32, dy: i32| field.px[((2 * y + dy) * FW + 2 * x + dx) as usize];
            let q = [p(0, 0), p(1, 0), p(0, 1), p(1, 1)];
            let m = |k: usize| ((q[0][k] as u32 + q[1][k] as u32 + q[2][k] as u32 + q[3][k] as u32 + 2) / 4) as u8;
            cv.px[(y * cv.w + x) as usize] = [m(0), m(1), m(2), 255];
        }
    }
    draw_hud(cv, a, rec, view);
}

/// The field: the ground, the units, their health, the effects and numbers; dimmed at the end.
pub fn draw_field(cv: &mut Image, a: &Assets, rec: &Record, sparks: &(Vec<Number>, Vec<Effect>), view: &View) {
    let total = rec.frames();
    let f = (view.frame as i32).min(total - 1);
    // the ground (an ordinary fight's, an elite's, a boss's), opaque and the field's own size: copied whole (a blend
    // of two million pixels is most of a frame)
    let ground = rec.ground.checked_sub(1).and_then(|k| a.grounds.get(k)).and_then(|g| g.as_ref()).unwrap_or(&a.ground);
    if (cv.w, cv.h) == (ground.w, ground.h) {
        cv.px.copy_from_slice(&ground.px);
    } else {
        cv.blit(ground, 0, 0, false, 1.0);
    }
    ground_layers(cv, rec, (f / FR) as usize);
    burning_ground(cv, a, rec, (f / FR) as usize, view.frame);
    // the units, in depth order. The small ones of a cell stand as one pack: no more than three bodies show — one in
    // front, two peeking out from behind it — with one shadow, and a row of dots under the pack when there are more
    // (a dot a body, no number to translate); a hidden one's swing or hit is shown by the body standing for it. The
    // dead lie each on a place of their own (so a corpse never shifts when the living come and go).
    let ff = view.frame.min((total - 1) as f32);
    let shown = rec.shown(ff);
    let ms = rec.moments((f / FR) as usize);
    let lying_of = |o: &crate::playback::Shown| o.pose == Pose::Dead && o.dead_at.map(|k| ff - k as f32 >= 6.0).unwrap_or(true);
    let small = |id: usize| rec.units[id].fp == 1 && !rec.units[id].leader && !rec.units[id].cloud && !rec.units[id].ghost && !rec.units[id].wall;
    // a pack: the small ones of one side, one size, in one cell (big ones never stand among small ones)
    type PackKey = ((i32, i32), u8, u32);
    let key = |id: usize, cell: (i32, i32)| -> PackKey { (cell, rec.units[id].side, rec.units[id].size) };
    let mut packs: std::collections::HashMap<PackKey, Vec<usize>> = Default::default();
    for o in &shown {
        if small(o.id) && !lying_of(o) {
            packs.entry(key(o.id, o.cell)).or_default().push(o.id);
        }
    }
    struct Placed<'a> {
        y: f32,
        x: f32,
        s: &'a crate::playback::Shown,
        lying: bool,
        stands_for: Vec<usize>,
    }
    let mut placed: Vec<Placed> = vec![];
    let mut badges: Vec<(f32, f32, usize)> = vec![];
    for s in &shown {
        let (mut x, mut y) = (s.x, s.y);
        let lying = lying_of(s);
        let mut stands_for = vec![s.id];
        if small(s.id) {
            let dead_slot = SLOTS[s.id % 4];
            if lying {
                x += dead_slot.0;
                y += dead_slot.1;
            } else {
                let pack = &packs[&key(s.id, s.cell)];
                let rank = pack.iter().position(|&i| i == s.id).unwrap_or(0);
                let place = PACK[rank % 3];
                if let Some(k) = s.dead_at {
                    // the fall: out of the pack to its own place on the ground
                    let u = ((ff - k as f32 - 3.0) / 3.0).clamp(0.0, 1.0);
                    x += place.0 + (dead_slot.0 - place.0) * u;
                    y += place.1 + (dead_slot.1 - place.1) * u;
                } else {
                    if rank >= 3 {
                        continue; // hidden in the pack: a dot under it, its moves shown by the body in front
                    }
                    let alive: Vec<usize> = pack.iter().copied().filter(|&i| shown.iter().any(|o| o.id == i && o.dead_at.is_none())).collect();
                    stands_for = alive.iter().copied().enumerate().filter(|(r, _)| r % 3 == rank).map(|(_, i)| i).collect();
                    if !stands_for.contains(&s.id) {
                        stands_for.insert(0, s.id);
                    }
                    x += place.0;
                    y += place.1;
                    if rank == 0 && alive.len() > 3 {
                        badges.push((x, y, alive.len()));
                    }
                }
            }
        }
        placed.push(Placed { y, x, s, lying, stands_for });
    }
    placed.sort_by(|p, q| (!p.lying).cmp(&!q.lying).then(p.y.partial_cmp(&q.y).unwrap()));
    let at = |id: usize| shown.iter().find(|o| o.id == id).map(|o| (o.x, o.y));
    // a death is drawn again over the fire and smoke: the flash of the killed and the dust of its fall must show
    // even inside a blast
    let mut over: Vec<Dying> = vec![];
    // the standing bodies as drawn: where their head is, what is on them (all they stand for), whether the glyph row
    // goes over them (a pack has one, over its front body; a leader's sits above his health meter)
    let mut marked: Vec<Marks> = vec![];
    for p in &placed {
        let (x, y, s, lying) = (p.x, p.y, p.s, p.lying);
        let info = &rec.units[s.id];
        // the body's own life, and the swing or the hit of any it stands for
        let mut anim = animate(rec, &ms, s, ff, &at);
        for &id in p.stands_for.iter().filter(|&&i| i != s.id) {
            let Some(o) = shown.iter().find(|o| o.id == id) else { continue };
            let other = animate(rec, &ms, o, ff, &at);
            if other.pose == Pose::Attack && anim.pose != Pose::Attack {
                anim.pose = Pose::Attack;
                anim.dx = other.dx;
                anim.dy = other.dy;
            }
            anim.flash = anim.flash.max(other.flash);
        }
        if info.cloud {
            // no body: a swirl of specks, thinning as it is killed
            let k = match s.dead_at {
                Some(d) => (1.0 - (ff - d as f32) / 6.0).clamp(0.0, 1.0),
                None if lying => 0.0,
                None => 1.0,
            };
            if k > 0.0 {
                midges(cv, x, y, ff, s.id, k);
            }
            continue;
        }
        let Some((spr, name)) = sprite(a, rec, s.id, anim.pose, f) else { continue };
        // a body that has no broken pose lies as it stood, dark (the drawing below darkens the dead)
        let big = info.fp >= 2 || info.machine;
        if info.wall && !lying && anim.pose != Pose::Dead {
            cv.shadow(x + 2.0, y, 26.0, 4.0);
        } else if !lying && anim.pose != Pose::Dead {
            let pack = small(s.id) && packs.get(&key(s.id, s.cell)).map(|v| v.len() > 1).unwrap_or(false);
            let rank0 = small(s.id) && packs.get(&key(s.id, s.cell)).map(|v| v.first() == Some(&s.id)).unwrap_or(true);
            if !small(s.id) || !pack {
                cv.shadow(x + 2.0, y, if big { 40.0 } else { 14.0 }, if big { 7.0 } else { 3.0 });
            } else if rank0 {
                cv.shadow(x + 1.0, y - 2.0, 30.0, 6.0); // one shadow under the whole pack
            }
        }
        let flip = info.side == 1;
        let ox = if flip { spr.img.w - 1 - spr.ox } else { spr.ox };
        let (sx, sy) = ((x + anim.dx).round() as i32 - ox, (y + anim.dy).round() as i32 - spr.oy);
        // the modules on a golem, each a layer over its body in the same pose (sprites/mod/…), drawn as the body is
        let mods: Vec<(&crate::assets::Sprite, i32, i32)> = match name.rsplit_once('_') {
            Some((prefix, pose)) if info.machine && !info.mods.is_empty() => info
                .mods
                .iter()
                .filter_map(|(key, lvl)| a.sprites.get(&format!("mod/{prefix}_{key}_{lvl}_{pose}")))
                .map(|o| {
                    let oox = if flip { o.img.w - 1 - o.ox } else { o.ox };
                    (o, (x + anim.dx).round() as i32 - oox, (y + anim.dy).round() as i32 - o.oy)
                })
                .collect(),
            _ => vec![],
        };
        if anim.pose == Pose::Dead {
            // the dead lie darker and greyer than the living, so a heap of them does not read as a living swarm; the
            // longer dead, the deeper they sink into the ground's colour — in steps, opaque, no see-through
            let age = rec.died_at[s.id].map(|k| (f - k) / FR).unwrap_or(0);
            let (mul, grey, sink) = match age {
                0 => (0.62, 0.55, 0.0),
                1 => (0.52, 0.65, 0.2),
                2 => (0.46, 0.7, 0.4),
                _ => (0.42, 0.75, 0.55),
            };
            cv.blit_shade_to(&spr.img, sx, sy, flip, mul, grey, [42, 34, 50], sink);
            for (o, ox, oy) in &mods {
                cv.blit_shade_to(&o.img, *ox, *oy, flip, mul, grey, [42, 34, 50], sink);
            }
        } else if info.ghost {
            // a ghost of the mirage: see-through and psi-violet, wavering
            let waver = 0.42 + 0.12 * (ff * 0.4 + s.id as f32).sin();
            cv.blit_tint_faded(&spr.img, sx, sy, flip, [196, 160, 255], 0.55, waver);
        } else if anim.flash > 0.0 {
            cv.blit_tint(&spr.img, sx, sy, flip, [255, 250, 236], anim.flash);
            for (o, ox, oy) in &mods {
                cv.blit_tint(&o.img, *ox, *oy, flip, [255, 250, 236], anim.flash);
            }
        } else if info.puppet {
            // a machine worked by larvae: a sickly green film over the metal, and the grubs themselves writhing in
            // its seams, at the chest and the hip, turning over now and then
            cv.blit_tint(&spr.img, sx, sy, flip, [130, 196, 70], 0.32);
            for (n, (fx_, fy_)) in [(0.38f32, 0.34f32), (0.58, 0.56), (0.44, 0.74)].iter().enumerate() {
                let pose = if ((ff as i32 / 5) + n as i32 + s.id as i32) % 2 == 0 { "Личинка_walk0" } else { "Личинка_walk1" };
                if let Some(g) = a.sprites.get(pose) {
                    let gx = sx + (spr.img.w as f32 * fx_) as i32 - g.img.w / 2;
                    let gy = sy + (spr.img.h as f32 * fy_) as i32 - g.img.h / 2 + if (ff as i32 / 3 + n as i32) % 3 == 0 { -1 } else { 0 };
                    cv.blit(&g.img, gx, gy, (n % 2 == 0) ^ flip, 1.0);
                }
            }
        } else {
            cv.blit(&spr.img, sx, sy, flip, 1.0);
            for (o, ox, oy) in &mods {
                cv.blit(&o.img, *ox, *oy, flip, 1.0);
            }
        }
        if let Some(k) = s.dead_at.filter(|_| !info.ghost) {
            over.push(Dying { sx, sy, flip, flash: anim.flash, x, y, golem: info.machine, big, t: ff - k as f32, name });
        } else if !lying && anim.pose != Pose::Dead && !info.ghost {
            let body = p.stands_for.iter().fold(0, |m, &id| m | rec.state_at(id, f).flags);
            let pack = small(s.id).then(|| packs.get(&key(s.id, s.cell))).flatten();
            // a pack's row goes over its first living body (the one in front may be falling)
            let bearer = pack.and_then(|v| v.iter().copied().find(|&i| shown.iter().any(|o| o.id == i && o.dead_at.is_none())));
            let (row, all) = match pack {
                Some(v) if bearer == Some(s.id) => (true, v.iter().fold(0, |m, &id| m | rec.state_at(id, f).flags)),
                Some(_) => (false, 0),
                None => (true, body),
            };
            marked.push(Marks { x: x + anim.dx, top: sy as f32, foot: y + anim.dy, h: spr.img.h, body, row: if row { all } else { 0 }, leader: info.leader, id: s.id });
        }
    }
    // fire on the burning bodies: tongues licking up from the lower half, two on a big one, and their light
    if let Some(fx) = a.fx.get("burn-body") {
        for m in marked.iter().filter(|m| m.body & S_BURN != 0) {
            let spots: &[f32] = if m.h > 40 { &[-0.22, 0.2] } else { &[0.0] };
            for (n, &dx) in spots.iter().enumerate() {
                let k = ((ff * fx.fps / 24.0) as i32 + m.id as i32 * 3 + n as i32 * 5).rem_euclid(fx.frames);
                let bx = m.x + dx * m.h as f32 * 0.8;
                let by = m.foot - m.h as f32 * 0.22;
                cv.blit_region(&fx.img, k * fx.w, 0, fx.w, fx.h, bx as i32 - fx.pivot.0, by as i32 - fx.pivot.1, false, 1.0);
                cv.glow(bx, by - fx.h as f32 * 0.4, fx.h as f32 * 1.3, [240, 138, 32], 0.35);
            }
        }
    }
    // how many a pack holds: a dot a body, under it
    for &(x, y, n) in &badges {
        let w = n as i32 * 3 + 1;
        let (x0, y0) = (x as i32 - w / 2, y as i32 + 5);
        cv.fill(x0, y0, w, 4, [14, 10, 18, 255]);
        for k in 0..n as i32 {
            cv.fill(x0 + 1 + k * 3, y0 + 1, 2, 2, [232, 220, 178, 255]);
        }
    }
    // the sky over it: a storm darkens it and rains on it, the night leaves only what burns or glows to be seen
    match rec.weather {
        sim::model::Weather::Storm => {
            let flash = ms.iter().any(|m| matches!(m.ev, Event::Strike { .. }) && (0..3).contains(&(f - m.frame)));
            storm(cv, ff, flash);
        }
        sim::model::Weather::Night => {
            let mut lights: Vec<(f32, f32, f32)> = vec![];
            for m in &marked {
                if m.body & S_BURN != 0 {
                    lights.push((m.x, m.foot - m.h as f32 * 0.4, 120.0));
                }
                if rec.units[m.id].name.starts_with("Светляк") {
                    lights.push((m.x, m.foot - 10.0, 80.0));
                }
            }
            let round = &rec.rounds[(f / FR) as usize];
            for (c, _) in round.flames.iter().enumerate().filter(|(_, &v)| v > 0) {
                let cols = sim::battle::W;
                lights.push((X0 + ((c as i32 % cols) as f32 + 0.5) * CW, Y0 + ((c as i32 / cols) as f32 + 0.5) * CH, 100.0));
            }
            for e in &sparks.1 {
                let bright = matches!(e.name, "fireball" | "small-explosion" | "fire-breath" | "zap-hit" | "mana-burst" | "muzzle-shotgun" | "heal" | "tesla" | "bolt");
                if bright && (e.start..e.start + 10).contains(&f) {
                    lights.push((e.x, e.y - 10.0, 110.0));
                }
            }
            night(cv, &lights);
        }
        _ => {}
    }
    // the leaders' health, the crown by it
    let mut bars = vec![];
    for (id, info) in rec.units.iter().enumerate() {
        if !info.leader {
            continue;
        }
        let st = rec.state_at(id, f);
        if !st.alive {
            continue;
        }
        if let Some(s) = shown.iter().find(|s| s.id == id) {
            let top = sprite(a, rec, id, s.pose, f).map(|(sp, _)| sp.oy).unwrap_or(40);
            let lit = ((st.hp.max(0) * 10 + info.max_hp - 1) / info.max_hp.max(1)).clamp(0, 10);
            // over his head; at the very edge it slides just enough to stay on the screen
            let (cx, cy) = ((s.x as i32).clamp(32, FW - 22), (s.y as i32 - top - 8).max(44));
            meter(cv, cx, cy, lit, !info.machine);
            bars.push((cx - 32, cy - 5, cx + 22, cy + 5));
        }
    }
    for e in &sparks.1 {
        bolt(cv, a, rec, &shown, e, f);
    }
    for e in &sparks.1 {
        effect(cv, a, e, f);
    }
    for d in &over {
        if d.t < 3.0 {
            if let Some(spr) = a.sprites.get(&d.name) {
                cv.blit_tint(&spr.img, d.sx, d.sy, d.flip, [255, 250, 236], d.flash);
            }
        }
        dust(cv, d.x, d.y, d.t - 3.0, d.golem, d.big, (d.x * 7.0 + d.y) as usize);
    }
    for n in &sparks.0 {
        number(cv, a, rec, n, f, &bars);
    }
    // the glyphs of what is on them, in a row over the head (no more than four: the worst first), over the numbers:
    // a number flies off, the state stays
    for m in marked.iter().filter(|m| m.row != 0) {
        let keys: Vec<&str> = STATUS_GLYPHS.iter().filter(|(bit, _)| m.row & bit != 0).map(|&(_, k)| k).take(4).collect();
        let rects: Vec<(&Image, [i32; 4])> = keys
            .iter()
            .filter_map(|k| a.icons.get(*k).and_then(|(atlas, r)| a.atlases.get(atlas).map(|img| (img, *r))))
            .collect();
        if rects.is_empty() {
            continue;
        }
        let w: i32 = rects.iter().map(|(_, r)| r[2] + 2).sum::<i32>() - 2;
        let gh = rects.iter().map(|(_, r)| r[3]).max().unwrap_or(9);
        // over a leader the health meter stands first
        let top = if m.leader { m.top - 22.0 } else { m.top - 4.0 };
        let mut gx = m.x as i32 - w / 2;
        for (img, r) in rects {
            cv.blit_region(img, r[0], r[1], r[2], r[3], gx, top as i32 - gh + (gh - r[3]) / 2, false, 1.0);
            gx += r[2] + 2;
        }
    }
    let end = view.frame as i32 - (total - 1);
    if end > 0 {
        cv.dim(0, 0, cv.w, cv.h, 1.0 - 0.5 * (end as f32 / 12.0).min(1.0));
    }
}

/// The interface over the field: the wing (the tug of war, the counts, the turn, the speed buttons with their keys)
/// and at the end the plate.
pub fn draw_hud(cv: &mut Image, a: &Assets, rec: &Record, view: &View) {
    let total = rec.frames();
    let f = (view.frame as i32).min(total - 1);
    // the wing: the swarm against the Foundry, the turn, the speed
    cv.blit(&a.ui["wing_battle_960"].img, 0, 0, false, 1.0);
    // a midge cloud is no body of the army
    let alive = |side: u8| {
        rec.units.iter().enumerate().filter(|(i, u)| u.side == side && !u.cloud && !u.ghost && !u.puppet && !u.wall && rec.state_at(*i, f).alive && rec.state_at(*i, f).present).count()
    };
    // the swarm's count on the left, the Foundry's leader and its golems on the right, whichever side each is on
    let swarm = if rec.units.iter().any(|u| u.side == 1 && !u.machine) { 1 } else { 0 };
    let forge = 1 - swarm;
    let hp = |side: u8| -> f32 {
        let (mut now, mut all) = (0.0, 0.0);
        for (i, u) in rec.units.iter().enumerate() {
            if u.side == side && !u.cloud && !u.ghost && !u.puppet && !u.wall {
                all += u.max_hp as f32;
                let s = rec.state_at(i, f);
                if s.alive && s.present {
                    now += s.hp.max(0) as f32;
                }
            }
        }
        now / all.max(1.0)
    };
    let (sw, fo) = (hp(swarm), hp(forge));
    let share = if sw + fo > 0.0 { sw / (sw + fo) } else { 0.5 };
    let title = &a.fonts["title16"];
    title.draw(cv, &crate::text::tf("hud.swarm", &[("n", &alive(swarm))]), 16, 8, ACID, Some(ACID_EDGE), Align::Left, 1.0);
    // Мимикрия: the weapon the swarm took up from the last machine it broke, under its count — the module it came from
    let took = rec.rounds.get((f / FR).max(0) as usize).map(|r| r.mimic[swarm as usize]).unwrap_or(0);
    use sim::battle::{MIMIC_BLUNT, MIMIC_EDGE, MIMIC_FIRE, MIMIC_MEND, MIMIC_SHELL, MIMIC_SHOCK};
    let weapon = [(MIMIC_SHOCK, "module/volt"), (MIMIC_FIRE, "module/fire"), (MIMIC_SHELL, "module/plates"), (MIMIC_BLUNT, "module/mortar"),
        (MIMIC_MEND, "module/repair"), (MIMIC_EDGE, "module/blades")]
    .iter()
    .find(|(bit, _)| took & bit != 0)
    .map(|&(_, k)| k);
    if let Some((atlas, r)) = weapon.and_then(|k| a.icons.get(k)) {
        if let Some(img) = a.atlases.get(atlas) {
            cv.fill(14, 38, r[2] + 6, r[3] + 6, [20, 30, 14, 220]);
            cv.fill(15, 39, r[2] + 4, 1, [122, 176, 64, 255]);
            cv.blit_region(img, r[0], r[1], r[2], r[3], 17, 41, false, 1.0);
        }
    }
    let (ts, tf) = (&a.ui["tug_swarm"].img, &a.ui["tug_foundry"].img);
    let cut = (share * ts.w as f32) as i32;
    cv.blit_region(ts, 0, 0, cut, ts.h, 144, 10, false, 1.0);
    cv.blit_region(tf, cut, 0, tf.w - cut, tf.h, 144 + cut, 10, false, 1.0);
    for j in 0..ts.h {
        let x = 144 + cut + if (j / 2) % 2 == 0 { 2 } else { -2 };
        cv.blend_px(x, 10 + j, [255, 244, 200, 255], 1.0);
    }
    let text = &a.fonts["text16"];
    let nf = rec.units.iter().filter(|u| u.side == forge && !u.wall).count();
    let leader = rec.units.iter().find(|u| u.side == forge && u.leader).map(|u| u.name.as_str()).unwrap_or("Литейщик");
    // the leader's name and his army's count, short enough to leave room for the turn before the buttons
    text.draw(cv, &format!("{leader} {}/{nf}", alive(forge)), 530, 9, [214, 196, 150], Some([16, 12, 16]), Align::Left, 1.0);
    let turn = (f / FR + 1).min(rec.rounds.len() as i32);
    text.draw(cv, &crate::text::tf("hud.turn", &[("n", &turn)]), 728, 9, MUTED, Some([16, 12, 16]), Align::Right, 1.0);
    // the sky and the elite's face, under the turn
    let mut under = vec![];
    if rec.weather != sim::model::Weather::Clear {
        under.push((crate::text::t(&format!("weather.{}", rec.weather.key())), [150, 190, 255]));
    }
    if rec.affix != sim::model::Affix::None {
        under.push((crate::text::t(&format!("affix.{}", rec.affix.key())), [255, 196, 110]));
    }
    if !under.is_empty() {
        let line = under.iter().map(|(w, _)| w.as_str()).collect::<Vec<_>>().join(" · ");
        let col = under[0].1;
        text.draw(cv, &line, 712, 30, col, Some([16, 12, 16]), Align::Right, 1.0);
    }
    let hot = |b: Button| view.hover == Some(b);
    // the keys show under a button only while the cursor is on it, and for the first seconds of a battle (to teach
    // them) — not over the field all the time
    let first = (1.0 - (view.frame - 72.0) / 24.0).clamp(0.0, 1.0);
    let keys = |b: Button| if hot(b) { 1.0 } else { first };
    button(cv, a, 736, 784, 2, view.paused, hot(Button::Pause), "II", "Пробел", 1.0, keys(Button::Pause));
    button(cv, a, 790, 838, 2, !view.paused, hot(Button::Speed), &format!("×{}", view.speed), "Tab", 1.0, keys(Button::Speed));
    button(cv, a, 844, 952, 2, false, hot(Button::ToEnd), "в конец »", "End", 1.0, keys(Button::ToEnd));
    // the end: the plate across the dimmed field
    let end = view.frame as i32 - (total - 1);
    if end > 0 {
        let k = (end as f32 / 12.0).min(1.0);
        // the plate as the player sees it: side 0 is the player's in a run; the demo is watched from the swarm's side
        let mine = if view.end.is_some() { 0 } else { 1 };
        let win = rec.outcome.winner == Some(mine);
        let p = &a.ui[if win { "end_plate_win" } else { "end_plate_lose" }];
        let dy = ((1.0 - k) * -40.0) as i32;
        cv.blit(&p.img, W / 2 - p.img.w / 2, H / 2 - 60 + dy, false, k);
        let big = &a.fonts["title24"];
        // both armies gone at once, or the rounds run out: a draw, on the grey plate
        let (t, c, e) = match rec.outcome.winner {
            Some(w) if w == mine => (crate::text::t("hud.win"), ACID, ACID_EDGE),
            Some(_) => (crate::text::t("hud.lose"), [176, 178, 186], [56, 58, 68]),
            None => (crate::text::t("hud.draw"), [176, 178, 186], [56, 58, 68]),
        };
        big.draw(cv, &t, W / 2, H / 2 - 30 + dy, c, Some(e), Align::Center, k);
        // the demo tells its seed (to replay a battle); a run's battle only how long it was
        let sub = if view.end.is_some() {
            crate::text::tf("hud.rounds", &[("n", &rec.rounds.len())])
        } else {
            crate::text::tf("hud.sub", &[("n", &rec.rounds.len()), ("seed", &rec.seed)])
        };
        text.draw(cv, &sub, W / 2, H / 2 + 46 + dy, INK, Some([16, 12, 16]), Align::Center, k);
        let (label, key) = view.end.clone().unwrap_or_else(|| (crate::text::t("hud.new"), "R".to_string()));
        button(cv, a, W / 2 - 70, W / 2 + 70, PLATE_BUTTON_Y + dy, true, hot(Button::NewBattle), &label, &key, k, 1.0);
    }
}
