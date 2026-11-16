//! A frame of the demo: the field with the units in depth order, the effects and numbers over them, the swarm's
//! thin wing on top (the tug of war, the counts, the turn, the speed buttons with their keys), the leaders' health
//! with the crown, and at the end the plate across the dimmed field.

use crate::assets::{Align, Assets, Font};
use crate::gfx::Image;
use crate::playback::{Effect, Number, NumStyle, Pose, Record, FR};

pub const W: i32 = 960;
pub const H: i32 = 540;

pub struct View {
    pub frame: f32,
    pub speed: u32,
    pub paused: bool,
}

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
                Pose::Idle => "idle",
                Pose::Attack => "attack",
                Pose::Dead => "broken",
            };
            format!("{n}_{p}")
        }
        "Пожиратель" => {
            let st = rec.state_at(id, f).growth.min(2);
            let p = match pose {
                Pose::Idle => "idle",
                Pose::Attack => "attack",
                Pose::Dead => "dead",
            };
            format!("Пожиратель_{st}_{p}")
        }
        _ => {
            let p = match pose {
                Pose::Idle => "idle",
                Pose::Attack => "attack",
                Pose::Dead => "dead",
            };
            let base = if n.starts_with("Кузнечик") { "Кузнечик (рабочая)" } else if n.contains("солдат") { "Муравей (солдат)" } else { "Муравей (рабочая)" };
            format!("{base}_{}_{p}", id % 4)
        }
    }
}

const SLOTS: [(f32, f32); 4] = [(-11.0, -6.0), (11.0, -7.0), (-10.0, 8.0), (12.0, 7.0)];

fn number(cv: &mut Image, a: &Assets, rec: &Record, n: &Number, f: i32) {
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
    a.fonts[font].draw(cv, &n.text, nx as i32, (ny + dy) as i32, col, Some(edge), Align::Center, fade);
}

fn effect(cv: &mut Image, a: &Assets, e: &Effect, f: i32) {
    let fx = &a.fx[e.name];
    let per = 24.0 / fx.fps; // game frames per effect frame
    let k = ((f - e.start) as f32 / per.max(0.01)) as i32;
    if f < e.start || k >= fx.frames {
        return;
    }
    cv.blit_region(&fx.img, k * fx.w, 0, fx.w, fx.h, e.x as i32 - fx.pivot.0, e.y as i32 - fx.pivot.1, false, 1.0);
}

fn button(cv: &mut Image, a: &Assets, x0: i32, x1: i32, lit: bool, text: &str, key: &str) {
    let p = &a.ui[if lit { "button_amber_22" } else { "button_chitin_22" }];
    // the kit's 22 px button: 14 px of pad either side, the hexagon's points ~12 px, the middle repeats
    cv.three_slice(&p.img, x0 - 14, 2, (x1 - x0) + 28, 26, 26, (110, 116));
    a.fonts["text16"].draw(cv, text, (x0 + x1) / 2, 9, if lit { DARK } else { INK }, if lit { None } else { Some([16, 12, 16]) }, Align::Center, 1.0);
    keycap(cv, &a.fonts["text16"], (x0 + x1) / 2, 31, key);
}

fn keycap(cv: &mut Image, font: &Font, cx: i32, y: i32, t: &str) {
    let w = font.width(t) + 12;
    let x = cx - w / 2;
    cv.fill(x, y, w, 22, [26, 20, 32, 255]);
    cv.fill(x + 1, y + 1, w - 2, 17, [74, 64, 86, 255]);
    cv.fill(x + 2, y + 1, w - 4, 1, [114, 104, 126, 255]);
    font.draw(cv, t, cx, y + 1, INK, None, Align::Center, 1.0);
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
    // the units, in depth order; small ones sharing a cell spread over its four places
    let mut shown = rec.shown(view.frame.min((total - 1) as f32));
    let mut seen: std::collections::HashMap<(i32, i32, u8, bool), usize> = Default::default();
    let mut placed = vec![];
    shown.sort_by_key(|s| s.id);
    for s in &shown {
        let info = &rec.units[s.id];
        let (mut x, mut y) = (s.x, s.y);
        if info.fp == 1 && !info.leader {
            let key = ((s.x / 4.0) as i32, (s.y / 4.0) as i32, info.side, s.pose == Pose::Dead);
            let k = seen.entry(key).or_insert(0);
            let (dx, dy) = SLOTS[*k % 4];
            *k += 1;
            x += dx;
            y += dy;
        }
        placed.push((y, x, s));
    }
    placed.sort_by(|p, q| (p.2.pose != Pose::Dead).cmp(&(q.2.pose != Pose::Dead)).then(p.0.partial_cmp(&q.0).unwrap()));
    for (y, x, s) in &placed {
        let info = &rec.units[s.id];
        let name = sprite_name(rec, s.id, s.pose, f);
        let Some(spr) = a.sprites.get(&name) else { continue };
        let big = info.fp >= 2 || info.name.as_str() != "Муравей (рабочая)" && info.side == 0;
        if s.pose != Pose::Dead {
            cv.shadow(*x + 2.0, *y, if big { 40.0 } else { 14.0 }, if big { 7.0 } else { 3.0 });
        }
        let flip = info.side == 1;
        let ox = if flip { spr.img.w - 1 - spr.ox } else { spr.ox };
        cv.blit(&spr.img, *x as i32 - ox, *y as i32 - spr.oy, flip, 1.0);
    }
    // the leaders' health, the crown by it
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
            meter(cv, a, s.x as i32, s.y as i32 - top - 10, lit, if info.side == 1 { "scale_over" } else { "scale_eat" });
        }
    }
    for e in &sparks.1 {
        effect(cv, a, e, f);
    }
    for n in &sparks.0 {
        number(cv, a, rec, n, f);
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
    button(cv, a, 736, 784, view.paused, "II", "Пробел");
    button(cv, a, 790, 838, !view.paused, &format!("×{}", view.speed), "Tab");
    button(cv, a, 844, 952, false, "в конец »", "End");
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
        let sub = format!("ходов: {} · зерно {} · R — новый бой", rec.rounds.len(), rec.seed);
        text.draw(cv, &sub, W / 2, H / 2 + 52, INK, Some([16, 12, 16]), Align::Center, k);
    }
}
