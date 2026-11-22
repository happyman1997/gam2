//! The game: the screens one after another — the menu, the class, the leader, then the run: the fork of roads, a
//! battle, its spoils, the trader, an event, the camp, the end of the run — with the pause, the settings and the
//! army over any of them. A screen is a state here; how it looks is screens.rs. Between two screens the picture
//! dips through black for a moment.
//!
//! The run is sim::run (deterministic, saved after every step: «Продолжить» in the menu takes it up again). A
//! battle of the run is played back by the same machinery as the demo's (playback.rs, render.rs).

use crate::playback;
use crate::render;
use crate::ui::{Key, Ui};
use crate::Demo;
use serde::{Deserialize, Serialize};
use sim::run::{self, Class, Node, Reward, Run, Shop};
use std::path::PathBuf;

/// The player's settings, kept between games (settings.json in the game's folder of the user's data).
#[derive(Clone, Serialize, Deserialize)]
pub struct Settings {
    /// 0..=10.
    pub volume: u8,
    pub fullscreen: bool,
    pub camera: bool,
    /// How close the battle's camera may come, 1..=4 (with `camera` off — the whole field); the last one kept.
    #[serde(default = "zoom_default")]
    pub zoom: u8,
    /// First-time hints on; which of them were seen (a bit each).
    #[serde(default = "yes")]
    pub hints: bool,
    #[serde(default)]
    pub hints_seen: u32,
    /// The interface's whole factor: 0 — the largest that fits.
    pub ui_scale: u8,
    /// The battle's speed at its start: 1, 2 or 4.
    pub speed: u32,
}

impl Default for Settings {
    fn default() -> Self {
        Settings { volume: 8, fullscreen: true, camera: true, ui_scale: 0, speed: 1, zoom: ZOOM_DEFAULT, hints: true, hints_seen: 0 }
    }
}

/// The camera's levels: 0 — the whole field, then how close it may come (as many times the whole field).
pub const ZOOMS: [f32; 5] = [1.0, 1.2, 1.5, 1.85, 2.25];
const ZOOM_DEFAULT: u8 = 2;

fn zoom_default() -> u8 {
    ZOOM_DEFAULT
}

fn yes() -> bool {
    true
}

/// The screens with a first-time hint: the leaders, the fork, a battle, the spoils, the trader, the camp.
pub const HINTS: u8 = 6;

impl Settings {
    /// The camera's level now: 0 — the whole field (the camera off), 1..=4 — how close it may come.
    pub fn cam_level(&self) -> u8 {
        if self.camera {
            self.zoom.clamp(1, 4)
        } else {
            0
        }
    }

    /// The camera set to a level; 0 turns it off and keeps the last level for when it comes back on.
    pub fn set_cam_level(&mut self, l: u8) {
        self.camera = l > 0;
        if l > 0 {
            self.zoom = l.min(4);
        }
    }
}

/// Where the game keeps the player's things: %APPDATA%\gam2 on Windows (elsewhere ~/.local/share/gam2).
pub fn data_dir() -> PathBuf {
    let base = std::env::var_os("APPDATA")
        .map(PathBuf::from)
        .or_else(|| std::env::var_os("HOME").map(|h| PathBuf::from(h).join(".local").join("share")))
        .unwrap_or_else(|| PathBuf::from("."));
    base.join("gam2")
}

impl Settings {
    pub fn load() -> Settings {
        std::fs::read_to_string(data_dir().join("settings.json")).ok().and_then(|s| serde_json::from_str(&s).ok()).unwrap_or_default()
    }
    pub fn save(&self) {
        let _ = std::fs::create_dir_all(data_dir());
        let _ = std::fs::write(data_dir().join("settings.json"), serde_json::to_string_pretty(self).unwrap_or_default());
    }
}

fn save_path() -> PathBuf {
    data_dir().join("run.json")
}

pub fn load_run() -> Option<Run> {
    std::fs::read_to_string(save_path()).ok().and_then(|s| serde_json::from_str(&s).ok())
}

#[derive(Clone, Copy, PartialEq, Debug)]
pub enum CampStage {
    Choose,
    Pick,
    Done,
    /// The Foundry's workshop at the camp: modules moved between golems, melted into others; `held` — the module
    /// picked up (member, cell).
    Workshop { held: Option<(usize, usize)> },
}

pub enum Screen {
    Menu,
    Class,
    Leaders { class: Class, chosen: usize },
    Fork,
    Battle { node: Node },
    /// The spoils: each with whether it was taken; `pick` — the find being chosen from.
    Rewards { list: Vec<(Reward, bool)>, pick: Option<usize> },
    Shop(Shop),
    /// An event; `done` — what came of the option taken.
    Event { id: usize, done: Option<String> },
    Camp { stage: CampStage, said: String },
    End { victory: bool },
}

/// A module or a mutation on its way to where it goes: from the spoils (which reward) or the trader (which good).
#[derive(Clone, Debug)]
pub struct Targeting {
    pub offer: sim::run::Offer,
    pub from: From,
}

#[derive(Clone, Copy, Debug, PartialEq)]
pub enum From {
    Reward(usize),
    Shop(usize),
}

#[derive(Clone, Copy, PartialEq, Debug)]
pub enum Overlay {
    Pause,
    Settings,
    Army,
    About,
    /// The swarm's evolutions of its forms, for biomass (from the spoils and the Hive).
    Evolution,
    /// A roster to look at (an enemy, a recruit, a leader's start, the battle's fighters): `Game::inspect`.
    Inspect,
    /// The help: the keys, the battle, the run, the icons (`Game::help_tab`).
    Help,
    /// A first-time hint about the screen (its number, `HINTS`).
    Hint(u8),
    /// «Are you sure?» before something that cannot be undone.
    Confirm(Ask),
}

/// What is asked about before it is done.
#[derive(Clone, Copy, PartialEq, Debug)]
pub enum Ask {
    Surrender,
    ToMenu,
    Quit,
}

/// What a battle came to: how long, how many of the enemy fell, ours lost (a body, how many, broken — a golem —
/// or dead), the one of ours who killed most.
#[derive(Clone)]
pub struct Summary {
    pub rounds: u32,
    pub kills: u32,
    pub lost: Vec<(sim::model::Template, usize, bool)>,
    pub best: Option<(sim::model::Template, u32)>,
}

pub struct Game {
    pub demo: Demo,
    pub ui: Ui,
    pub screen: Screen,
    pub overlays: Vec<Overlay>,
    pub run: Option<Run>,
    pub settings: Settings,
    /// How dark the picture is (a dip between screens), and the screen to go to at the bottom of the dip.
    pub(crate) fade: f32,
    pub(crate) next: Option<Screen>,
    pub quit: bool,
    /// The window should go full screen (true) or windowed (false).
    pub want_fullscreen: Option<bool>,
    /// The saved run, if there is one (for «Продолжить»).
    pub saved: Option<(u32, Class)>,
    /// The currency as last drawn, and the changes floating up from it: (when, how much).
    pub(crate) money_seen: Option<i32>,
    pub(crate) floats: Vec<(f32, i32)>,
    /// Work for the moment the shutters are shut (it takes a few battles played out, a tenth of a second or two:
    /// done there, it shows as no stall): a run to begin, the next fork to build.
    pending_run: Option<(Class, usize, u64)>,
    fork_due: bool,
    /// A module or a mutation being given a place (over the screen, under the overlays).
    pub targeting: Option<Targeting>,
    /// When the camera's level was last changed in battle (its note shows for a moment).
    pub cam_note: Option<f32>,
    /// The army's view: the row picked (its sheet shown), the first row of the list on screen.
    pub army_sel: usize,
    pub army_top: usize,
    /// What the Inspect overlay shows: its title and rows.
    pub inspect: Option<(String, Vec<crate::screens::SheetItem>)>,
    /// Where the mouse is on the battlefield, in its art pixels (the window works it out through the camera).
    pub field_mouse: Option<(f32, f32)>,
    /// The bodies of the battle being watched, in its units' order (ours, then the enemy's).
    pub battle_bodies: Vec<sim::model::Template>,
    /// What the last battle came to, for the spoils' screen.
    pub summary: Option<Summary>,
    /// The help's page.
    pub help_tab: usize,
    /// How far down the picked body's sheet is scrolled (lines).
    pub sheet_top: usize,
}

impl Game {
    pub fn new(demo: Demo) -> Game {
        let mut settings = Settings::load();
        // the tests click their way through the screens: no first-time hints in their way
        if cfg!(test) {
            settings.hints = false;
        }
        let saved = load_run().filter(|r| r.over.is_none()).map(|r| (r.next_fight(), r.class));
        let mut g = Game {
            demo,
            ui: Ui::new(),
            screen: Screen::Menu,
            overlays: vec![],
            run: None,
            settings,
            fade: 1.0,
            next: None,
            quit: false,
            want_fullscreen: None,
            cam_note: None,
            army_sel: 0,
            army_top: 0,
            inspect: None,
            field_mouse: None,
            battle_bodies: vec![],
            summary: None,
            help_tab: 0,
            sheet_top: 0,
            saved,
            money_seen: None,
            floats: vec![],
            pending_run: None,
            fork_due: false,
            targeting: None,
        };
        g.apply_volume();
        g
    }

    pub fn apply_volume(&mut self) {
        #[cfg(feature = "audio")]
        if let Some(a) = &mut self.demo.audio {
            a.set_volume(self.settings.volume as f32 / 10.0);
        }
    }

    /// The class whose look the screen takes (the menu's is the Foundry's).
    pub fn class(&self) -> Class {
        match &self.screen {
            Screen::Leaders { class, .. } => *class,
            _ => self.run.as_ref().map(|r| r.class).unwrap_or(Class::Foundry),
        }
    }

    pub fn in_battle(&self) -> bool {
        matches!(self.screen, Screen::Battle { .. })
    }

    /// Off to another screen, through black.
    pub fn go(&mut self, s: Screen) {
        self.next = Some(s);
    }

    /// The light of the picture (1 — full).
    pub fn light(&self) -> f32 {
        1.0 - self.fade * 0.85
    }

    /// The dip: darker toward the next screen, the switch at the bottom, lighter again.
    pub fn step_fade(&mut self, dt: f32) {
        if self.next.is_some() {
            self.fade = (self.fade + dt / 0.16).min(1.0);
            if self.fade >= 1.0 {
                if let Some(s) = self.next.take() {
                    self.enter(s);
                }
            }
        } else {
            self.fade = (self.fade - dt / 0.22).max(0.0);
        }
    }

    /// The place-picking given up: back to the find it came from (the trader's goods stay as they were).
    pub fn cancel_target(&mut self) {
        if let Some(tg) = self.targeting.take() {
            if let (From::Reward(i), Screen::Rewards { pick, .. }) = (tg.from, &mut self.screen) {
                *pick = Some(i);
                self.ui.opened = self.ui.t;
            }
        }
    }

    fn enter(&mut self, s: Screen) {
        self.ui.blocked = false;
        self.targeting = None;
        self.ui.entered = self.ui.t;
        if let Screen::Battle { node } = &s {
            self.start_battle(node.clone());
        }
        if matches!(s, Screen::Menu | Screen::Class | Screen::Leaders { .. }) {
            self.money_seen = None;
        }
        if matches!(s, Screen::Fork) {
            if let Some((c, l, seed)) = self.pending_run.take() {
                self.run = Some(Run::new(c, l, seed));
            }
            if std::mem::take(&mut self.fork_due) {
                if let Some(run) = &mut self.run {
                    run.fork();
                }
            }
            self.save();
        }
        self.screen = s;
    }

    pub fn save(&mut self) {
        if let Some(r) = &self.run {
            let _ = std::fs::create_dir_all(data_dir());
            let _ = std::fs::write(save_path(), serde_json::to_string(r).unwrap_or_default());
            self.saved = Some((r.next_fight(), r.class));
        }
    }

    fn forget_save(&mut self) {
        let _ = std::fs::remove_file(save_path());
        self.saved = None;
    }

    // ---------------------------------------------------------------- the run's steps

    pub fn new_run(&mut self, class: Class, leader: usize) {
        let seed = std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).map(|d| d.as_nanos() as u64).unwrap_or(7);
        self.pending_run = Some((class, leader, seed));
        self.go(Screen::Fork);
    }

    pub fn continue_run(&mut self) {
        if let Some(r) = load_run() {
            self.run = Some(r);
            self.go(Screen::Fork);
        }
    }

    /// A road taken at the fork.
    pub fn take_road(&mut self, i: usize) {
        let Some(run) = &mut self.run else { return };
        let Some(node) = run.path.get(i).cloned() else { return };
        let s = match node.kind {
            run::Kind::Merchant => Screen::Shop(run.shop()),
            run::Kind::Event => Screen::Event { id: node.event, done: None },
            run::Kind::Camp => Screen::Camp { stage: CampStage::Choose, said: String::new() },
            _ => Screen::Battle { node },
        };
        self.go(s);
    }

    fn start_battle(&mut self, node: Node) {
        let Some(run) = &mut self.run else { return };
        let (me, _) = run.fighters();
        let seed = run.battle_seed();
        let rec = playback::record_of(seed, &me, &node.enemy);
        self.battle_bodies = me.iter().chain(node.enemy.iter()).cloned().collect();
        self.demo.load(rec);
        self.demo.view.speed = self.settings.speed.max(1);
        let won = self.demo.rec.outcome.winner == Some(0);
        let key = if won { "battle.loot" } else { "battle.end" };
        self.demo.view.end = Some((crate::text::t(key), "Enter".to_string()));
    }

    /// The battle watched to its end: the losses stay, the spoils — or the end of the run.
    pub fn battle_done(&mut self) {
        let Screen::Battle { node } = &self.screen else { return };
        let node = node.clone();
        let Some(run) = &mut self.run else { return };
        let res = run::BattleResult {
            won: self.demo.rec.outcome.winner == Some(0),
            dead: self.demo.rec.dead0.clone(),
            kills: self.demo.rec.kills1,
        };
        // the battle's summary, read before its losses are taken from the army: who fell (the leader always comes
        // back), who killed most
        let (fighters, idx) = run.fighters();
        let mut lost: Vec<(sim::model::Template, usize, bool)> = vec![];
        for &d in &res.dead {
            let Some(&m) = idx.get(d) else { continue };
            if run.is_leader(&run.army[m]) {
                continue;
            }
            let t = run.army[m].t.clone();
            let broken = run.class == run::Class::Foundry;
            match lost.iter_mut().find(|(x, _, _)| x.name == t.name) {
                Some(l) => l.1 += 1,
                None => lost.push((t, 1, broken)),
            }
        }
        let rec = &self.demo.rec;
        let best = (0..fighters.len().min(rec.kills.len())).filter(|&i| rec.kills[i] > 0).max_by_key(|&i| (rec.kills[i], std::cmp::Reverse(i))).map(|i| (fighters[i].clone(), rec.kills[i]));
        self.summary = Some(Summary { rounds: rec.outcome.rounds, kills: res.kills, lost, best });
        let rewards = run.after_battle(&node, &res);
        if run.over == Some(false) {
            self.forget_save();
            self.go(Screen::End { victory: false });
        } else {
            self.go(Screen::Rewards { list: rewards.into_iter().map(|r| (r, false)).collect(), pick: None });
        }
    }

    /// From the spoils on: the next fork, or the run's end after the last boss.
    pub fn leave_rewards(&mut self) {
        let Some(run) = &mut self.run else { return };
        if run.over == Some(true) {
            self.forget_save();
            self.go(Screen::End { victory: true });
        } else {
            self.fork_due = true;
            self.go(Screen::Fork);
        }
    }

    /// A stop (the trader, an event, the camp) left: the next fork is battles only.
    pub fn leave_stop(&mut self) {
        if let Some(run) = &mut self.run {
            run.stopped = true;
        }
        self.fork_due = true;
        self.go(Screen::Fork);
    }

    pub fn surrender(&mut self) {
        if let Some(run) = &mut self.run {
            run.over = Some(false);
        }
        self.overlays.clear();
        self.forget_save();
        self.go(Screen::End { victory: false });
    }

    /// To the menu. The run stays as it was saved when its last fork came up: saving in the middle of a step (after
    /// an event's choice, at the trader's) would bring that same fork back, its event or trader to take again; a
    /// step left halfway is replayed from the fork — the same, the run is deterministic.
    pub fn back_to_menu(&mut self) {
        self.overlays.clear();
        self.targeting = None;
        self.pending_run = None;
        self.fork_due = false;
        self.run = None;
        self.go(Screen::Menu);
    }

    // ---------------------------------------------------------------- the frame

    /// The battle's ticks (24 a second; only while a battle is on and not paused under an overlay).
    pub fn tick(&mut self) {
        if self.in_battle() && self.overlays.is_empty() && self.next.is_none() {
            self.demo.tick();
        } else {
            #[cfg(feature = "audio")]
            if let Some(a) = &mut self.demo.audio {
                a.bed(false);
            }
        }
    }

    /// A key, as the window hands it over.
    pub fn key(&mut self, k: Key) {
        if k == Key::Esc {
            self.escape();
            return;
        }
        // F1: the help, from anywhere (again — closed)
        if k == Key::Help {
            if self.overlays.last() == Some(&Overlay::Help) {
                self.overlays.pop();
            } else {
                self.overlays.push(Overlay::Help);
                self.ui.opened = self.ui.t;
            }
            return;
        }
        self.ui.keys.push(k);
    }

    /// Esc: closes the uppermost overlay; on a screen of the run (and in battle) opens the pause; in the menu does
    /// nothing; on the class or leader screens goes back.
    fn escape(&mut self) {
        if let Some(Overlay::Hint(h)) = self.overlays.last().copied() {
            self.hint_seen(h);
            return;
        }
        if self.overlays.pop().is_some() {
            self.demo.ui_sound("toggle");
            return;
        }
        if self.targeting.is_some() {
            self.cancel_target();
            self.demo.ui_sound("toggle");
            return;
        }
        if let Screen::Rewards { pick: pick @ Some(_), .. } = &mut self.screen {
            *pick = None;
            self.demo.ui_sound("toggle");
            return;
        }
        // the workshop: the module held put back, else back to the camp's choice
        if let Screen::Camp { stage: stage @ CampStage::Workshop { .. }, said } = &mut self.screen {
            *stage = match *stage {
                CampStage::Workshop { held: Some(_) } => CampStage::Workshop { held: None },
                _ if said.is_empty() => CampStage::Choose,
                _ => CampStage::Done,
            };
            self.demo.ui_sound("toggle");
            return;
        }
        match self.screen {
            Screen::Menu => {}
            Screen::Class => self.go(Screen::Menu),
            Screen::Leaders { .. } => self.go(Screen::Class),
            Screen::End { .. } => self.back_to_menu(),
            _ => {
                self.overlays.push(Overlay::Pause);
                self.demo.ui_sound("toggle");
            }
        }
    }

    /// A first-time hint read: gone, and not shown again.
    pub fn hint_seen(&mut self, h: u8) {
        debug_assert!(h < HINTS);
        if self.overlays.last() == Some(&Overlay::Hint(h)) {
            self.overlays.pop();
        }
        self.settings.hints_seen |= 1 << h;
        self.settings.save();
    }

    /// The first-time hint the screen has, if it has one (and the battle's only while it plays).
    pub fn hint_here(&self) -> Option<u8> {
        match self.screen {
            Screen::Leaders { .. } => Some(0),
            Screen::Fork => Some(1),
            Screen::Battle { .. } => Some(2),
            Screen::Rewards { pick: None, .. } => Some(3),
            Screen::Shop(_) => Some(4),
            Screen::Camp { .. } => Some(5),
            _ => None,
        }
    }

    /// A roster opened to look at: its title, its rows, the one picked first.
    pub fn open_inspect(&mut self, title: String, items: Vec<crate::screens::SheetItem>, sel: usize) {
        self.army_sel = sel.min(items.len().saturating_sub(1));
        self.army_top = self.army_sel.saturating_sub(crate::screens::ARMY_ROWS / 2);
        self.sheet_top = 0;
        self.inspect = Some((title, items));
        self.overlays.push(Overlay::Inspect);
        self.ui.opened = self.ui.t;
    }

    /// The fighter under the mouse on the battlefield, if there is one standing there.
    fn fighter_at(&self) -> Option<usize> {
        let (fx, fy) = self.field_mouse?;
        let rec = &self.demo.rec;
        let shown = rec.shown(self.demo.view.frame.min((rec.frames() - 1) as f32));
        shown
            .iter()
            .filter(|s| s.pose != playback::Pose::Dead && s.id < rec.units.len())
            .filter(|s| {
                let u = &rec.units[s.id];
                let (hw, top) = if u.fp >= 2 || u.leader { (40.0, 90.0) } else { (16.0, 40.0) };
                fx >= s.x - hw && fx <= s.x + hw && fy >= s.y - top && fy <= s.y + 6.0
            })
            .min_by(|a, b| {
                let d = |s: &&playback::Shown| (s.x - fx).powi(2) + (s.y - 20.0 - fy).powi(2);
                d(a).total_cmp(&d(b))
            })
            .map(|s| s.id)
    }

    /// Every fighter of the battle as a roster (ours first, the enemy's after; the fallen last of each), each with
    /// how it stands now; and the row of `pick`.
    fn battle_items(&self, pick: usize) -> (Vec<crate::screens::SheetItem>, usize) {
        use crate::text::{t, tf};
        let rec = &self.demo.rec;
        let f = (self.demo.view.frame as i32).clamp(0, rec.frames() - 1);
        let round = &rec.rounds[(f / playback::FR) as usize];
        let mut rows: Vec<(usize, crate::screens::SheetItem, bool)> = vec![];
        for (id, u) in rec.units.iter().enumerate() {
            let body = self.battle_bodies.get(id).cloned().unwrap_or_else(|| {
                // one hatched in the battle: a larva
                let mut l = sim::data::rabochaya();
                l.name = u.name.clone().into();
                l
            });
            let st = round.before.get(id).copied().unwrap_or_default();
            let present = st.present;
            if !present && st.alive {
                continue; // not on the field (yet, or any more)
            }
            let mut it = crate::screens::SheetItem::of(&body, 1, u.side == 1);
            let fallen = !st.alive;
            it.state = Some(if fallen {
                (t("sheet.fallen"), crate::ui::RED)
            } else {
                (tf("sheet.now", &[("hp", &st.hp.max(0)), ("max", &body.hp)]), if st.hp * 3 < body.hp { crate::ui::RED } else { crate::ui::INK })
            });
            rows.push((id, it, fallen));
        }
        rows.sort_by_key(|(id, it, fallen)| (it.foe, *fallen, *id));
        let sel = rows.iter().position(|(id, _, _)| *id == pick).unwrap_or(0);
        (rows.into_iter().map(|(_, it, _)| it).collect(), sel)
    }

    /// The battle's own controls (its speed buttons, the end plate's button, its keys).
    pub fn battle_input(&mut self) {
        if !self.overlays.is_empty() || self.next.is_some() {
            self.demo.view.hover = None;
            return;
        }
        let (mx, my) = (self.ui.mx, self.ui.my);
        let b = render::button_at(&self.demo.rec, &self.demo.view, mx, my);
        self.demo.view.hover = b;
        let ended = self.demo.view.frame as i32 >= self.demo.rec.frames() + 12;
        let clicked = if self.ui.released { b } else { None };
        let key = |g: &mut Game, k: Key| g.ui.keys.contains(&k);
        if clicked == Some(render::Button::Pause) || key(self, Key::Space) {
            self.demo.view.paused = !self.demo.view.paused;
            self.demo.ui_sound("toggle");
        }
        if clicked == Some(render::Button::Speed) || key(self, Key::Tab) {
            self.demo.view.speed = match self.demo.view.speed {
                1 => 2,
                2 => 4,
                _ => 1,
            };
            self.demo.view.paused = false;
            self.demo.ui_sound("toggle");
        }
        if clicked == Some(render::Button::ToEnd) || key(self, Key::End) {
            self.demo.view.frame = (self.demo.rec.frames() - 1) as f32;
            self.demo.ui_sound("click");
        }
        // the camera: C on and off, the wheel and + / − nearer and farther (down to the whole field)
        let now = self.settings.cam_level();
        let mut want = now;
        if key(self, Key::C) {
            want = if now > 0 { 0 } else { self.settings.zoom.clamp(1, 4) };
        }
        let steps = self.ui.wheel + key(self, Key::ZoomIn) as i32 - key(self, Key::ZoomOut) as i32;
        if steps != 0 {
            want = (now as i32 + steps).clamp(0, 4) as u8;
        }
        if want != now || steps != 0 {
            self.settings.set_cam_level(want);
            self.settings.save();
            self.cam_note = Some(self.ui.t);
            if want != now {
                self.demo.ui_sound("toggle");
            }
        }
        // a click on a fighter (not on a button): its sheet, and every fighter of the battle beside it
        let on_field = b.is_none() && my > 34;
        let left = self.ui.released && on_field;
        let right = self.ui.rreleased_at() && on_field;
        if left || right {
            if let Some(id) = self.fighter_at() {
                let (items, sel) = self.battle_items(id);
                self.demo.ui_sound("toggle");
                self.open_inspect(crate::text::t("inspect.battle"), items, sel);
                return;
            }
        }
        if ended && (clicked == Some(render::Button::NewBattle) || key(self, Key::Enter) || key(self, Key::R)) {
            self.demo.ui_sound("click");
            self.battle_done();
        }
        self.ui.keys.clear();
    }

    /// The interface sounds the frame asked for.
    pub fn play_sounds(&mut self) {
        for s in std::mem::take(&mut self.ui.sounds) {
            self.demo.ui_sound(s);
        }
    }
}
