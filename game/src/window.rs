//! The window: winit for the window, the mouse and the keys; pixels to put the picture on screen at the window's own
//! size. It runs the game (game.rs): the screens between battles drawn on the interface's 960×540 canvas over their
//! background, a battle's field shown through the camera (camera.rs) — the whole field while the armies stand apart,
//! closer on the clash. The interface is laid over at the largest whole factor that fits (or the one the settings
//! ask for). The battle ticks at 24 fps (its sounds and blows), but the picture is drawn at the screen's own rate, the
//! walks between the ticks, so it moves smoothly on a 60 or 144 Hz screen.
//!
//! It opens borderless over the whole screen, as a game does (or as a window, if the settings say so); F11 or
//! Alt+Enter switches. Minimised, nothing is drawn (the battle and its sounds go on).

use crate::camera::{self, Cam, Frame};
use crate::game::Game;
use crate::ui::Key;
use crate::{gfx, render, Demo};
use pixels::{Pixels, SurfaceTexture};
use std::sync::Arc;
use std::time::{Duration, Instant};
use winit::application::ApplicationHandler;
use winit::dpi::{PhysicalPosition, PhysicalSize};
use winit::event::{ElementState, MouseButton, MouseScrollDelta, WindowEvent};
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
    game: Game,
    window: Option<Arc<Window>>,
    pixels: Option<Pixels<'static>>,
    field: gfx::Image,
    size: (u32, u32),
    frame: Frame,
    cam: Cam,
    /// The mouse wheel's scroll not yet a whole step (a touchpad's).
    wheel: f32,
    last: Instant,
    next: Instant,
    cursor: (f32, f32),
    mods: ModifiersState,
    /// The window reported a size of nothing (Windows does so when it is minimised).
    zero: bool,
}

/// The output's frame, with the interface's whole factor as the settings ask (0 — the largest that fits).
fn frame_for(w: u32, h: u32, scale: u8) -> Frame {
    let mut fr = Frame::fit(w as i32, h as i32);
    if scale > 0 && (scale as i32) < fr.hud_scale {
        let s = scale as i32;
        fr.hud_scale = s;
        fr.hud_x0 = (w as i32 - render::W * s) / 2;
        fr.wing = 34.0 * s as f32;
    }
    fr
}

impl App {
    /// Minimised: nothing to draw.
    fn hidden(&self) -> bool {
        self.zero || self.window.as_ref().and_then(|w| w.is_minimized()) == Some(true)
    }

    /// The battle's ticks due by `now` (a few at most — after a stall it goes on from where it stood).
    fn advance(&mut self, now: Instant) {
        let mut n = 0;
        while self.next <= now && n < CATCH_UP {
            self.game.tick();
            self.next += TICK;
            n += 1;
        }
        if self.next <= now {
            self.next = now + TICK;
        }
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
        self.size = (w, h);
        // the camera keeps its place and how close it is, as a share of the new window
        let old = self.frame;
        self.frame = frame_for(w, h, self.game.settings.ui_scale);
        self.cam.z *= self.frame.zmin / old.zmin;
        self.cam = camera::clamp(self.cam, &self.frame);
    }

    /// Borderless over the whole screen, or a window: the largest whole multiple of 960×540 that leaves room for the
    /// title bar and the taskbar, in the middle of the screen.
    fn set_fullscreen(&mut self, full: bool) {
        let Some(w) = &self.window else { return };
        if !full {
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

    fn toggle_fullscreen(&mut self) {
        let full = self.window.as_ref().map(|w| w.fullscreen().is_none()).unwrap_or(true);
        self.game.settings.fullscreen = full;
        self.game.settings.save();
        self.set_fullscreen(full);
    }

    /// Where the mouse is on the interface's canvas.
    fn mouse_to_ui(&mut self) {
        let Some(px) = self.pixels.as_ref() else { return };
        match px.window_pos_to_pixel(self.cursor) {
            Ok((x, y)) => {
                let (hx, hy) = self.frame.hud_point(x as i32, y as i32);
                self.game.ui.mx = hx;
                self.game.ui.my = hy;
            }
            Err(_) => {
                self.game.ui.mx = -1;
                self.game.ui.my = -1;
            }
        }
    }

    fn draw(&mut self, now: Instant) {
        let dt = now.duration_since(self.last).as_secs_f32().min(0.1);
        self.last = now;
        let scale = self.game.settings.ui_scale;
        if self.frame.hud_scale != frame_for(self.size.0, self.size.1, scale).hud_scale {
            self.frame = frame_for(self.size.0, self.size.1, scale);
        }
        self.game.step_fade(dt);
        let battle = self.game.in_battle();
        let mut hud = gfx::Image::clear(render::W, render::H);
        let mut ff = 0.0;
        if battle {
            // between two ticks: the picture runs ahead by the part of a tick already gone, so a walk is smooth
            let d = &mut self.game.demo;
            let tick = d.view.frame;
            let end = (d.rec.frames() + 24) as f32;
            if !d.view.paused && tick < end && self.game.overlays.is_empty() {
                let part = 1.0 - (self.next.saturating_duration_since(now).as_secs_f32() / TICK.as_secs_f32()).clamp(0.0, 1.0);
                d.view.frame = (tick + part * d.view.speed as f32).min(end);
            }
            render::draw_field(&mut self.field, &d.assets, &d.rec, &d.sparks, &d.view);
            render::draw_hud(&mut hud, &d.assets, &d.rec, &d.view);
            ff = d.view.frame;
            d.view.frame = tick;
        } else {
            self.game.draw_bg(&mut self.field);
        }
        self.game.draw_ui(&mut hud);
        self.game.ui.end(dt);
        // the camera's level: how close it may come to the clash (0 — the whole field)
        let level = self.game.settings.cam_level();
        let want = if battle {
            camera::at_level(&self.game.demo.rec, ff, &self.frame, level, &crate::game::ZOOMS)
        } else {
            camera::whole(&self.frame)
        };
        if battle {
            camera::follow(&mut self.cam, want, dt, &self.frame);
        } else {
            self.cam = want;
        }
        let light = self.game.light();
        if let Some(p) = &mut self.pixels {
            camera::compose(&self.field, &hud, self.cam, light, p.frame_mut(), &self.frame, 4);
            if let Err(e) = p.render() {
                crate::fatal(&format!("Картинка перестала выводиться: {e}"));
            }
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
        let full = self.game.settings.fullscreen;
        let mut attrs = Window::default_attributes()
            .with_title("gam2")
            .with_min_inner_size(PhysicalSize::new(render::W as u32, render::H as u32));
        if full {
            attrs = attrs.with_fullscreen(Some(Fullscreen::Borderless(None)));
        } else {
            attrs = attrs.with_inner_size(PhysicalSize::new(render::W as u32, render::H as u32));
        }
        let window = Arc::new(el.create_window(attrs).unwrap_or_else(|e| crate::fatal(&format!("Окно не открылось: {e}"))));
        let size = window.inner_size();
        let surface = SurfaceTexture::new(size.width, size.height, window.clone());
        let pixels = Pixels::new(size.width.max(1), size.height.max(1), surface)
            .unwrap_or_else(|e| crate::fatal(&format!("Видеокарта не запустилась (нужен DirectX 12 или Vulkan; обновите драйвер):\n{e}")));
        self.window = Some(window);
        self.pixels = Some(pixels);
        self.fit(size.width, size.height);
        if !full {
            self.set_fullscreen(false);
        }
        self.next = Instant::now();
    }

    fn window_event(&mut self, el: &ActiveEventLoop, _id: WindowId, event: WindowEvent) {
        match event {
            WindowEvent::CloseRequested => el.exit(),
            WindowEvent::Resized(s) => self.fit(s.width, s.height),
            WindowEvent::CursorMoved { position, .. } => {
                self.cursor = (position.x as f32, position.y as f32);
                self.mouse_to_ui();
            }
            WindowEvent::CursorLeft { .. } => {
                self.game.ui.mx = -1;
                self.game.ui.my = -1;
            }
            WindowEvent::ModifiersChanged(m) => self.mods = m.state(),
            // Alt+Tab away: the Alt let go elsewhere must not stay held here
            WindowEvent::Focused(false) => self.mods = ModifiersState::empty(),
            WindowEvent::MouseInput { state, button: MouseButton::Left, .. } => match state {
                ElementState::Pressed => self.game.ui.mouse_down(),
                ElementState::Released => self.game.ui.mouse_up(),
            },
            // the wheel: a notch a step; a touchpad's smooth scroll gathered into steps of 40 pixels
            WindowEvent::MouseWheel { delta, .. } => {
                let dy = match delta {
                    MouseScrollDelta::LineDelta(_, y) => y,
                    MouseScrollDelta::PixelDelta(p) => p.y as f32 / 40.0,
                };
                self.wheel += dy;
                let steps = self.wheel.trunc();
                if steps != 0.0 {
                    self.wheel -= steps;
                    self.game.ui.wheel += steps as i32;
                }
            }
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
                let k = match code {
                    KeyCode::F11 => {
                        self.toggle_fullscreen();
                        None
                    }
                    KeyCode::Escape => Some(Key::Esc),
                    KeyCode::Enter | KeyCode::NumpadEnter => Some(Key::Enter),
                    KeyCode::Space => Some(Key::Space),
                    KeyCode::Tab => Some(Key::Tab),
                    KeyCode::End => Some(Key::End),
                    KeyCode::KeyR => Some(Key::R),
                    KeyCode::KeyC => Some(Key::C),
                    KeyCode::Minus | KeyCode::NumpadSubtract => Some(Key::ZoomOut),
                    KeyCode::Equal | KeyCode::NumpadAdd => Some(Key::ZoomIn),
                    KeyCode::Digit1 | KeyCode::Numpad1 => Some(Key::Digit(1)),
                    KeyCode::Digit2 | KeyCode::Numpad2 => Some(Key::Digit(2)),
                    KeyCode::Digit3 | KeyCode::Numpad3 => Some(Key::Digit(3)),
                    KeyCode::Digit4 | KeyCode::Numpad4 => Some(Key::Digit(4)),
                    _ => None,
                };
                if let Some(k) = k {
                    self.game.key(k);
                }
            }
            WindowEvent::RedrawRequested => {
                let now = Instant::now();
                self.advance(now);
                if self.hidden() {
                    return;
                }
                self.draw(now);
                if self.game.quit {
                    el.exit();
                }
                if let Some(full) = self.game.want_fullscreen.take() {
                    self.set_fullscreen(full);
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

pub fn run(mut demo: Demo) {
    #[cfg(feature = "audio")]
    {
        demo.audio = crate::audio::Audio::new();
        if demo.audio.is_none() {
            eprintln!("звук не включился: нет устройства или файлов в game/assets/sfx — играем без звука");
        }
    }
    let game = Game::new(demo);
    let el = EventLoop::new().unwrap_or_else(|e| crate::fatal(&format!("Окно не открылось: {e}")));
    let mut app = App {
        game,
        window: None,
        pixels: None,
        field: gfx::Image::new(render::W, render::H),
        size: (render::W as u32 * 2, render::H as u32 * 2),
        frame: Frame::fit(render::W * 2, render::H * 2),
        cam: Cam { cx: render::W as f32 / 2.0, cy: render::H as f32 / 2.0, z: 2.0 },
        wheel: 0.0,
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
