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

pub struct Assets {
    pub ground: Image,
    pub sprites: HashMap<String, Sprite>,
    pub fx: HashMap<String, Fx>,
    pub fonts: HashMap<String, Font>,
    pub ui: HashMap<String, Piece>,
}

pub fn dir() -> PathBuf {
    std::env::var_os("GAME_ASSETS").map(PathBuf::from).unwrap_or_else(|| Path::new(env!("CARGO_MANIFEST_DIR")).join("assets"))
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
            sprites.insert(k.clone(), Sprite { img: img(&v["file"])?, ox: i(&v["ox"]), oy: i(&v["oy"]) });
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
        Ok(Assets { ground: Image::load(&root.join("ground.png"))?, sprites, fx, fonts, ui })
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
