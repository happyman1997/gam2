//! The software frame: RGBA images, alpha blitting (optionally mirrored), rectangles, PNG in and out.

use std::fs::File;
use std::io::BufWriter;
use std::path::Path;

#[derive(Clone)]
pub struct Image {
    pub w: i32,
    pub h: i32,
    pub px: Vec<[u8; 4]>,
}

impl Image {
    pub fn new(w: i32, h: i32) -> Self {
        Image { w, h, px: vec![[0, 0, 0, 255]; (w * h) as usize] }
    }

    /// A clear image, to draw a layer on (the interface over a zoomed field).
    pub fn clear(w: i32, h: i32) -> Self {
        Image { w, h, px: vec![[0, 0, 0, 0]; (w * h) as usize] }
    }

    pub fn load(path: &Path) -> Result<Self, String> {
        let file = File::open(path).map_err(|e| format!("{}: {e}", path.display()))?;
        let mut dec = png::Decoder::new(file);
        dec.set_transformations(png::Transformations::EXPAND | png::Transformations::STRIP_16);
        let mut reader = dec.read_info().map_err(|e| format!("{}: {e}", path.display()))?;
        let mut buf = vec![0; reader.output_buffer_size()];
        let info = reader.next_frame(&mut buf).map_err(|e| format!("{}: {e}", path.display()))?;
        let (w, h) = (info.width as i32, info.height as i32);
        let n = (w * h) as usize;
        let mut px = Vec::with_capacity(n);
        for i in 0..n {
            px.push(match info.color_type {
                png::ColorType::Rgba => [buf[i * 4], buf[i * 4 + 1], buf[i * 4 + 2], buf[i * 4 + 3]],
                png::ColorType::Rgb => [buf[i * 3], buf[i * 3 + 1], buf[i * 3 + 2], 255],
                png::ColorType::GrayscaleAlpha => [buf[i * 2], buf[i * 2], buf[i * 2], buf[i * 2 + 1]],
                _ => [255, 255, 255, buf[i]], // grayscale: a font atlas — the value is the coverage
            });
        }
        Ok(Image { w, h, px })
    }

    pub fn save(&self, path: &Path) -> Result<(), String> {
        let file = File::create(path).map_err(|e| e.to_string())?;
        let mut enc = png::Encoder::new(BufWriter::new(file), self.w as u32, self.h as u32);
        enc.set_color(png::ColorType::Rgba);
        enc.set_depth(png::BitDepth::Eight);
        let mut wr = enc.write_header().map_err(|e| e.to_string())?;
        let data: Vec<u8> = self.px.iter().flat_map(|p| p.iter().copied()).collect();
        wr.write_image_data(&data).map_err(|e| e.to_string())
    }

    #[inline]
    pub fn get(&self, x: i32, y: i32) -> [u8; 4] {
        self.px[(y * self.w + x) as usize]
    }

    #[inline]
    pub fn blend_px(&mut self, x: i32, y: i32, c: [u8; 4], alpha: f32) {
        if x < 0 || y < 0 || x >= self.w || y >= self.h {
            return;
        }
        let a = c[3] as f32 / 255.0 * alpha;
        if a <= 0.0 {
            return;
        }
        let d = &mut self.px[(y * self.w + x) as usize];
        if d[3] == 255 {
            for k in 0..3 {
                d[k] = (d[k] as f32 * (1.0 - a) + c[k] as f32 * a).round() as u8;
            }
            return;
        }
        // over a clear or see-through pixel: the colours weighed by their coverage
        let da = d[3] as f32 / 255.0;
        let oa = a + da * (1.0 - a);
        for k in 0..3 {
            d[k] = ((c[k] as f32 * a + d[k] as f32 * da * (1.0 - a)) / oa).round() as u8;
        }
        d[3] = (oa * 255.0).round() as u8;
    }

    /// `src` with its top-left at (x, y); mirrored left-right if asked; faded by `alpha`.
    pub fn blit(&mut self, src: &Image, x: i32, y: i32, flip: bool, alpha: f32) {
        self.blit_region(src, 0, 0, src.w, src.h, x, y, flip, alpha);
    }

    #[allow(clippy::too_many_arguments)]
    pub fn blit_region(&mut self, src: &Image, sx: i32, sy: i32, sw: i32, sh: i32, x: i32, y: i32, flip: bool, alpha: f32) {
        for j in 0..sh {
            let dy = y + j;
            if dy < 0 || dy >= self.h {
                continue;
            }
            for i in 0..sw {
                let dx = x + i;
                if dx < 0 || dx >= self.w {
                    continue;
                }
                let si = if flip { sw - 1 - i } else { i };
                let c = src.get(sx + si, sy + j);
                if c[3] == 0 {
                    continue;
                }
                self.blend_px(dx, dy, c, alpha);
            }
        }
    }

    /// `src` darkened by `mul` and drained of colour by `grey` (0..1): a body that is dead, under the living.
    pub fn blit_shade(&mut self, src: &Image, x: i32, y: i32, flip: bool, mul: f32, grey: f32) {
        self.blit_shade_to(src, x, y, flip, mul, grey, [0, 0, 0], 0.0);
    }

    /// As `blit_shade`, then pulled toward `to` by `k` — an old corpse sinking into the ground's colour (opaque,
    /// in steps: no see-through).
    #[allow(clippy::too_many_arguments)]
    pub fn blit_shade_to(&mut self, src: &Image, x: i32, y: i32, flip: bool, mul: f32, grey: f32, to: [u8; 3], k: f32) {
        for j in 0..src.h {
            for i in 0..src.w {
                let si = if flip { src.w - 1 - i } else { i };
                let c = src.get(si, j);
                if c[3] == 0 {
                    continue;
                }
                let l = (c[0] as f32 * 0.3 + c[1] as f32 * 0.59 + c[2] as f32 * 0.11) * (1.0 - 0.15 * grey);
                let s = |v: u8, t: u8| {
                    let d = (v as f32 * (1.0 - grey) + l * grey) * mul;
                    (d + (t as f32 - d) * k).clamp(0.0, 255.0) as u8
                };
                self.blend_px(x + i, y + j, [s(c[0], to[0]), s(c[1], to[1]), s(c[2], to[2]), c[3]], 1.0);
            }
        }
    }

    /// `src` with every pixel pulled toward `col` by `k` (a body flashing as a blow lands).
    pub fn blit_tint(&mut self, src: &Image, x: i32, y: i32, flip: bool, col: [u8; 3], k: f32) {
        for j in 0..src.h {
            for i in 0..src.w {
                let si = if flip { src.w - 1 - i } else { i };
                let c = src.get(si, j);
                if c[3] == 0 {
                    continue;
                }
                let m = |v: u8, t: u8| (v as f32 + (t as f32 - v as f32) * k) as u8;
                self.blend_px(x + i, y + j, [m(c[0], col[0]), m(c[1], col[1]), m(c[2], col[2]), c[3]], 1.0);
            }
        }
    }

    /// As `blit_tint`, faded by `alpha`: a ghost of the Hive Mind's mirage.
    #[allow(clippy::too_many_arguments)]
    pub fn blit_tint_faded(&mut self, src: &Image, x: i32, y: i32, flip: bool, col: [u8; 3], k: f32, alpha: f32) {
        for j in 0..src.h {
            for i in 0..src.w {
                let si = if flip { src.w - 1 - i } else { i };
                let c = src.get(si, j);
                if c[3] == 0 {
                    continue;
                }
                let m = |v: u8, t: u8| (v as f32 + (t as f32 - v as f32) * k) as u8;
                self.blend_px(x + i, y + j, [m(c[0], col[0]), m(c[1], col[1]), m(c[2], col[2]), c[3]], alpha);
            }
        }
    }

    /// Every covered pixel of the image lifted toward white by `k` (a button under the cursor).
    pub fn lighten(&mut self, k: f32) {
        for p in self.px.iter_mut().filter(|p| p[3] > 0) {
            for c in p.iter_mut().take(3) {
                *c = (*c as f32 + (255.0 - *c as f32) * k) as u8;
            }
        }
    }

    /// A coverage mask (a font glyph) in one colour.
    #[allow(clippy::too_many_arguments)]
    pub fn mask(&mut self, src: &Image, sx: i32, sy: i32, sw: i32, sh: i32, x: i32, y: i32, col: [u8; 3], alpha: f32) {
        for j in 0..sh {
            for i in 0..sw {
                let a = src.get(sx + i, sy + j)[3];
                if a > 0 {
                    self.blend_px(x + i, y + j, [col[0], col[1], col[2], a], alpha);
                }
            }
        }
    }

    pub fn fill(&mut self, x: i32, y: i32, w: i32, h: i32, c: [u8; 4]) {
        for j in y.max(0)..(y + h).min(self.h) {
            for i in x.max(0)..(x + w).min(self.w) {
                self.blend_px(i, j, c, 1.0);
            }
        }
    }

    /// Multiply a rectangle's colour (dim it).
    pub fn dim(&mut self, x: i32, y: i32, w: i32, h: i32, k: f32) {
        for j in y.max(0)..(y + h).min(self.h) {
            for i in x.max(0)..(x + w).min(self.w) {
                let d = &mut self.px[(j * self.w + i) as usize];
                for c in d.iter_mut().take(3) {
                    *c = (*c as f32 * k) as u8;
                }
            }
        }
    }

    /// An ellipse darkened under a body (its shadow).
    pub fn shadow(&mut self, cx: f32, cy: f32, w: f32, h: f32) {
        let (rx, ry) = (w / 2.0, h / 2.0);
        for j in (cy - ry) as i32..=(cy + ry) as i32 {
            for i in (cx - rx) as i32..=(cx + rx) as i32 {
                let (dx, dy) = ((i as f32 - cx) / rx, (j as f32 - cy) / ry);
                if dx * dx + dy * dy <= 1.0 && i >= 0 && j >= 0 && i < self.w && j < self.h {
                    let d = &mut self.px[(j * self.w + i) as usize];
                    for c in d.iter_mut().take(3) {
                        *c = (*c as f32 * 0.62) as u8;
                    }
                }
            }
        }
    }

    /// Light added round a point, falling off to the rim (a fire's glow, a button lit, a lantern): additive, so it
    /// brightens what is under it without covering it.
    pub fn glow(&mut self, cx: f32, cy: f32, r: f32, col: [u8; 3], k: f32) {
        if r <= 0.0 || k <= 0.0 {
            return;
        }
        for j in (cy - r) as i32..=(cy + r) as i32 {
            for i in (cx - r) as i32..=(cx + r) as i32 {
                if i < 0 || j < 0 || i >= self.w || j >= self.h {
                    continue;
                }
                let d = ((i as f32 - cx).hypot(j as f32 - cy) / r).min(1.0);
                let a = (1.0 - d) * (1.0 - d) * k;
                if a <= 0.004 {
                    continue;
                }
                let p = &mut self.px[(j * self.w + i) as usize];
                for c in 0..3 {
                    p[c] = (p[c] as f32 + col[c] as f32 * a).min(255.0) as u8;
                }
                if p[3] < 255 {
                    p[3] = (p[3] as f32 + 255.0 * a).min(255.0) as u8;
                }
            }
        }
    }

    /// A copy `k` times larger, each pixel a k×k block (an icon at a card's size).
    pub fn scaled(&self, k: i32) -> Image {
        let mut out = Image::clear(self.w * k, self.h * k);
        for y in 0..out.h {
            for x in 0..out.w {
                out.px[(y * out.w + x) as usize] = self.get(x / k, y / k);
            }
        }
        out
    }

    /// A region cut out as its own image.
    pub fn crop(&self, x: i32, y: i32, w: i32, h: i32) -> Image {
        let mut out = Image::clear(w, h);
        for j in 0..h {
            for i in 0..w {
                if x + i >= 0 && y + j >= 0 && x + i < self.w && y + j < self.h {
                    out.px[(j * w + i) as usize] = self.get(x + i, y + j);
                }
            }
        }
        out
    }

    /// The piece grown to w×h the way the kit's pieces grow (tools/sprites/engine_kit.py `grow`): the corners as
    /// they are, the edges and the middle repeating their strips — the columns `tx` along the top and bottom, the
    /// rows `ty` down the sides — cut at the far end. `sl` = (left, top, right, bottom); a 3-slice has top = bottom
    /// = 0 and keeps its own height.
    pub fn grow(&self, w: i32, h: i32, sl: [i32; 4], tx: (i32, i32), ty: (i32, i32)) -> Image {
        let [l, t, r, b] = sl;
        let axis = |n: i32, lo: i32, hi: i32, tile: (i32, i32), full: i32| -> Vec<i32> {
            let mut v: Vec<i32> = (0..lo).collect();
            let period = (tile.1 - tile.0).max(1);
            for k in 0..(n - lo - hi).max(0) {
                v.push(tile.0 + k % period);
            }
            v.extend(full - hi..full);
            v
        };
        let xs = axis(w, l, r, tx, self.w);
        let ys = axis(h, t, b, ty, self.h);
        let mut out = Image::clear(xs.len() as i32, ys.len() as i32);
        for (j, &sy) in ys.iter().enumerate() {
            for (i, &sx) in xs.iter().enumerate() {
                out.px[j * xs.len() + i] = self.get(sx.clamp(0, self.w - 1), sy.clamp(0, self.h - 1));
            }
        }
        out
    }

    /// A coverage mask (a title's letters) in a colour running from `top` to `bot` down its rows `y0..y1`.
    #[allow(clippy::too_many_arguments)]
    pub fn mask_grad(&mut self, src: &Image, sx: i32, sy: i32, sw: i32, sh: i32, x: i32, y: i32, top: [u8; 3], bot: [u8; 3], rows: (i32, i32), alpha: f32) {
        for j in 0..sh {
            let t = ((j - rows.0) as f32 / (rows.1 - rows.0).max(1) as f32).clamp(0.0, 1.0);
            let col = [0, 1, 2].map(|k| (top[k] as f32 + (bot[k] as f32 - top[k] as f32) * t) as u8);
            for i in 0..sw {
                let a = src.get(sx + i, sy + j)[3];
                if a > 0 {
                    self.blend_px(x + i, y + j, [col[0], col[1], col[2], a], alpha);
                }
            }
        }
    }

    /// A piece grown to a new width along its middle (a 3-slice): `left`/`right` stay, the columns
    /// `tile.0..tile.1` repeat.
    #[allow(clippy::too_many_arguments)]
    pub fn three_slice(&mut self, src: &Image, x: i32, y: i32, w: i32, left: i32, right: i32, tile: (i32, i32)) {
        self.blit_region(src, 0, 0, left, src.h, x, y, false, 1.0);
        let mut dx = left;
        let period = (tile.1 - tile.0).max(1);
        while dx < w - right {
            let n = period.min(w - right - dx);
            self.blit_region(src, tile.0, 0, n, src.h, x + dx, y, false, 1.0);
            dx += n;
        }
        self.blit_region(src, src.w - right, 0, right, src.h, x + w - right, y, false, 1.0);
    }
}
