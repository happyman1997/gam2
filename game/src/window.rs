//! The window: winit for the window and the keys, pixels to put the picture on screen at the window's own size.
//! The field is drawn at 960×540 and shown through the camera (camera.rs) — the whole field while the armies stand
//! apart, closer on the clash; C turns the camera off (the whole field all the time). The interface is laid over it
//! at the largest whole factor that fits. The battle ticks at 24 fps (its sounds and blows), but the picture is drawn
//! at the screen's own rate, the walks between the ticks, so it moves smoothly on a 60 or 144 Hz screen.

use crate::camera::{self, Cam, Frame};
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
    field: gfx::Image,
    frame: Frame,
    cam: Cam,
    cam_on: bool,
    last: Instant,
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
        let (hx, hy) = self.frame.hud_point(x as i32, y as i32);
        render::button_at(&self.demo.rec, &self.demo.view, hx, hy)
    }

    /// The picture fills the window at its own size: the buffer follows the window.
    fn fit(&mut self, w: u32, h: u32) {
        let (w, h) = (w.max(render::W as u32), h.max(render::H as u32));
        if let Some(p) = &mut self.pixels {
            let _ = p.resize_surface(w, h);
            let _ = p.resize_buffer(w, h);
        }
        self.frame = Frame::fit(w as i32, h as i32);
        self.cam = camera::whole(&self.frame);
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
        let pixels = Pixels::new(size.width.max(1), size.height.max(1), surface).expect("pixels");
        self.window = Some(window);
        self.pixels = Some(pixels);
        self.fit(size.width, size.height);
        self.next = Instant::now();
    }

    fn window_event(&mut self, el: &ActiveEventLoop, _id: WindowId, event: WindowEvent) {
        match event {
            WindowEvent::CloseRequested => el.exit(),
            WindowEvent::Resized(s) => self.fit(s.width, s.height),
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
                Key::Character(ref c) if c.as_str() == "c" || c.as_str() == "с" => {
                    self.cam_on = !self.cam_on;
                    self.demo.ui_sound("toggle");
                }
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
                // the field and the interface on their 960×540 canvases, then through the camera to the window
                let (w, h) = (render::W, render::H);
                render::draw_field(&mut self.field, &self.demo.assets, &self.demo.rec, &self.demo.sparks, &self.demo.view);
                let mut hud = gfx::Image::clear(w, h);
                render::draw_hud(&mut hud, &self.demo.assets, &self.demo.rec, &self.demo.view);
                let ff = self.demo.view.frame;
                self.demo.view.frame = tick;
                let want = if self.cam_on {
                    camera::target(&self.demo.rec, ff.min((self.demo.rec.frames() - 1) as f32), &self.frame)
                } else {
                    camera::whole(&self.frame)
                };
                let secs = now.duration_since(self.last).as_secs_f32().min(0.1);
                self.last = now;
                camera::follow(&mut self.cam, want, secs, &self.frame);
                if let Some(p) = &mut self.pixels {
                    camera::compose(&self.field, &hud, self.cam, 1.0, p.frame_mut(), &self.frame, 4);
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
        field: gfx::Image::new(render::W, render::H),
        frame: Frame::fit(render::W * 2, render::H * 2),
        cam: Cam { cx: render::W as f32 / 2.0, cy: render::H as f32 / 2.0, z: 2.0 },
        cam_on: true,
        last: Instant::now(),
        next: Instant::now(),
        cursor: (0.0, 0.0),
    };
    el.run_app(&mut app).expect("run");
}
