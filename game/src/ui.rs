//! The interface between battles: an immediate-mode kit over the engine kits of both classes (game/assets/ui/
//! foundry, …/swarm — tools/sprites/engine_kit.py, swarm_engine_kit.py). A screen draws itself every frame and asks
//! the kit, as it draws a control, whether the mouse is on it and whether it was clicked; the kit keeps only how far
//! each control has eased into its hover (0..1), so a lift or a glow comes on smoothly.
//!
//! Everything is drawn on the 960×540 canvas of the interface (the window lays it over at a whole factor). The
//! Foundry's controls are forge iron and brass: a throttle lever beside a cast nameplate for the screen's own
//! action, a push-button with its stamped tag on a wire for the rest; the swarm's are chitin plates with acid,
//! amber or blood in them.

use crate::assets::{Align, Assets};
use crate::gfx::Image;
use sim::run::Class;
use std::collections::HashMap;

#[derive(Clone, Copy, PartialEq, Debug, Default)]
pub struct Rect {
    pub x: i32,
    pub y: i32,
    pub w: i32,
    pub h: i32,
}

impl Rect {
    pub const fn new(x: i32, y: i32, w: i32, h: i32) -> Rect {
        Rect { x, y, w, h }
    }
    pub fn contains(&self, x: i32, y: i32) -> bool {
        x >= self.x && y >= self.y && x < self.x + self.w && y < self.y + self.h
    }
    pub fn cx(&self) -> i32 {
        self.x + self.w / 2
    }
    pub fn cy(&self) -> i32 {
        self.y + self.h / 2
    }
    pub fn shift(self, dx: i32, dy: i32) -> Rect {
        Rect { x: self.x + dx, y: self.y + dy, ..self }
    }
    pub fn inset(self, d: i32) -> Rect {
        Rect { x: self.x + d, y: self.y + d, w: self.w - 2 * d, h: self.h - 2 * d }
    }
}

pub const INK: [u8; 3] = [230, 220, 204];
pub const MUTED: [u8; 3] = [150, 142, 128];
pub const PALE: [u8; 3] = [110, 104, 100];
pub const GOLD: [u8; 3] = [240, 200, 120];
pub const BRASS: [u8; 3] = [208, 168, 72];
pub const RED: [u8; 3] = [232, 96, 64];
pub const BLUE: [u8; 3] = [154, 216, 255];
pub const ACID: [u8; 3] = [176, 244, 70];
pub const ACID2: [u8; 3] = [214, 255, 140];
pub const VIOLET: [u8; 3] = [196, 160, 240];
pub const EDGE: [u8; 3] = [16, 12, 16];
/// The cast-metal headings: pale steel running down to warm brown (the Foundry), bone to rust (the swarm).
pub const TITLE_F: ([u8; 3], [u8; 3]) = ([240, 230, 214], [124, 98, 70]);
pub const TITLE_S: ([u8; 3], [u8; 3]) = ([236, 216, 170], [150, 96, 60]);

/// Keys a screen may answer.
#[derive(Clone, Copy, PartialEq, Debug)]
pub enum Key {
    Enter,
    Esc,
    Space,
    Tab,
    End,
    R,
    C,
    Digit(u8),
    /// The battle's camera nearer / farther (+ / −).
    ZoomIn,
    ZoomOut,
    /// F1: the help.
    Help,
}

/// A tooltip: where the mouse was, its lines with their colours.
type Tip = (i32, i32, Vec<(String, [u8; 3])>);

pub struct Ui {
    pub mx: i32,
    pub my: i32,
    pub down: bool,
    press: Option<(i32, i32)>,
    /// The right button: where it went down, and whether it came up this frame (a click to look closer).
    rpress: Option<(i32, i32)>,
    rreleased: bool,
    pub pressed: bool,
    pub released: bool,
    pub keys: Vec<Key>,
    /// Steps of the mouse wheel this frame: up (away from the player) positive.
    pub wheel: i32,
    /// Alt held: every icon drawn gets its name under it (`named` gathers them for the frame).
    pub alt: bool,
    pub named: Vec<(i32, i32, i32, String)>,
    /// Seconds since the game began, and since the last frame.
    pub t: f32,
    pub dt: f32,
    hover: HashMap<String, f32>,
    seen: Vec<String>,
    /// Controls under an overlay don't answer.
    pub blocked: bool,
    /// Interface sounds asked for this frame.
    pub sounds: Vec<&'static str>,
    cache: HashMap<(String, i32, i32), Image>,
    tip: Option<Tip>,
    /// When the screen came up, and when the last thing opened over it (a find, an overlay): the entrance of their
    /// cards is timed from these.
    pub entered: f32,
    pub opened: f32,
    /// Where the currency's number stands on the top bar (a change floats up from there).
    pub money_at: (i32, i32),
}

impl Default for Ui {
    fn default() -> Self {
        Ui::new()
    }
}

impl Ui {
    pub fn new() -> Ui {
        Ui {
            mx: -1,
            my: -1,
            down: false,
            press: None,
            rpress: None,
            rreleased: false,
            pressed: false,
            released: false,
            keys: vec![],
            wheel: 0,
            alt: false,
            named: vec![],
            t: 0.0,
            dt: 0.0,
            hover: HashMap::new(),
            seen: vec![],
            blocked: false,
            sounds: vec![],
            cache: HashMap::new(),
            tip: None,
            entered: 0.0,
            opened: 0.0,
            money_at: (0, 0),
        }
    }

    pub fn mouse_down(&mut self) {
        self.down = true;
        self.pressed = true;
        self.press = Some((self.mx, self.my));
    }

    pub fn mouse_up(&mut self) {
        self.down = false;
        self.released = true;
    }

    pub fn rmouse_down(&mut self) {
        self.rpress = Some((self.mx, self.my));
    }

    pub fn rmouse_up(&mut self) {
        self.rreleased = true;
    }

    /// The right button came up this frame (anywhere).
    pub fn rreleased_at(&self) -> bool {
        self.rreleased && !self.blocked
    }

    /// A right click on `r` (to look closer at what is there): pressed and let go on it.
    pub fn rclicked(&mut self, r: Rect) -> bool {
        let hit = !self.blocked && self.rreleased && r.contains(self.mx, self.my) && self.rpress.is_some_and(|(x, y)| r.contains(x, y));
        if hit {
            self.rpress = None;
        }
        hit
    }

    /// The frame's input has been read by the screens: the clicks and keys are spent, the controls not drawn this
    /// frame ease back out of their hover.
    pub fn end(&mut self, dt: f32) {
        self.dt = dt;
        self.t += dt;
        let seen = std::mem::take(&mut self.seen);
        self.hover.retain(|k, _| seen.contains(k));
        if self.released {
            self.press = None;
        }
        self.pressed = false;
        self.released = false;
        self.keys.clear();
        self.wheel = 0;
        if self.rreleased {
            self.rpress = None;
        }
        self.rreleased = false;
    }

    /// Whether the mouse is on `r`, and how far this control has eased into its hover (0..1).
    pub fn hot(&mut self, id: &str, r: Rect) -> (bool, f32) {
        let over = !self.blocked && r.contains(self.mx, self.my);
        let rate = 1.0 - (-14.0 * self.dt.max(0.001)).exp();
        let k = self.hover.entry(id.to_string()).or_insert(0.0);
        *k += ((over as i32 as f32) - *k) * rate;
        if !self.seen.iter().any(|s| s == id) {
            self.seen.push(id.to_string());
        }
        (over, *k)
    }

    /// A click on `r`: pressed and let go on it.
    pub fn clicked(&mut self, r: Rect) -> bool {
        let hit = !self.blocked && self.released && r.contains(self.mx, self.my) && self.press.is_some_and(|(x, y)| r.contains(x, y));
        if hit {
            self.press = None;
        }
        hit
    }

    pub fn key(&mut self, k: Key) -> bool {
        if self.blocked {
            return false;
        }
        if let Some(i) = self.keys.iter().position(|&x| x == k) {
            self.keys.remove(i);
            return true;
        }
        false
    }

    /// How far below its place the i-th card of the screen still is as it comes up (0 once it has settled): one
    /// after another, quick and easing out.
    pub fn rise(&self, i: usize) -> i32 {
        self.rise_from(self.entered, i)
    }

    pub fn rise_from(&self, t0: f32, i: usize) -> i32 {
        let k = ((self.t - t0 - i as f32 * 0.06) / 0.3).clamp(0.0, 1.0);
        ((1.0 - k).powi(3) * 30.0).round() as i32
    }

    pub fn sound(&mut self, name: &'static str) {
        self.sounds.push(name);
    }

    // ---------------------------------------------------------------- drawing the kit's pieces

    /// A piece of the kit at `r` (its inside: a halo margin, if it has one, spills round it), grown to the size
    /// its slicing allows; a piece with no slicing is drawn as it is at r's corner.
    pub fn piece(&mut self, cv: &mut Image, a: &Assets, name: &str, r: Rect, alpha: f32) {
        let Some(p) = a.ui.get(name) else { return };
        let (px, py) = p.pad();
        match p.slicing() {
            Some((sl, tx, ty)) => {
                let three = sl[1] == 0 && sl[3] == 0;
                let (w, h) = (r.w + 2 * px, if three { p.img.h } else { r.h + 2 * py });
                let key = (name.to_string(), w, h);
                if !self.cache.contains_key(&key) {
                    let g = p.img.grow(w, h, sl, tx, ty);
                    self.cache.insert(key.clone(), g);
                }
                let img = &self.cache[&key];
                let y = if three { r.y + (r.h - img.h) / 2 } else { r.y - py };
                cv.blit(img, r.x - px, y, false, alpha);
            }
            None => cv.blit(&p.img, r.x - px, r.y - py, false, alpha),
        }
    }

    /// A piece drawn as it is with its top-left at (x, y).
    pub fn put(&self, cv: &mut Image, a: &Assets, name: &str, x: i32, y: i32, alpha: f32) {
        if let Some(p) = a.ui.get(name) {
            cv.blit(&p.img, x, y, false, alpha);
        }
    }

    #[allow(clippy::too_many_arguments)]
    pub fn icon(&mut self, cv: &mut Image, a: &Assets, key: &str, x: i32, y: i32, k: i32, alpha: f32) {
        let Some((atlas, r)) = a.icons.get(key) else { return };
        if self.alt && alpha > 0.5 {
            self.named.push((x + r[2] * k / 2, y + r[3] * k, r[2] * k, key.to_string()));
        }
        let Some(img) = a.atlases.get(atlas) else { return };
        if k == 1 {
            cv.blit_region(img, r[0], r[1], r[2], r[3], x, y, false, alpha);
            return;
        }
        let ck = (format!("icon:{key}"), k, 0);
        if !self.cache.contains_key(&ck) {
            self.cache.insert(ck.clone(), img.crop(r[0], r[1], r[2], r[3]).scaled(k));
        }
        cv.blit(&self.cache[&ck], x, y, false, alpha);
    }

    /// A sprite (a body) scaled up by k, from the cache.
    #[allow(clippy::too_many_arguments)]
    pub fn sprite_k(&mut self, cv: &mut Image, a: &Assets, name: &str, gx: i32, gy: i32, k: i32, flip: bool, alpha: f32) {
        let Some(s) = a.sprites.get(name) else { return };
        if k == 1 {
            let ox = if flip { s.img.w - 1 - s.ox } else { s.ox };
            cv.blit(&s.img, gx - ox, gy - s.oy, flip, alpha);
            return;
        }
        let ck = (format!("spr:{name}"), k, 0);
        if !self.cache.contains_key(&ck) {
            self.cache.insert(ck.clone(), s.img.scaled(k));
        }
        let img = &self.cache[&ck];
        let ox = if flip { img.w - 1 - s.ox * k } else { s.ox * k };
        cv.blit(img, gx - ox, gy - s.oy * k, flip, alpha);
    }

    // ---------------------------------------------------------------- the controls

    /// The screen's own action, the Foundry's way: a throttle lever beside a cast nameplate (sizes 272×64, 244×52,
    /// 200×44). Under the mouse the lever is thrown and the enamel glows, sparks fly off the plate.
    #[allow(clippy::too_many_arguments)]
    pub fn lever(&mut self, cv: &mut Image, a: &Assets, id: &str, x: i32, y: i32, size: (i32, i32), label: &str, on: bool) -> bool {
        let (w, h) = size;
        let r = Rect::new(x, y, w + 46, h);
        let (over, k) = self.hot(id, r);
        let lit = on && (over || k > 0.5);
        self.put(cv, a, if lit { "foundry/lever_thrown" } else { "foundry/lever_rest" }, x - 4, y + h / 2 - 34, 1.0);
        let state = if !on { "off" } else if lit { "lit" } else { "rest" };
        self.put(cv, a, &format!("plate_{state}_{w}x{h}"), x + 44 - 2, y - 2, 1.0);
        if on && k > 0.01 {
            cv.glow((x + 44 + w / 2) as f32, (y + h / 2) as f32, w as f32 * 0.7, [255, 110, 40], 0.18 * k);
            sparks(cv, self.t, x + 44 + w - 14, y + 6, 7, k, 3);
            sparks(cv, self.t, x + 62, y + h - 4, 5, k, 9);
        }
        let font = &a.fonts["title16"];
        let col = if on { [255, 222, 150] } else { [120, 112, 104] };
        font.draw_grad(cv, label, x + 44 + w / 2, y + h / 2 - 9, col, if on { [176, 120, 50] } else { [80, 74, 70] }, EDGE, Align::Center, 1.0);
        let hit = on && self.clicked(r);
        if hit {
            self.sound("click");
        }
        hit
    }

    /// A push-button in its nut with a stamped tag on a wire (kinds: steel, brass, rust, dull). Returns whether it
    /// was clicked. Its width: the knob, the tag sized to the words.
    #[allow(clippy::too_many_arguments)]
    pub fn tag(&mut self, cv: &mut Image, a: &Assets, id: &str, x: i32, y: i32, label: &str, kind: &str, on: bool) -> bool {
        let font = &a.fonts["text16"];
        let tw = font.width(label) + 34;
        let r = Rect::new(x, y, 46 + tw, 40);
        let (over, k) = self.hot(id, r);
        let kind = if on { kind } else { "dull" };
        let down = on && over && self.down;
        let knob = format!("foundry/button_{kind}_{}", if on && (over || k > 0.5) { "down" } else { "rest" });
        self.put(cv, a, &knob, x, y + down as i32, 1.0);
        // the wire from the knob to the tag, and the tag swinging a little as the mouse comes on it
        let swing = (k * (1.0 - k) * 4.0 * (self.t * 18.0).sin()).round() as i32;
        cv.fill(x + 38, y + 20, 10, 1, [60, 58, 64, 255]);
        let tr = Rect::new(x + 46, y + 7 + swing.clamp(-1, 1), tw, 26);
        self.piece(cv, a, &format!("foundry/tag_{kind}"), tr, 1.0);
        if on && k > 0.01 {
            cv.glow(tr.cx() as f32, tr.cy() as f32, tw as f32 * 0.6, [255, 230, 190], 0.06 * k);
        }
        let col = if on { [26, 22, 24] } else { [70, 66, 70] };
        font.draw(cv, label, tr.x + 20 + (tw - 20) / 2, tr.y + 4, col, None, Align::Center, 1.0);
        let hit = on && self.clicked(r);
        if hit {
            self.sound("click");
        }
        hit
    }

    /// A chitin button of the swarm in `r` (kinds: chitin, acid, amber, blood, dim); the words in the title font
    /// (big) or the text font. Under the mouse it brightens and its rim glows.
    #[allow(clippy::too_many_arguments)]
    pub fn chitin(&mut self, cv: &mut Image, a: &Assets, id: &str, r: Rect, label: &str, kind: &str, on: bool, big: bool) -> bool {
        let (over, k) = self.hot(id, r);
        let kind = if on { kind } else { "dim" };
        let sz = [22, 30, 42, 56].into_iter().min_by_key(|&s| (s - r.h).abs()).unwrap_or(30);
        let lift = if on && over && self.down { 1 } else { 0 };
        self.piece(cv, a, &format!("swarm/button_{kind}_{sz}"), r.shift(0, lift), 1.0);
        if on && k > 0.01 {
            let g = if kind == "acid" { [150, 230, 60] } else { [200, 160, 255] };
            cv.glow(r.cx() as f32, r.cy() as f32, r.w as f32 * 0.55, g, 0.14 * k);
        }
        let (font, dy) = if big { (&a.fonts["title16"], 9) } else { (&a.fonts["text16"], 9) };
        let col = match kind {
            "acid" => ACID2,
            "dim" => [110, 100, 120],
            "blood" => [255, 210, 190],
            "amber" => [255, 236, 190],
            _ => INK,
        };
        if big {
            font.draw_grad(cv, label, r.cx(), r.cy() - dy + lift, col, [col[0] / 2, col[1] / 2, col[2] / 2], EDGE, Align::Center, 1.0);
        } else {
            font.draw(cv, label, r.cx(), r.cy() - dy + lift, col, Some(EDGE), Align::Center, 1.0);
        }
        let hit = on && self.clicked(r);
        if hit {
            self.sound("click");
        }
        hit
    }

    /// The class's main action button (the lever / the acid plate).
    #[allow(clippy::too_many_arguments)]
    pub fn action(&mut self, cv: &mut Image, a: &Assets, cls: Class, id: &str, x: i32, y: i32, label: &str, on: bool) -> bool {
        match cls {
            Class::Foundry => self.lever(cv, a, id, x, y, (244, 52), label, on),
            Class::Swarm => self.chitin(cv, a, id, Rect::new(x, y, 290, 54), label, "acid", on, true),
        }
    }

    /// The class's lesser button (a tag / a chitin plate).
    #[allow(clippy::too_many_arguments)]
    pub fn minor(&mut self, cv: &mut Image, a: &Assets, cls: Class, id: &str, x: i32, y: i32, label: &str, on: bool) -> bool {
        match cls {
            Class::Foundry => self.tag(cv, a, id, x, y, label, "steel", on),
            Class::Swarm => {
                let w = a.fonts["text16"].width(label) + 70;
                self.chitin(cv, a, id, Rect::new(x, y + 2, w.max(150), 38), label, "chitin", on, false)
            }
        }
    }

    /// A card: the class's cell, lifted a little and lit under the mouse. `state`: normal, hi, new, rare, broken,
    /// locked (the Foundry's names; the swarm's cells are matched to them). Returns (hovered, ease, clicked).
    #[allow(clippy::too_many_arguments)]
    pub fn card(&mut self, cv: &mut Image, a: &Assets, cls: Class, id: &str, r: Rect, state: &str, on: bool) -> (bool, f32, bool) {
        let (over, k) = self.hot(id, r);
        let lift = if on { (k * 4.0).round() as i32 } else { 0 };
        let rr = r.shift(0, -lift);
        let st = if on && over && state == "normal" { "hover" } else { state };
        cell(self, cv, a, cls, rr, st);
        if on && k > 0.01 {
            let g = match cls {
                Class::Foundry => [255, 170, 80],
                Class::Swarm => [140, 220, 70],
            };
            cv.glow(rr.cx() as f32, rr.cy() as f32, (r.w.max(r.h)) as f32 * 0.6, g, 0.07 * k);
        }
        let hit = on && self.clicked(r);
        if hit {
            self.sound("click");
        }
        (over, if on { k } else { 0.0 }, hit)
    }

    /// A tooltip to draw over everything at the end of the frame, by the mouse.
    pub fn tooltip(&mut self, lines: Vec<(String, [u8; 3])>) {
        self.tip = Some((self.mx, self.my, lines));
    }

    pub fn draw_tip(&mut self, cv: &mut Image, a: &Assets, cls: Class) {
        let Some((mx, my, lines)) = self.tip.take() else { return };
        let font = &a.fonts["text16"];
        let w = lines.iter().map(|(s, _)| font.width(s)).max().unwrap_or(0) + 24;
        let h = lines.len() as i32 * 20 + 16;
        let x = (mx + 16).min(960 - w - 6).max(6);
        let y = if my + 20 + h > 534 { my - h - 8 } else { my + 20 };
        cell(self, cv, a, cls, Rect::new(x, y, w, h), "hi");
        for (i, (s, c)) in lines.iter().enumerate() {
            font.draw(cv, s, x + 12, y + 8 + i as i32 * 20, *c, Some(EDGE), Align::Left, 1.0);
        }
    }
}

/// The class's cell (a card, a row, a box) in a state.
pub fn cell(ui: &mut Ui, cv: &mut Image, a: &Assets, cls: Class, r: Rect, state: &str) {
    match cls {
        Class::Foundry => ui.piece(cv, a, &format!("foundry/cell_{state}"), r, 1.0),
        Class::Swarm => {
            let st = match state {
                "rare" => "mut",
                "broken" => "eat",
                "trophy" => "find",
                s => s,
            };
            let sz = if r.h >= 70 { 12 } else { 8 };
            ui.piece(cv, a, &format!("swarm/cell_{st}_{sz}"), r, 1.0)
        }
    }
}

/// The class's plate (a panel).
pub fn plate(ui: &mut Ui, cv: &mut Image, a: &Assets, cls: Class, r: Rect) {
    match cls {
        Class::Foundry => {
            // the plate's rivets fall on an 18-pixel step: its size snaps so none is cut in half
            let snap = |v: i32| 38 + ((v - 38).max(0) + 9) / 18 * 18;
            ui.piece(cv, a, "foundry/plate", Rect::new(r.x, r.y, snap(r.w), snap(r.h)), 1.0)
        }
        Class::Swarm => ui.piece(cv, a, "swarm/plate", r, 1.0),
    }
}

pub fn text(cv: &mut Image, a: &Assets, s: &str, x: i32, y: i32, col: [u8; 3], align: Align) {
    a.fonts["text16"].draw(cv, s, x, y, col, Some(EDGE), align, 1.0);
}

/// Words broken to a width, line under line (20 px apart); returns the y under the last line.
pub fn para(cv: &mut Image, a: &Assets, s: &str, x: i32, y: i32, w: i32, col: [u8; 3]) -> i32 {
    let font = &a.fonts["text16"];
    let mut y = y;
    for line in font.wrap(s, w) {
        font.draw(cv, &line, x, y, col, Some(EDGE), Align::Left, 1.0);
        y += 20;
    }
    y
}

/// A heading in the title font, 16 or 24, cast-metal colours.
#[allow(clippy::too_many_arguments)]
pub fn heading(cv: &mut Image, a: &Assets, s: &str, x: i32, y: i32, px: i32, cols: ([u8; 3], [u8; 3]), align: Align) {
    let f = if px >= 24 { &a.fonts["title24"] } else { &a.fonts["title16"] };
    f.draw_grad(cv, s, x, y, cols.0, cols.1, EDGE, align, 1.0);
}

fn hash(n: u32) -> f32 {
    let mut x = n.wrapping_mul(0x9E37_79B9) ^ 0x85EB_CA6B;
    x ^= x >> 15;
    x = x.wrapping_mul(0x2C1B_3C6D);
    x ^= x >> 12;
    (x % 10_000) as f32 / 10_000.0
}

/// A few sparks spitting off a point, redrawn from the time (no state): a hot plate under the mouse.
pub fn sparks(cv: &mut Image, t: f32, x: i32, y: i32, n: u32, k: f32, seed: u32) {
    for i in 0..n {
        let h = hash(seed * 131 + i);
        let period = 0.5 + h * 0.6;
        let ph = ((t / period) + hash(i * 7 + seed)).fract();
        let ang = -1.2 - hash(i * 13 + seed) * 2.0;
        let d = ph * (10.0 + h * 14.0);
        let (px, py) = (x as f32 + ang.cos() * d, y as f32 + ang.sin() * d + ph * ph * 10.0);
        let c = if ph < 0.5 { [255, 236, 170, 255] } else { [255, 140, 50, 255] };
        cv.blend_px(px as i32, py as i32, c, (1.0 - ph) * k);
    }
}

/// Embers rising through a region (the forge) or spores drifting up (the hive): drawn from the time, no state.
pub fn motes(cv: &mut Image, t: f32, r: Rect, n: u32, cls: Class, k: f32) {
    for i in 0..n {
        let h = hash(i * 977 + 13);
        let period = 5.0 + h * 7.0;
        let ph = ((t / period) + hash(i * 31 + 7)).fract();
        let sway = (t * (0.5 + h) + i as f32).sin() * (4.0 + h * 8.0);
        let x = r.x as f32 + hash(i * 53 + 3) * r.w as f32 + sway;
        let y = (r.y + r.h) as f32 - ph * r.h as f32;
        let fade = (ph * 6.0).min(1.0) * ((1.0 - ph) * 3.0).min(1.0) * k;
        let flick = 0.6 + 0.4 * (t * (6.0 + h * 9.0) + i as f32).sin();
        let col = match cls {
            Class::Foundry => {
                if h < 0.5 {
                    [255, 160, 60, 255]
                } else {
                    [255, 220, 140, 255]
                }
            }
            Class::Swarm => {
                if h < 0.5 {
                    [150, 230, 70, 255]
                } else {
                    [200, 255, 150, 255]
                }
            }
        };
        cv.blend_px(x as i32, y as i32, col, fade * flick);
        if h > 0.8 {
            cv.glow(x, y, 4.0, [col[0], col[1], col[2]], 0.12 * fade);
        }
    }
}

/// The shutters between two screens, closed by `k` (0..1): the Foundry's are iron with a brass edge and rivets, the
/// swarm's are chitin plates with acid seeping at the seam.
pub fn shutters(cv: &mut Image, k: f32, cls: Class) {
    if k <= 0.001 {
        return;
    }
    let e = k * k * (3.0 - 2.0 * k);
    let h = (e * 272.0) as i32;
    let (body, rim, glow) = match cls {
        Class::Foundry => ([22, 19, 21, 255], [208, 168, 72, 255], [255, 140, 50]),
        Class::Swarm => ([24, 18, 30, 255], [150, 230, 70, 255], [140, 220, 60]),
    };
    cv.fill(0, 0, 960, h, body);
    cv.fill(0, 540 - h, 960, h, body);
    for (y, dir) in [(h - 3, 1), (540 - h, -1)] {
        cv.fill(0, y, 960, 3, rim);
        cv.fill(0, y + if dir > 0 { 3 } else { -2 }, 960, 2, [8, 6, 10, 255]);
        if cls == Class::Foundry {
            for x in (12..960).step_by(36) {
                let ry = y + if dir > 0 { -10 } else { 12 };
                cv.fill(x, ry, 3, 3, [120, 112, 118, 255]);
                cv.fill(x, ry, 1, 1, [200, 196, 200, 255]);
            }
        } else {
            for x in (8..960).step_by(26) {
                let ry = y + if dir > 0 { -12 } else { 12 };
                cv.fill(x, ry, 12, 1, [52, 40, 62, 255]);
            }
        }
    }
    if k > 0.6 {
        cv.glow(480.0, 270.0, 300.0, glow, (k - 0.6) * 0.35);
    }
}
