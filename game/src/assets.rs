//! What the demo draws, baked by tools/sprites/demo_bake.py into game/assets and listed in assets.json.

use crate::gfx::Image;
use serde_json::Value;
use std::collections::HashMap;
use std::path::{Path, PathBuf};

pub struct Sprite {
    pub img: Image,
    /// The point on the ground the body stands on.
    pub ox: i32,
    pub oy: i32,
    /// Where a bolt leaves the body, from the ground point (the Sage's staff ball, the Inventor's arc).
    pub emit: Option<(i32, i32)>,
}

pub struct Fx {
    pub img: Image,
    pub w: i32,
    pub h: i32,
    pub frames: i32,
    pub pivot: (i32, i32),
    pub fps: f32,
}

pub struct Font {
    pub img: Image,
    pub line: i32,
    /// (x, y, width in the atlas, advance)
    pub glyphs: HashMap<char, (i32, i32, i32, i32)>,
}

pub struct Piece {
    pub img: Image,
    pub meta: Value,
}

/// How a piece grows: (left, top, right, bottom) kept, the columns and the rows that repeat.
pub type Slicing = ([i32; 4], (i32, i32), (i32, i32));

impl Piece {
    /// How it grows; None — drawn as it is.
    pub fn slicing(&self) -> Option<Slicing> {
        let sl = self.meta.get("slice")?.as_array()?;
        let sl = [i(&sl[0]), i(&sl[1]), i(&sl[2]), i(&sl[3])];
        let pair = |k: &str, full: i32| {
            self.meta.get(k).and_then(|v| v.as_array()).map(|v| (i(&v[0]), i(&v[1]))).unwrap_or((0, full))
        };
        let tx = self.meta.get("tile_x").map(|_| pair("tile_x", self.img.w)).unwrap_or((sl[0], self.img.w - sl[2]));
        let ty = self.meta.get("tile_y").map(|_| pair("tile_y", self.img.h)).unwrap_or((sl[1], self.img.h - sl[3]));
        Some((sl, tx, ty))
    }

    /// The see-through margin round it (for a halo, a spark): (x, y).
    pub fn pad(&self) -> (i32, i32) {
        match self.meta.get("pad") {
            Some(Value::Array(v)) => (i(&v[0]), i(&v[1])),
            Some(v) => (i(v), i(v)),
            None => (0, 0),
        }
    }
}

/// An icon: its atlas, and its rectangle in it (x, y, w, h).
pub type Icon = (String, [i32; 4]);

pub struct Assets {
    pub ground: Image,
    pub sprites: HashMap<String, Sprite>,
    pub fx: HashMap<String, Fx>,
    pub fonts: HashMap<String, Font>,
    pub ui: HashMap<String, Piece>,
    /// The screens' backgrounds (960×540, or a part of one), baked by tools/sprites/bake_screens.py.
    pub bg: HashMap<String, Image>,
    /// Icons: each a rectangle of one of the atlases.
    pub icons: HashMap<String, Icon>,
    pub atlases: HashMap<String, Image>,
}

/// Where the assets are: GAME_ASSETS if set; else `assets` next to the executable (a shipped build — the folder
/// beside game.exe); else the source tree's (a build run from the repository).
pub fn dir() -> PathBuf {
    if let Some(p) = std::env::var_os("GAME_ASSETS") {
        return PathBuf::from(p);
    }
    if let Some(beside) = std::env::current_exe().ok().and_then(|e| e.parent().map(|d| d.join("assets"))) {
        if beside.join("assets.json").is_file() {
            return beside;
        }
    }
    Path::new(env!("CARGO_MANIFEST_DIR")).join("assets")
}

fn i(v: &Value) -> i32 {
    v.as_i64().unwrap_or(0) as i32
}

impl Assets {
    pub fn load() -> Result<Self, String> {
        let root = dir();
        let text = std::fs::read_to_string(root.join("assets.json")).map_err(|e| format!("assets.json: {e}"))?;
        let m: Value = serde_json::from_str(&text).map_err(|e| e.to_string())?;
        let img = |f: &Value| Image::load(&root.join(f.as_str().unwrap_or("")));
        let mut sprites = HashMap::new();
        for (k, v) in m["sprites"].as_object().ok_or("no sprites")? {
            let emit = v["emit"].as_array().map(|e| (i(&e[0]), i(&e[1])));
            sprites.insert(k.clone(), Sprite { img: img(&v["file"])?, ox: i(&v["ox"]), oy: i(&v["oy"]), emit });
        }
        let mut fx = HashMap::new();
        for (k, v) in m["fx"].as_object().ok_or("no fx")? {
            fx.insert(
                k.clone(),
                Fx {
                    img: img(&v["file"])?,
                    w: i(&v["w"]),
                    h: i(&v["h"]),
                    frames: i(&v["frames"]),
                    pivot: (i(&v["pivot"][0]), i(&v["pivot"][1])),
                    fps: v["fps"].as_f64().unwrap_or(24.0) as f32,
                },
            );
        }
        let mut fonts = HashMap::new();
        for (k, v) in m["fonts"].as_object().ok_or("no fonts")? {
            let mut glyphs = HashMap::new();
            for (ch, g) in v["glyphs"].as_object().ok_or("no glyphs")? {
                if let Some(c) = ch.chars().next() {
                    glyphs.insert(c, (i(&g[0]), i(&g[1]), i(&g[2]), i(&g[3])));
                }
            }
            fonts.insert(k.clone(), Font { img: img(&v["file"])?, line: i(&v["line"]), glyphs });
        }
        let mut ui = HashMap::new();
        for (k, v) in m["ui"].as_object().ok_or("no ui")? {
            ui.insert(k.clone(), Piece { img: img(&v["file"])?, meta: v.clone() });
        }
        let mut bg = HashMap::new();
        if let Some(o) = m["bg"].as_object() {
            for (k, v) in o {
                bg.insert(k.clone(), img(&v["file"])?);
            }
        }
        let (mut icons, mut atlases) = (HashMap::new(), HashMap::new());
        if let Some(o) = m["icons"].as_object() {
            for (k, v) in o {
                let atlas = v["atlas"].as_str().unwrap_or("").to_string();
                if !atlases.contains_key(&atlas) {
                    atlases.insert(atlas.clone(), Image::load(&root.join(&atlas))?);
                }
                let r = &v["rect"];
                icons.insert(k.clone(), (atlas, [i(&r[0]), i(&r[1]), i(&r[2]), i(&r[3])]));
            }
        }
        Ok(Assets { ground: Image::load(&root.join("ground.png"))?, sprites, fx, fonts, ui, bg, icons, atlases })
    }
}

pub enum Align {
    Left,
    Center,
    Right,
}

impl Font {
    pub fn width(&self, text: &str) -> i32 {
        text.chars().map(|c| self.glyphs.get(&c).map(|g| g.3).unwrap_or(self.line / 2)).sum()
    }

    /// The text broken into lines no wider than `w` (at spaces; a line break kept).
    pub fn wrap(&self, text: &str, w: i32) -> Vec<String> {
        let mut out = vec![];
        for para in text.split('\n') {
            let mut line = String::new();
            for word in para.split(' ') {
                let cand = if line.is_empty() { word.to_string() } else { format!("{line} {word}") };
                if self.width(&cand) > w && !line.is_empty() {
                    out.push(std::mem::take(&mut line));
                    line = word.to_string();
                } else {
                    line = cand;
                }
            }
            out.push(line);
        }
        out
    }

    /// A title: the letters running from `top` to `bot` down their height, a dark outline and a shadow under them
    /// (the mockups' cast-metal headings).
    #[allow(clippy::too_many_arguments)]
    pub fn draw_grad(&self, cv: &mut Image, text: &str, x: i32, y: i32, top: [u8; 3], bot: [u8; 3], edge: [u8; 3], align: Align, alpha: f32) {
        let w = self.width(text);
        let x0 = match align {
            Align::Left => x,
            Align::Center => x - w / 2,
            Align::Right => x - w,
        };
        let px = self.line * 2 / 3;
        let mut cx = x0;
        for c in text.chars() {
            if let Some(&(gx, gy, gw, adv)) = self.glyphs.get(&c) {
                cv.mask(&self.img, gx, gy, gw, self.line, cx + 2, y + 2, [10, 6, 12], alpha * 0.85);
                for (dx, dy) in [(-1, 0), (1, 0), (0, -1), (0, 1), (1, 1)] {
                    cv.mask(&self.img, gx, gy, gw, self.line, cx + dx, y + dy, edge, alpha);
                }
                cx += adv;
            } else {
                cx += self.line / 2;
            }
        }
        let mut cx = x0;
        for c in text.chars() {
            if let Some(&(gx, gy, gw, adv)) = self.glyphs.get(&c) {
                cv.mask_grad(&self.img, gx, gy, gw, self.line, cx, y, top, bot, (px / 6, px), alpha);
                cx += adv;
            } else {
                cx += self.line / 2;
            }
        }
    }

    /// Text with its top at y; a dark outline round it and a shadow under it when `edge` is given (as the art's
    /// letters); faded by `alpha`.
    #[allow(clippy::too_many_arguments)]
    pub fn draw(&self, cv: &mut Image, text: &str, x: i32, y: i32, col: [u8; 3], edge: Option<[u8; 3]>, align: Align, alpha: f32) {
        let w = self.width(text);
        let x0 = match align {
            Align::Left => x,
            Align::Center => x - w / 2,
            Align::Right => x - w,
        };
        if let Some(e) = edge {
            let mut cx = x0;
            for c in text.chars() {
                if let Some(&(gx, gy, gw, adv)) = self.glyphs.get(&c) {
                    cv.mask(&self.img, gx, gy, gw, self.line, cx + 1, y + 2, [10, 6, 12], alpha * 0.8);
                    for (dx, dy) in [(-1, 0), (1, 0), (0, -1), (0, 1), (1, 1)] {
                        cv.mask(&self.img, gx, gy, gw, self.line, cx + dx, y + dy, e, alpha);
                    }
                    cx += adv;
                } else {
                    cx += self.line / 2;
                }
            }
        }
        let mut cx = x0;
        for c in text.chars() {
            if let Some(&(gx, gy, gw, adv)) = self.glyphs.get(&c) {
                cv.mask(&self.img, gx, gy, gw, self.line, cx, y, col, alpha);
                cx += adv;
            } else {
                cx += self.line / 2;
            }
        }
    }
}
