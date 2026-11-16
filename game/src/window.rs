//! The window: winit for the window and the keys, pixels to put the 960×540 frame on screen at a whole factor
//! (pixels scales by the largest whole multiple that fits and letterboxes the rest). The battle ticks at 24 fps (its
//! sounds and blows), but the picture is drawn at the screen's own rate, the walks between the ticks, so it moves
//! smoothly on a 60 or 144 Hz screen.

use crate::{gfx, render, Demo};
use pixels::{Pixels, SurfaceTexture};
use std::sync::Arc;
use std::time::{Duration, Instant};
use winit::application::ApplicationHandler;
use winit::dpi::LogicalSize;
use winit::event::{ElementState, MouseButton, WindowEvent};
use winit::event_loop::{ActiveEventLoop, ControlFlow, EventLoop};
use winit::keyboard::{Key, NamedKey};
use winit::window::{Window, WindowId};

const TICK: Duration = Duration::from_nanos(1_000_000_000 / 24);

struct App {
    demo: Demo,
    seed: u64,
    window: Option<Arc<Window>>,
    pixels: Option<Pixels<'static>>,
    canvas: gfx::Image,
    next: Instant,
    cursor: (f32, f32),
}

impl App {
    fn speed_up(&mut self) {
        self.demo.view.speed = match self.demo.view.speed {
            1 => 2,
            2 => 4,
            _ => 1,
        };
        self.demo.view.paused = false;
        self.demo.ui_sound("toggle");
    }

    fn skip_to_end(&mut self) {
        self.demo.view.frame = (self.demo.rec.frames() - 1) as f32;
        self.demo.ui_sound("click");
    }

    fn pause(&mut self) {
        self.demo.view.paused = !self.demo.view.paused;
        self.demo.ui_sound("toggle");
    }

    fn new_battle(&mut self) {
        self.seed = self.seed.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407) >> 16;
        self.demo.restart(self.seed);
        self.demo.ui_sound("click");
    }

    /// The button under the cursor, if any.
    fn under_cursor(&self) -> Option<render::Button> {
        let px = self.pixels.as_ref()?;
        let (x, y) = px.window_pos_to_pixel(self.cursor).ok()?;
        render::button_at(&self.demo.rec, &self.demo.view, x as i32, y as i32)
    }

    fn click(&mut self) {
        match self.under_cursor() {
            Some(render::Button::Pause) => self.pause(),
            Some(render::Button::Speed) => self.speed_up(),
            Some(render::Button::ToEnd) => self.skip_to_end(),
            Some(render::Button::NewBattle) => self.new_battle(),
            None => {}
        }
    }
}

impl ApplicationHandler for App {
    fn resumed(&mut self, el: &ActiveEventLoop) {
        if self.window.is_some() {
            return;
        }
        let attrs = Window::default_attributes()
            .with_title("gam2 — техно-демо")
            .with_inner_size(LogicalSize::new(1920.0, 1080.0))
            .with_min_inner_size(LogicalSize::new(render::W as f64, render::H as f64));
        let window = Arc::new(el.create_window(attrs).expect("window"));
        let size = window.inner_size();
        let surface = SurfaceTexture::new(size.width, size.height, window.clone());
        let pixels = Pixels::new(render::W as u32, render::H as u32, surface).expect("pixels");
        self.window = Some(window);
        self.pixels = Some(pixels);
        self.next = Instant::now();
    }

    fn window_event(&mut self, el: &ActiveEventLoop, _id: WindowId, event: WindowEvent) {
        match event {
            WindowEvent::CloseRequested => el.exit(),
            WindowEvent::Resized(s) => {
                if let Some(p) = &mut self.pixels {
                    let _ = p.resize_surface(s.width.max(1), s.height.max(1));
                }
            }
            WindowEvent::CursorMoved { position, .. } => {
                self.cursor = (position.x as f32, position.y as f32);
                self.demo.view.hover = self.under_cursor();
            }
            WindowEvent::MouseInput { state: ElementState::Pressed, button: MouseButton::Left, .. } => self.click(),
            WindowEvent::KeyboardInput { event, .. } if event.state == ElementState::Pressed => match event.logical_key {
                Key::Named(NamedKey::Escape) => el.exit(),
                Key::Named(NamedKey::Space) => self.pause(),
                Key::Named(NamedKey::Tab) => self.speed_up(),
                Key::Named(NamedKey::End) => self.skip_to_end(),
                Key::Character(ref c) if c.as_str() == "r" || c.as_str() == "к" => self.new_battle(),
                _ => {}
            },
            WindowEvent::RedrawRequested => {
                let now = Instant::now();
                while self.next <= now {
                    self.demo.tick();
                    self.next += TICK;
                }
                // between two ticks: the picture runs ahead by the part of a tick already gone, so a walk is smooth
                let tick = self.demo.view.frame;
                let end = (self.demo.rec.frames() + 24) as f32;
                if !self.demo.view.paused && tick < end {
                    let part = 1.0 - (self.next.saturating_duration_since(now).as_secs_f32() / TICK.as_secs_f32()).clamp(0.0, 1.0);
                    self.demo.view.frame = (tick + part * self.demo.view.speed as f32).min(end);
                }
                self.demo.draw(&mut self.canvas);
                self.demo.view.frame = tick;
                if let Some(p) = &mut self.pixels {
                    for (dst, src) in p.frame_mut().chunks_exact_mut(4).zip(self.canvas.px.iter()) {
                        dst.copy_from_slice(src);
                    }
                    if p.render().is_err() {
                        el.exit();
                    }
                }
            }
            _ => {}
        }
    }

    fn about_to_wait(&mut self, el: &ActiveEventLoop) {
        // draw as often as the screen shows (pixels waits for its refresh), not only on a tick
        el.set_control_flow(ControlFlow::Poll);
        if let Some(w) = &self.window {
            w.request_redraw();
        }
    }
}

pub fn run(mut demo: Demo, seed: u64) {
    #[cfg(feature = "audio")]
    {
        demo.audio = crate::audio::Audio::new();
        if demo.audio.is_none() {
            eprintln!("звук не включился: нет устройства или файлов в game/assets/sfx — играем без звука");
        }
    }
    let el = EventLoop::new().expect("event loop");
    let mut app = App {
        demo,
        seed,
        window: None,
        pixels: None,
        canvas: gfx::Image::new(render::W, render::H),
        next: Instant::now(),
        cursor: (0.0, 0.0),
    };
    el.run_app(&mut app).expect("run");
}
