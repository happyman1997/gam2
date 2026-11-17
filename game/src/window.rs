//! The window: winit for the window and the keys, pixels to put the picture on screen at the window's own size.
//! It opens borderless over the whole screen, as a game does; F11 or Alt+Enter turns it into a window that fits the
//! screen and back. Minimised, nothing is drawn (the battle and its sounds go on).
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
use winit::dpi::{PhysicalPosition, PhysicalSize};
use winit::event::{ElementState, MouseButton, WindowEvent};
use winit::event_loop::{ActiveEventLoop, ControlFlow, EventLoop};
use winit::keyboard::{KeyCode, ModifiersState, PhysicalKey};
use winit::window::{Fullscreen, Window, WindowId};

const TICK: Duration = Duration::from_nanos(1_000_000_000 / 24);
/// The most ticks one frame catches up on: after a stall (the window dragged, the machine asleep) the battle goes on
/// from where it stood, not leaping ahead with a burst of every sound it missed.
const CATCH_UP: u32 = 3;
/// The shortest time between two pictures — a floor for when the screen does not hold the frame back (a covered
/// window), so the loop does not spin a core.
const MIN_FRAME: Duration = Duration::from_micros(3_300);

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
    mods: ModifiersState,
    /// The window reported a size of nothing (Windows does so when it is minimised).
    zero: bool,
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

    /// Minimised: nothing to draw.
    fn hidden(&self) -> bool {
        self.zero || self.window.as_ref().and_then(|w| w.is_minimized()) == Some(true)
    }

    /// The battle's ticks due by `now` (a few at most — after a stall it goes on from where it stood).
    fn advance(&mut self, now: Instant) {
        let mut n = 0;
        while self.next <= now && n < CATCH_UP {
            self.demo.tick();
            self.next += TICK;
            n += 1;
        }
        if self.next <= now {
            self.next = now + TICK;
        }
    }

    /// The button under the cursor, if any.
    fn under_cursor(&self) -> Option<render::Button> {
        let px = self.pixels.as_ref()?;
        let (x, y) = px.window_pos_to_pixel(self.cursor).ok()?;
        let (hx, hy) = self.frame.hud_point(x as i32, y as i32);
        render::button_at(&self.demo.rec, &self.demo.view, hx, hy)
    }

    /// The picture fills the window at its own size: the buffer follows the window. A minimised window reports a
    /// size of nothing — then the surface is left as it was (a surface of no size cannot be made) and nothing drawn.
    fn fit(&mut self, w: u32, h: u32) {
        self.zero = w == 0 || h == 0;
        if self.zero {
            return;
        }
        if let Some(p) = &mut self.pixels {
            if p.resize_surface(w, h).is_err() || p.resize_buffer(w, h).is_err() {
                return;
            }
        }
        // the camera keeps its place and how close it is, as a share of the new window
        let old = self.frame;
        self.frame = Frame::fit(w as i32, h as i32);
        self.cam.z *= self.frame.zmin / old.zmin;
        self.cam = camera::clamp(self.cam, &self.frame);
    }

    /// Borderless over the whole screen, or a window: the largest whole multiple of 960×540 that leaves room for the
    /// title bar and the taskbar, in the middle of the screen.
    fn toggle_fullscreen(&mut self) {
        let Some(w) = &self.window else { return };
        if w.fullscreen().is_some() {
            w.set_fullscreen(None);
            if let Some(m) = w.current_monitor() {
                let (mw, mh) = (m.size().width as f32, m.size().height as f32);
                let k = ((mw * 0.92 / render::W as f32).min(mh * 0.86 / render::H as f32).floor() as u32).max(1);
                let (ww, wh) = (render::W as u32 * k, render::H as u32 * k);
                let _ = w.request_inner_size(PhysicalSize::new(ww, wh));
                let p = m.position();
                w.set_outer_position(PhysicalPosition::new(p.x + (mw as i32 - ww as i32) / 2, p.y + (mh as i32 - wh as i32 - 40).max(0) / 2));
            }
        } else {
            w.set_fullscreen(Some(Fullscreen::Borderless(None)));
        }
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
        // borderless over the whole screen: a window of 1920×1080 would not fit a 1080p screen with its title bar and
        // taskbar, nor any screen scaled by Windows (125 %, 150 %)
        let attrs = Window::default_attributes()
            .with_title("gam2 — техно-демо")
            .with_fullscreen(Some(Fullscreen::Borderless(None)))
            .with_min_inner_size(PhysicalSize::new(render::W as u32, render::H as u32));
        let window = Arc::new(el.create_window(attrs).unwrap_or_else(|e| crate::fatal(&format!("Окно не открылось: {e}"))));
        let size = window.inner_size();
        let surface = SurfaceTexture::new(size.width, size.height, window.clone());
        let pixels = Pixels::new(size.width.max(1), size.height.max(1), surface)
            .unwrap_or_else(|e| crate::fatal(&format!("Видеокарта не запустилась (нужен DirectX 12 или Vulkan; обновите драйвер):\n{e}")));
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
            WindowEvent::CursorLeft { .. } => self.demo.view.hover = None,
            WindowEvent::ModifiersChanged(m) => self.mods = m.state(),
            // Alt+Tab away: the Alt let go elsewhere must not stay held here
            WindowEvent::Focused(false) => self.mods = ModifiersState::empty(),
            WindowEvent::MouseInput { state: ElementState::Pressed, button: MouseButton::Left, .. } => self.click(),
            // keys by their place on the keyboard, not their letter: R and C work in any layout, with Caps Lock too;
            // a held key does not repeat its action; with Alt held only Alt+Enter counts (Alt+Tab is the system's)
            WindowEvent::KeyboardInput { event, .. } if event.state == ElementState::Pressed && !event.repeat => {
                let PhysicalKey::Code(code) = event.physical_key else { return };
                if self.mods.alt_key() {
                    if matches!(code, KeyCode::Enter | KeyCode::NumpadEnter) {
                        self.toggle_fullscreen();
                    }
                    return;
                }
                match code {
                    KeyCode::Escape => el.exit(),
                    KeyCode::F11 => self.toggle_fullscreen(),
                    KeyCode::Space => self.pause(),
                    KeyCode::Tab => self.speed_up(),
                    KeyCode::End => self.skip_to_end(),
                    KeyCode::KeyR => self.new_battle(),
                    KeyCode::KeyC => {
                        self.cam_on = !self.cam_on;
                        self.demo.ui_sound("toggle");
                    }
                    _ => {}
                }
            }
            WindowEvent::RedrawRequested => {
                let now = Instant::now();
                self.advance(now);
                if self.hidden() {
                    return;
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
                    if let Err(e) = p.render() {
                        crate::fatal(&format!("Картинка перестала выводиться: {e}"));
                    }
                }
            }
            _ => {}
        }
    }

    fn about_to_wait(&mut self, el: &ActiveEventLoop) {
        // draw as often as the screen shows (pixels waits for its refresh), not only on a tick — but no more often
        // than MIN_FRAME; minimised, nothing is drawn: wake only for the battle's ticks
        let now = Instant::now();
        if self.hidden() {
            self.advance(now);
            el.set_control_flow(ControlFlow::WaitUntil(self.next));
        } else if now >= self.last + MIN_FRAME {
            if let Some(w) = &self.window {
                w.request_redraw();
            }
            el.set_control_flow(ControlFlow::Wait);
        } else {
            el.set_control_flow(ControlFlow::WaitUntil(self.last + MIN_FRAME));
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
    let el = EventLoop::new().unwrap_or_else(|e| crate::fatal(&format!("Окно не открылось: {e}")));
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
        mods: ModifiersState::empty(),
        zero: false,
    };
    if let Err(e) = el.run_app(&mut app) {
        crate::fatal(&format!("Окно закрылось с ошибкой: {e}"));
    }
}
