//! A frame of the demo: the field with the units in depth order, the effects and numbers over them, the swarm's
//! thin wing on top (the tug of war, the counts, the turn, the speed buttons with their keys), the leaders' health
//! with the crown, and at the end the plate across the dimmed field.

use crate::assets::{Align, Assets, Font};
use crate::gfx::Image;
use crate::playback::{Effect, Number, NumStyle, Pose, Record, FR};
use sim::Event;

pub const W: i32 = 960;
pub const H: i32 = 540;

pub struct View {
    pub frame: f32,
    pub speed: u32,
    pub paused: bool,
    /// The button under the cursor, lit a little: one of the `Button`s.
    pub hover: Option<Button>,
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
    match n {
        "Мудрец" | "Орудие" | "Механик" | "Изобретатель" => {
            let p = match pose {
                Pose::Idle => "idle".to_string(),
                Pose::Attack => "attack".to_string(),
                Pose::Dead => "broken".to_string(),
                Pose::Walk(k) => format!("walk{}", (k / 2) % 4), // four frames, each held two counts
            };
            format!("{n}_{p}")
        }
        "Пожиратель" => {
            let st = rec.state_at(id, f).growth.min(2);
            let p = match pose {
                Pose::Idle => "idle".to_string(),
                Pose::Attack => "attack".to_string(),
                Pose::Dead => "dead".to_string(),
                Pose::Walk(k) => format!("walk{}", (k / 2) % 2),
            };
            format!("Пожиратель_{st}_{p}")
        }
        _ => {
            let p = match pose {
                Pose::Idle => "idle".to_string(),
                Pose::Attack => "attack".to_string(),
                Pose::Dead => "dead".to_string(),
                Pose::Walk(k) => format!("walk{}", k % 2), // the small ones scuttle: a frame every count
            };
            let base = if n.starts_with("Кузнечик") { "Кузнечик (рабочая)" } else if n.contains("солдат") { "Муравей (солдат)" } else { "Муравей (рабочая)" };
            format!("{base}_{}_{p}", id % 4)
        }
    }
}

const SLOTS: [(f32, f32); 4] = [(-11.0, -6.0), (11.0, -7.0), (-10.0, 8.0), (12.0, 7.0)];

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
        let slow = info.side == 0 || info.fp >= 2;
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
    let head = a.sprites.get(&sprite_name(rec, n.t, Pose::Idle, n.start)).map(|s| s.oy).unwrap_or(40);
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
    let k = f - (e.start - 3);
    if !(0..8).contains(&k) {
        return;
    }
    let (Some(s), Some(t)) = (shown.iter().find(|s| s.id == src), shown.iter().find(|s| s.id == tgt)) else { return };
    let spr = a.sprites.get(&sprite_name(rec, src, Pose::Attack, f));
    let (mut ex, ey) = spr.and_then(|p| p.emit).unwrap_or((0, -30));
    if rec.units[src].side == 1 {
        ex = -ex;
    }
    let body = a.sprites.get(&sprite_name(rec, tgt, Pose::Idle, f)).map(|p| p.oy).unwrap_or(20);
    let from = (s.x + ex as f32, s.y + ey as f32);
    let to = (t.x, t.y - body as f32 * 0.45);
    let reach = ((k + 1) as f32 / 3.0).min(1.0);
    let fade = if k <= 6 { 1.0 } else { 0.55 };
    // the same bolt while it runs out, a new one each frame after
    let seed = (e.start as u32).wrapping_mul(2654435761) ^ (src as u32 * 97 + tgt as u32 * 13) ^ if k < 3 { 0 } else { k as u32 * 7919 };
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
    let fx = &a.fx[e.name];
    let per = 24.0 / fx.fps; // game frames per effect frame
    let k = ((f - e.start) as f32 / per.max(0.01)) as i32;
    if f < e.start || k >= fx.frames {
        return;
    }
    cv.blit_region(&fx.img, k * fx.w, 0, fx.w, fx.h, e.x as i32 - fx.pivot.0, e.y as i32 - fx.pivot.1, false, 1.0);
}

#[allow(clippy::too_many_arguments)]
fn button(cv: &mut Image, a: &Assets, x0: i32, x1: i32, y: i32, lit: bool, hot: bool, text: &str, key: &str, alpha: f32) {
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
    keycap(cv, &a.fonts["text16"], (x0 + x1) / 2, y + 29, key, alpha);
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

fn meter(cv: &mut Image, a: &Assets, cx: i32, y: i32, lit: i32, gem: &str) {
    for k in 0..10 {
        let p = &a.ui[if k < lit { gem } else { "scale_dim" }];
        let x = cx - 46 + k * 9;
        cv.blit(&p.img, x - p.img.w / 2 + 4, y - p.img.h / 2, false, 1.0);
    }
    let c = &a.ui["crown"];
    cv.blit(&c.img, cx - 64, y - 10, false, 1.0);
}

pub fn draw(cv: &mut Image, a: &Assets, rec: &Record, sparks: &(Vec<Number>, Vec<Effect>), view: &View) {
    draw_field(cv, a, rec, sparks, view);
    draw_hud(cv, a, rec, view);
}

/// The field: the ground, the units, their health, the effects and numbers; dimmed at the end.
pub fn draw_field(cv: &mut Image, a: &Assets, rec: &Record, sparks: &(Vec<Number>, Vec<Effect>), view: &View) {
    let total = rec.frames();
    let f = (view.frame as i32).min(total - 1);
    cv.blit(&a.ground, 0, 0, false, 1.0);
    // the units, in depth order; small ones sharing a cell spread over its four places — the living by their order
    // in the cell, the dead each on a place of its own (so a corpse never shifts when the living come and go)
    let ff = view.frame.min((total - 1) as f32);
    let shown = rec.shown(ff);
    let ms = rec.moments((f / FR) as usize);
    let mut placed = vec![];
    for s in &shown {
        let info = &rec.units[s.id];
        let pos = |s: &crate::playback::Shown| (s.x, s.y);
        let (mut x, mut y) = pos(s);
        let lying = s.pose == Pose::Dead && s.dead_at.map(|k| ff - k as f32 >= 6.0).unwrap_or(true);
        if info.fp == 1 && !info.leader {
            let rank = shown
                .iter()
                .filter(|o| o.id < s.id && o.cell == s.cell && rec.units[o.id].side == info.side && rec.units[o.id].fp == 1)
                .filter(|o| !(o.pose == Pose::Dead && o.dead_at.map(|k| ff - k as f32 >= 6.0).unwrap_or(true)))
                .count();
            let alive_slot = SLOTS[rank % 4];
            let dead_slot = SLOTS[s.id % 4];
            let (dx, dy) = if lying {
                dead_slot
            } else if let Some(k) = s.dead_at {
                // the fall: from its place among the living to its own place on the ground
                let u = ((ff - k as f32 - 3.0) / 3.0).clamp(0.0, 1.0);
                (alive_slot.0 + (dead_slot.0 - alive_slot.0) * u, alive_slot.1 + (dead_slot.1 - alive_slot.1) * u)
            } else {
                alive_slot
            };
            x += dx;
            y += dy;
        }
        placed.push((y, x, s, lying));
    }
    placed.sort_by(|p, q| (!p.3).cmp(&!q.3).then(p.0.partial_cmp(&q.0).unwrap()));
    let at = |id: usize| shown.iter().find(|o| o.id == id).map(|o| (o.x, o.y));
    for &(y, x, s, lying) in &placed {
        let info = &rec.units[s.id];
        let anim = animate(rec, &ms, s, ff, &at);
        let name = sprite_name(rec, s.id, anim.pose, f);
        let Some(spr) = a.sprites.get(&name) else { continue };
        let big = info.fp >= 2 || info.name.as_str() != "Муравей (рабочая)" && info.side == 0;
        if !lying && anim.pose != Pose::Dead {
            cv.shadow(x + 2.0, y, if big { 40.0 } else { 14.0 }, if big { 7.0 } else { 3.0 });
        }
        let flip = info.side == 1;
        let ox = if flip { spr.img.w - 1 - spr.ox } else { spr.ox };
        let (sx, sy) = ((x + anim.dx).round() as i32 - ox, (y + anim.dy).round() as i32 - spr.oy);
        if anim.pose == Pose::Dead {
            // the dead lie darker and greyer than the living, so a heap of them does not read as a living swarm
            cv.blit_shade(&spr.img, sx, sy, flip, 0.62, 0.55);
        } else if anim.flash > 0.0 {
            cv.blit_tint(&spr.img, sx, sy, flip, [255, 250, 236], anim.flash);
        } else {
            cv.blit(&spr.img, sx, sy, flip, 1.0);
        }
        if let Some(k) = s.dead_at {
            dust(cv, x, y, ff - k as f32 - 3.0, info.side == 0, big, s.id);
        }
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
            let name = sprite_name(rec, id, s.pose, f);
            let top = a.sprites.get(&name).map(|sp| sp.oy).unwrap_or(40);
            let lit = ((st.hp.max(0) * 10 + info.max_hp - 1) / info.max_hp.max(1)).clamp(0, 10);
            // kept on the screen: a leader at the very edge still shows his crown and his health
            let (cx, cy) = ((s.x as i32).clamp(66, W - 52), (s.y as i32 - top - 10).max(48));
            meter(cv, a, cx, cy, lit, if info.side == 1 { "scale_over" } else { "scale_eat" });
            bars.push((cx - 66, cy - 12, cx + 52, cy + 12));
        }
    }
    for e in &sparks.1 {
        bolt(cv, a, rec, &shown, e, f);
    }
    for e in &sparks.1 {
        effect(cv, a, e, f);
    }
    for n in &sparks.0 {
        number(cv, a, rec, n, f, &bars);
    }
    let end = view.frame as i32 - (total - 1);
    if end > 0 {
        cv.dim(0, 0, W, H, 1.0 - 0.5 * (end as f32 / 12.0).min(1.0));
    }
}

/// The interface over the field: the wing (the tug of war, the counts, the turn, the speed buttons with their keys)
/// and at the end the plate.
pub fn draw_hud(cv: &mut Image, a: &Assets, rec: &Record, view: &View) {
    let total = rec.frames();
    let f = (view.frame as i32).min(total - 1);
    // the wing: the swarm against the Foundry, the turn, the speed
    cv.blit(&a.ui["wing_battle_960"].img, 0, 0, false, 1.0);
    let alive = |side: u8| rec.units.iter().enumerate().filter(|(i, u)| u.side == side && rec.state_at(*i, f).alive && rec.state_at(*i, f).present).count();
    let hp = |side: u8| -> f32 {
        let (mut now, mut all) = (0.0, 0.0);
        for (i, u) in rec.units.iter().enumerate() {
            if u.side == side {
                all += u.max_hp as f32;
                let s = rec.state_at(i, f);
                if s.alive && s.present {
                    now += s.hp.max(0) as f32;
                }
            }
        }
        now / all.max(1.0)
    };
    let (sw, fo) = (hp(1), hp(0));
    let share = if sw + fo > 0.0 { sw / (sw + fo) } else { 0.5 };
    let title = &a.fonts["title16"];
    title.draw(cv, &format!("рой {}", alive(1)), 16, 8, ACID, Some(ACID_EDGE), Align::Left, 1.0);
    let (ts, tf) = (&a.ui["tug_swarm"].img, &a.ui["tug_foundry"].img);
    let cut = (share * ts.w as f32) as i32;
    cv.blit_region(ts, 0, 0, cut, ts.h, 144, 10, false, 1.0);
    cv.blit_region(tf, cut, 0, tf.w - cut, tf.h, 144 + cut, 10, false, 1.0);
    for j in 0..ts.h {
        let x = 144 + cut + if (j / 2) % 2 == 0 { 2 } else { -2 };
        cv.blend_px(x, 10 + j, [255, 244, 200, 255], 1.0);
    }
    let text = &a.fonts["text16"];
    let nf = rec.units.iter().filter(|u| u.side == 0).count();
    text.draw(cv, &format!("Литейщик: {} из {nf}", alive(0)), 530, 9, [214, 196, 150], Some([16, 12, 16]), Align::Left, 1.0);
    let turn = (f / FR + 1).min(rec.rounds.len() as i32);
    text.draw(cv, &format!("ход {turn}"), 728, 9, MUTED, Some([16, 12, 16]), Align::Right, 1.0);
    let hot = |b: Button| view.hover == Some(b);
    button(cv, a, 736, 784, 2, view.paused, hot(Button::Pause), "II", "Пробел", 1.0);
    button(cv, a, 790, 838, 2, !view.paused, hot(Button::Speed), &format!("×{}", view.speed), "Tab", 1.0);
    button(cv, a, 844, 952, 2, false, hot(Button::ToEnd), "в конец »", "End", 1.0);
    // the end: the plate across the dimmed field
    let end = view.frame as i32 - (total - 1);
    if end > 0 {
        let k = (end as f32 / 12.0).min(1.0);
        let win = rec.outcome.winner == Some(1);
        let p = &a.ui[if win { "end_plate_win" } else { "end_plate_lose" }];
        let dy = ((1.0 - k) * -40.0) as i32;
        cv.blit(&p.img, W / 2 - p.img.w / 2, H / 2 - 60 + dy, false, k);
        let big = &a.fonts["title24"];
        let (t, c, e) = if win { ("ПОБЕДА", ACID, ACID_EDGE) } else { ("ПОРАЖЕНИЕ", [176, 178, 186], [56, 58, 68]) };
        big.draw(cv, t, W / 2, H / 2 - 30 + dy, c, Some(e), Align::Center, k);
        let sub = format!("ходов: {} · зерно {}", rec.rounds.len(), rec.seed);
        text.draw(cv, &sub, W / 2, H / 2 + 46 + dy, INK, Some([16, 12, 16]), Align::Center, k);
        button(cv, a, W / 2 - 70, W / 2 + 70, PLATE_BUTTON_Y + dy, true, hot(Button::NewBattle), "новый бой", "R", k);
    }
}
