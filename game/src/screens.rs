//! How each screen looks and what its controls do (the states are game.rs). The layouts follow the mockups
//! (docs/ART.md: the menu, the class, the leader, the camp, the trader…); the screens between battles take their
//! shape from the genre's way — the spoils a column of rows to take one by one, a find a choice of three cards with a
//! way to pass, the trader a counter of goods with their prices under them, an event a picture and a choice — but
//! are built of the game's own forge iron and brass (the Foundry) or chitin and acid (the swarm).
//!
//! A screen draws itself and answers its controls in one go (ui.rs); what a control does to the run is an `Act`,
//! applied when the frame is drawn.

use crate::assets::{Align, Assets};
use crate::game::{CampStage, From, Game, Overlay, Screen, Targeting};
use crate::gfx::Image;
use crate::text::{t, tf};
use crate::ui::{self, cell, heading, para, plate, text, Key, Rect, Ui, ACID, ACID2, BLUE, BRASS, EDGE, GOLD, INK, MUTED, PALE, RED, TITLE_F, TITLE_S, VIOLET};
use sim::model::{Ability, Dmg, Template};
use sim::run::{form_of, Artifact, Class, Effect, Find, Kind, Offer, Reward, Run, Target, EVENTS, FIGHTS};

pub enum Act {
    NewRun,
    Continue,
    Settings,
    About,
    Quit,
    ToClass,
    ToLeaders(Class),
    ToMenu,
    StartRun(Class, usize),
    Road(usize),
    Take(usize),
    OpenFind(usize),
    /// The camp's workshop opened (the Foundry).
    Workshop,
    /// A body of the army picked to see its sheet (its row); the army's list scrolled (rows).
    ArmySel(usize),
    ArmyScroll(i32),
    /// The picked body's sheet scrolled (lines).
    SheetScroll(i32),
    /// The swarm's evolutions opened; a form evolved: (form, evolution).
    Evolution,
    Evolve(String, String),
    /// A cell of a golem clicked in the workshop: (member, cell).
    Socket(usize, usize),
    Pick(usize, Option<usize>),
    LeaveRewards,
    BuyOffer(usize),
    BuyArtifact(usize),
    BuyService,
    LeaveStop,
    EventChoose(usize),
    CampRest,
    CampUp,
    CampPick(usize),
    CampBack,
    Place(Target),
    CancelTarget,
    CloseFind,
    Resume,
    Army,
    Surrender,
    CloseOverlay,
    Volume(i32),
    Fullscreen,
    Camera,
    UiScale,
    Speed,
}

fn cols(c: Class) -> ([u8; 3], [u8; 3]) {
    match c {
        Class::Foundry => TITLE_F,
        Class::Swarm => TITLE_S,
    }
}

fn ci(c: Class) -> usize {
    match c {
        Class::Foundry => 0,
        Class::Swarm => 1,
    }
}

fn currency_icon(c: Class) -> &'static str {
    match c {
        Class::Foundry => "glyph/металл",
        Class::Swarm => "glyph/биомасса",
    }
}

/// An artifact's icon (the kit's atlas, 16 px a cell) at k×.
fn artifact_icon(ui: &mut Ui, cv: &mut Image, a: &Assets, art: Artifact, x: i32, y: i32, k: i32) {
    let idx = Artifact::ALL.iter().position(|&x| x == art).unwrap_or(0) as i32;
    let Some(p) = a.ui.get("foundry/artifacts") else { return };
    if k == 1 {
        cv.blit_region(&p.img, idx * 16, 0, 16, 16, x, y, false, 1.0);
    } else {
        let key = format!("art:{idx}:{k}");
        let _ = key;
        let img = p.img.crop(idx * 16, 0, 16, 16).scaled(k);
        cv.blit(&img, x, y, false, 1.0);
    }
    let _ = ui;
}

fn artifact_tip(art: Artifact) -> Vec<(String, [u8; 3])> {
    vec![(t(&format!("art.{}", art.key())), GOLD), (t(&format!("art.{}.l", art.key())), INK)]
}

/// What an ability is called (a module's name, a trait's).
pub fn ability_name(ab: &Ability) -> String {
    let k = match ab {
        Ability::Volley { .. } => "ab.volley",
        Ability::Repair { .. } => "ab.repair",
        Ability::Bolt { dmg: Dmg::Shock, .. } => "ab.bolt_shock",
        Ability::Bolt { .. } => "ab.bolt_blunt",
        Ability::Flail => "ab.flail",
        Ability::Plates(_) => "ab.plates",
        Ability::PointBlank => "ab.pointblank",
        Ability::Intercept => "ab.intercept",
        Ability::Flash { .. } => "ab.flash",
        Ability::Spit { .. } => "ab.spit",
        Ability::Brood { .. } => "ab.brood",
        Ability::Mark { .. } => "ab.mark",
        Ability::Overload { .. } => "ab.overload",
        Ability::Fireball { .. } => "ab.fireball",
        Ability::Quake { .. } => "ab.quake",
        Ability::Augment => "ab.augment",
        Ability::Tinker { .. } => "ab.tinker",
    };
    t(k)
}

/// The portrait of a body for a card: the larger one baked for cards, else its battle sprite twice as large.
#[allow(clippy::too_many_arguments)]
fn portrait(ui: &mut Ui, cv: &mut Image, a: &Assets, t: &Template, gx: i32, gy: i32, alpha: f32, flip: bool) {
    let base = t.name.as_ref();
    let key = format!("portrait/{base}");
    if a.sprites.contains_key(&key) {
        ui.sprite_k(cv, a, &key, gx, gy, 1, flip, alpha);
        return;
    }
    let tries = [format!("{base}_{}_idle", t.size), format!("{base}_0_idle"), format!("{base}_idle"), "Пожиратель_0_idle".to_string()];
    for k in tries {
        if a.sprites.contains_key(&k) {
            let big = a.sprites[&k].img.h > 60;
            ui.sprite_k(cv, a, &k, gx, gy, if big { 1 } else { 2 }, flip, alpha);
            return;
        }
    }
}

/// A small battle sprite of a body (for a strip of the army, an enemy line-up).
fn small(cv: &mut Image, a: &Assets, t: &Template, gx: i32, gy: i32, flip: bool, dark: bool) {
    let n = t.name.as_ref();
    let tries = [format!("{n}_{}_idle", t.size), format!("{n}_1_idle"), format!("{n}_idle"), "Пожиратель_0_idle".to_string()];
    for k in tries {
        if let Some(s) = a.sprites.get(&k) {
            let ox = if flip { s.img.w - 1 - s.ox } else { s.ox };
            if dark {
                cv.blit_shade(&s.img, gx - ox, gy - s.oy, flip, 0.45, 0.8);
            } else {
                cv.blit(&s.img, gx - ox, gy - s.oy, flip, 1.0);
            }
            return;
        }
    }
}

/// Bodies grouped by name: (template, how many).
fn groups(ts: &[Template]) -> Vec<(Template, usize)> {
    let mut out: Vec<(Template, usize)> = vec![];
    for t in ts {
        if let Some(g) = out.iter_mut().find(|(x, _)| x.name == t.name && x.size == t.size) {
            g.1 += 1;
        } else {
            out.push((t.clone(), 1));
        }
    }
    out
}

fn hit_text(u: &Template) -> String {
    if u.die == 0 || u.has(sim::model::Trait::NoAttack) {
        return t("card.nohit");
    }
    let t = u;
    let b = if t.bonus > 0 {
        format!(" +{}", t.bonus)
    } else if t.bonus < 0 {
        format!(" −{}", -t.bonus)
    } else {
        String::new()
    };
    tf("card.hit", &[("d", &format!("1–{}", t.die)), ("b", &b)])
}

/// A body's card: its portrait on a dark pedestal, its name, how many, its numbers and what it carries.
#[allow(clippy::too_many_arguments)]
fn unit_card(ui: &mut Ui, cv: &mut Image, a: &Assets, cls: Class, id: &str, r: Rect, t: &Template, n: usize, state: &str, on: bool) -> (bool, bool) {
    let (over, k, hit) = ui.card(cv, a, cls, id, r, state, on);
    let lift = (k * 4.0).round() as i32;
    let r = r.shift(0, -lift);
    let pedestal = r.y + r.h / 2 + 4;
    cv.shadow(r.cx() as f32, pedestal as f32, (r.w as f32 * 0.55).min(110.0), 10.0);
    if k > 0.01 {
        let g = if cls == Class::Foundry { [255, 140, 60] } else { [140, 220, 70] };
        cv.glow(r.cx() as f32, (pedestal - 24) as f32, 50.0, g, 0.12 * k);
    }
    // the portrait cut to the card's inside (a tall one does not stand over its rim)
    let inner = r.inset(6);
    let mut pic = Image::clear(inner.w, pedestal - inner.y + 6);
    portrait(ui, &mut pic, a, t, r.cx() - inner.x, pedestal - inner.y, 1.0, false);
    cv.blit(&pic, inner.x, inner.y, false, if on { 1.0 } else { 0.5 });
    let name = t.name.as_ref();
    let font = &a.fonts["text16"];
    let title_col = if cls == Class::Foundry { [255, 214, 150] } else { ACID2 };
    let mut y = pedestal + 30;
    match name.split_once(" (") {
        // a name too wide for the card (a narrow one: the camp, the army): the form, and its caste under it
        Some((form, caste)) if font.width(name) > r.w - 10 => {
            font.draw(cv, form, r.cx(), pedestal + 8, if on { title_col } else { MUTED }, Some(EDGE), Align::Center, 1.0);
            font.draw(cv, caste.trim_end_matches(')'), r.cx(), pedestal + 26, if on { MUTED } else { PALE }, Some(EDGE), Align::Center, 1.0);
            y += 16;
        }
        _ => font.draw(cv, name, r.cx(), pedestal + 8, if on { title_col } else { MUTED }, Some(EDGE), Align::Center, 1.0),
    }
    if n > 1 {
        a.fonts["title16"].draw(cv, &tf("card.count", &[("n", &n)]), r.x + r.w - 14, r.y + 12, GOLD, Some(EDGE), Align::Right, 1.0);
    }
    let lines = [
        tf("card.hp", &[("n", &t.hp)]),
        hit_text(t),
        if t.armor != 0 { tf("card.armor", &[("n", &t.armor)]) } else { tf("card.size", &[("n", &t.size)]) },
    ];
    for l in lines {
        if y + 16 > r.y + r.h - 6 {
            break;
        }
        font.draw(cv, &l, r.cx(), y, if on { INK } else { PALE }, Some(EDGE), Align::Center, 1.0);
        y += 18;
    }
    let abil: Vec<String> = t.abilities.iter().map(ability_name).collect();
    if !abil.is_empty() && y + 16 <= r.y + r.h - 6 {
        let s = abil.join(" · ");
        let w = r.w - 16;
        for l in font.wrap(&s, w).into_iter().take(2) {
            if y + 16 > r.y + r.h - 6 {
                break;
            }
            font.draw(cv, &l, r.cx(), y, if on { BLUE } else { PALE }, Some(EDGE), Align::Center, 1.0);
            y += 18;
        }
    }
    (over, hit)
}

/// The finds' words and icons: a module's in the Foundry's atlas, a mutation's in the swarm's.
fn part_icon(o: &Offer) -> Option<(String, String)> {
    match &o.find {
        Find::Module(k) => Some((format!("module/{k}"), k.clone())),
        Find::Mutation(k) => Some((format!("swarm/{k}"), k.clone())),
        Find::Units => None,
    }
}

/// Who a module is for, in words: its frames' names, or any golem.
fn module_for(key: &str) -> String {
    let Some(f) = sim::data::finds().modules.iter().find(|f| f.key == key) else { return String::new() };
    if f.frames.is_empty() {
        return t("find.any");
    }
    let names: Vec<String> = f.frames.iter().map(|k| sim::data::unit(k).name.to_string()).collect();
    tf("find.for", &[("who", &names.join(", "))])
}

/// A find's card: bodies as a body's card, a module or a mutation as its icon large on a glowing disc, its name,
/// what kind of find it is, what it does — dimmed if the army has nowhere to put it.
#[allow(clippy::too_many_arguments)]
fn offer_card(ui: &mut Ui, cv: &mut Image, a: &Assets, run: &Run, id: &str, r: Rect, o: &Offer, state: &str, on: bool) -> (bool, bool) {
    let cls = run.class;
    let Some((icon, key)) = part_icon(o) else {
        return unit_card(ui, cv, a, cls, id, r, &o.units[0], o.units.len(), state, on);
    };
    let room = !run.targets(o).is_empty();
    let on = on && room;
    let (over, k, hit) = ui.card(cv, a, cls, id, r, "rare", on);
    let r = r.shift(0, -(k * 4.0).round() as i32);
    let disc = (r.cx(), r.y + r.h / 3 + 4);
    let g = if cls == Class::Foundry { [255, 150, 60] } else { [150, 230, 70] };
    cv.glow(disc.0 as f32, disc.1 as f32, 56.0, g, 0.18 + 0.15 * k + 0.04 * (ui.t * 2.5).sin());
    let sock = if cls == Class::Foundry { "foundry/artifact_socket_normal" } else { "swarm/artifact_cell_normal" };
    if let Some(p) = a.ui.get(sock) {
        let big = p.img.scaled(3);
        cv.blit(&big, disc.0 - big.w / 2, disc.1 - big.h / 2, false, if on { 1.0 } else { 0.5 });
    }
    ui.icon(cv, a, &icon, disc.0 - 32, disc.1 - 32, 4, if on { 1.0 } else { 0.45 });
    let font = &a.fonts["text16"];
    let mut y = r.y + r.h / 2 + 38;
    let name = t(&format!("find.{key}"));
    let title_col = if cls == Class::Foundry { [255, 214, 150] } else { ACID2 };
    for l in font.wrap(&name, r.w - 16) {
        font.draw(cv, &l, r.cx(), y, if on { title_col } else { MUTED }, Some(EDGE), Align::Center, 1.0);
        y += 18;
    }
    let kind = match &o.find {
        Find::Module(k) => format!("{} · {}", t("find.module"), module_for(k)),
        Find::Mutation(k) if sim::data::finds().mutations.iter().any(|m| &m.key == k && m.leader.is_some()) => t("find.pool"),
        _ => t("find.mutation"),
    };
    for l in font.wrap(&kind, r.w - 16).into_iter().take(2) {
        font.draw(cv, &l, r.cx(), y, if on { MUTED } else { PALE }, Some(EDGE), Align::Center, 1.0);
        y += 18;
    }
    y += 4;
    let line = if room { t(&format!("find.{key}.l")) } else { t("target.none") };
    for l in font.wrap(&line, r.w - 16).into_iter().take(3) {
        if y + 16 > r.y + r.h - 4 {
            break;
        }
        font.draw(cv, &l, r.cx(), y, if room { BLUE } else { RED }, Some(EDGE), Align::Center, 1.0);
        y += 18;
    }
    (over, hit)
}

/// A way for the leader to grow: the leader, what it becomes, the words of it. True when clicked.
fn growth_card(ui: &mut Ui, cv: &mut Image, a: &Assets, run: &Run, id: &str, r: Rect, key: &str) -> bool {
    let cls = run.class;
    let (_, k, hit) = ui.card(cv, a, cls, id, r, "rare", true);
    let r = r.shift(0, -(k * 4.0).round() as i32);
    let pedestal = r.y + 128;
    let g = if cls == Class::Foundry { [255, 170, 70] } else { [150, 230, 70] };
    cv.glow(r.cx() as f32, (pedestal - 40) as f32, 70.0, g, 0.16 + 0.14 * k + 0.04 * (ui.t * 2.5).sin());
    cv.shadow(r.cx() as f32, pedestal as f32, 90.0, 10.0);
    if let Some(m) = run.army.iter().find(|m| run.is_leader(m)) {
        let inner = r.inset(6);
        let mut pic = Image::clear(inner.w, pedestal - inner.y + 6);
        portrait(ui, &mut pic, a, &m.t, r.cx() - inner.x, pedestal - inner.y, 1.0, false);
        cv.blit(&pic, inner.x, inner.y, false, 1.0);
    }
    let font = &a.fonts["text16"];
    let title_col = if cls == Class::Foundry { [255, 214, 150] } else { ACID2 };
    let mut y = pedestal + 14;
    for l in font.wrap(&t(&format!("growth.{key}")), r.w - 20) {
        font.draw(cv, &l, r.cx(), y, title_col, Some(EDGE), Align::Center, 1.0);
        y += 18;
    }
    y += 6;
    for l in font.wrap(&t(&format!("growth.{key}.l")), r.w - 24).into_iter().take(5) {
        if y + 16 > r.y + r.h - 6 {
            break;
        }
        font.draw(cv, &l, r.cx(), y, INK, Some(EDGE), Align::Center, 1.0);
        y += 18;
    }
    hit
}

/// What a body carries, as a row of small icons along its card's foot: a golem's modules (and its free cells as
/// empty sockets), a breed's mutations.
fn marks(ui: &mut Ui, cv: &mut Image, a: &Assets, run: &Run, r: Rect, m: &sim::run::Member) {
    let mut icons: Vec<String> = vec![];
    let mut empty = 0;
    match run.class {
        Class::Foundry => {
            if m.t.golem || !m.mods.is_empty() {
                icons.extend(m.mods.iter().map(|k| format!("module/{k}")));
                empty = run.cells(m).saturating_sub(m.mods.len());
            }
        }
        Class::Swarm => {
            let f = form_of(&m.t);
            icons.extend(run.breeds.iter().filter(|(x, _)| x == f).map(|(_, k)| format!("swarm/{k}")));
        }
    }
    let n = (icons.len() + empty) as i32;
    if n == 0 {
        return;
    }
    // along the card's top-left (its count stands at the top-right)
    let x0 = r.x + 8;
    let y = r.y + 7;
    let rim = if run.class == Class::Foundry { [150, 118, 64, 255] } else { [110, 90, 130, 255] };
    for (i, key) in icons.iter().enumerate() {
        let x = x0 + i as i32 * 19;
        cv.fill(x - 1, y - 1, 18, 18, rim);
        cv.fill(x, y, 16, 16, [12, 9, 14, 255]);
        ui.icon(cv, a, key, x, y, 1, 1.0);
        // a module above level I: a gold dot for each level under it
        if run.class == Class::Foundry && m.level(i) > 1 {
            for p in 0..m.level(i) as i32 {
                cv.fill(x + 2 + p * 5, y + 18, 3, 3, [255, 200, 90, 255]);
            }
        }
    }
    // a free cell: an empty socket with its rim
    for j in 0..empty as i32 {
        let x = x0 + (icons.len() as i32 + j) * 19;
        cv.fill(x - 1, y - 1, 18, 18, [70, 60, 52, 255]);
        cv.fill(x, y, 16, 16, [12, 9, 14, 255]);
        cv.fill(x + 6, y + 6, 4, 4, [44, 38, 46, 255]);
    }
}

/// Where a module or a mutation goes: the golems it fits (with their cells) or the breeds (a body of each, how
/// many), over the dimmed screen; Esc or «Назад» gives it up.
fn target_overlay(ui: &mut Ui, cv: &mut Image, a: &Assets, run: &Run, tg: &Targeting) -> Option<Act> {
    let cls = run.class;
    cv.fill(0, 44, 960, 424, [6, 4, 8, 236]);
    let (icon, key) = part_icon(&tg.offer)?;
    let (title, sub) = match tg.offer.find {
        Find::Module(_) => ("target.module", "target.sub.module"),
        _ => ("target.mutation", "target.sub.mutation"),
    };
    heading(cv, a, &t(title), 480, 56, 24, cols(cls), Align::Center);
    let name = t(&format!("find.{key}"));
    let line = tf(sub, &[("name", &name)]);
    let w = a.fonts["text16"].width(&line);
    ui.icon(cv, a, &icon, 480 - w / 2 - 40, 84, 2, 1.0);
    text(cv, a, &line, 480, 92, INK, Align::Center);
    let mut act = None;
    let targets = run.targets(&tg.offer);
    let (cw, ch, gap) = (140, 196, 12);
    let per = 6;
    let n = targets.len().min(12) as i32;
    let x0 = (960 - n.min(per) * cw - (n.min(per) - 1) * gap) / 2;
    for (j, to) in targets.iter().enumerate().take(12) {
        let (col, row) = (j as i32 % per, j as i32 / per);
        let r = Rect::new(x0 + col * (cw + gap), 118 + row * (ch + gap) + ui.rise_from(ui.opened, j), cw, ch);
        let (m, count) = match to {
            Target::Member(i) => (&run.army[*i], 1),
            Target::Form(f) => {
                let ms: Vec<&sim::run::Member> = run.army.iter().filter(|m| form_of(&m.t) == f && !run.is_leader(m)).collect();
                let pick = ms.iter().find(|m| m.t.name.contains("рабоч")).or(ms.first()).copied();
                match pick {
                    Some(m) => (m, ms.len()),
                    None => continue,
                }
            }
        };
        let body = run.body(m);
        let (_, hit) = unit_card(ui, cv, a, cls, &format!("tgt{j}"), r, &body, count, if m.broken { "broken" } else { "normal" }, true);
        marks(ui, cv, a, run, r, m);
        // the module on it already: taken again, it goes a level up
        if let (Target::Member(i), Find::Module(k)) = (to, &tg.offer.find) {
            if run.raises(*i, k) {
                let lv = m.mods.iter().position(|x| x == k).map(|p| m.level(p) + 1).unwrap_or(2);
                text(cv, a, &tf("target.raise", &[("n", &t(&format!("lvl.{lv}")))]), r.cx(), r.y + r.h + 6, GOLD, Align::Center);
            }
        }
        if hit || ui.key(Key::Digit(j as u8 + 1)) {
            act = Some(Act::Place(to.clone()));
        }
    }
    if ui.minor(cv, a, cls, "tgtback", 410, 420, &t("back"), true) {
        act = Some(Act::CancelTarget);
    }
    act
}

/// A price under a good: the brass tag (the Foundry) or an amber chip (the swarm), the currency's glyph, the
/// number — red when it can't be paid.
#[allow(clippy::too_many_arguments)]
fn price_tag(ui: &mut Ui, cv: &mut Image, a: &Assets, cls: Class, cx: i32, y: i32, price: i32, can: bool) {
    let font = &a.fonts["title16"];
    let w = font.width(&price.to_string()) + 46;
    let r = Rect::new(cx - w / 2, y, w, 26);
    match cls {
        Class::Foundry => ui.piece(cv, a, "foundry/tag_brass", r, 1.0),
        Class::Swarm => ui.piece(cv, a, "swarm/button_amber_22", Rect::new(r.x - 10, r.y + 2, r.w + 20, 22), 1.0),
    }
    ui.icon(cv, a, currency_icon(cls), r.x + 20, r.y + 4, 2, 1.0);
    font.draw(cv, &price.to_string(), r.x + 44, r.y + 5, if can { [40, 26, 10] } else { [170, 30, 20] }, None, Align::Left, 1.0);
}

/// The «sold» stamp across a good.
fn sold_stamp(ui: &mut Ui, cv: &mut Image, a: &Assets, r: Rect) {
    cv.fill(r.x + 4, r.y + 4, r.w - 8, r.h - 8, [10, 8, 12, 150]);
    let w = a.fonts["title16"].width(&t("shop.sold")) + 24;
    let sr = Rect::new(r.cx() - w / 2, r.cy() - 12, w, 24);
    ui.piece(cv, a, "foundry/stamp", sr, 1.0);
    a.fonts["title16"].draw(cv, &t("shop.sold"), r.cx(), sr.y + 4, [224, 80, 58], None, Align::Center, 1.0);
}

// ---------------------------------------------------------------- the chrome of the run's screens

/// The top: the class's wing with the screen's name; the currency, the battle we are at, the artifacts.
fn top(ui: &mut Ui, cv: &mut Image, a: &Assets, run: &Run, title: &str, sub: &str) {
    let cls = run.class;
    match cls {
        Class::Foundry => ui.piece(cv, a, "foundry/wing", Rect::new(0, 0, 960, 44), 1.0),
        Class::Swarm => ui.put(cv, a, "swarm/wing_960", 0, 0, 1.0),
    }
    let w = a.fonts["title24"].width(title);
    heading(cv, a, title, 16, 8, 24, cols(cls), Align::Left);
    if !sub.is_empty() {
        let sc = if cls == Class::Foundry { [255, 170, 80] } else { ACID };
        text(cv, a, sub, 16 + w + 18, 14, sc, Align::Left);
    }
    // the artifacts from the right edge, then the battle number, then the currency
    let n = run.artifacts.len() as i32;
    let mut x = 948 - n * 32;
    for (i, art) in run.artifacts.iter().enumerate() {
        let sx = x + i as i32 * 32;
        let sock = if cls == Class::Foundry { "foundry/artifact_socket_normal" } else { "swarm/artifact_cell_normal" };
        ui.put(cv, a, sock, sx, 8, 1.0);
        artifact_icon(ui, cv, a, *art, sx + if cls == Class::Foundry { 6 } else { 8 }, 14, 1);
        let r = Rect::new(sx, 8, 28, 28);
        if ui.hot(&format!("art{i}"), r).0 {
            ui.tooltip(artifact_tip(*art));
        }
    }
    x -= 16;
    let fight = tf("bar.fight", &[("n", &run.next_fight().min(FIGHTS)), ("all", &FIGHTS)]);
    text(cv, a, &fight, x, 14, MUTED, Align::Right);
    x -= a.fonts["text16"].width(&fight) + 22;
    let m = run.money.to_string();
    a.fonts["title16"].draw(cv, &m, x, 13, GOLD, Some(EDGE), Align::Right, 1.0);
    ui.money_at = (x - a.fonts["title16"].width(&m) / 2, 30);
    x -= a.fonts["title16"].width(&m) + 26;
    ui.icon(cv, a, currency_icon(cls), x, 12, 2, 1.0);
    let r = Rect::new(x, 8, 26 + a.fonts["title16"].width(&m), 28);
    if ui.hot("money", r).0 {
        ui.tooltip(vec![(t(&format!("cur.{}", ci(cls))), GOLD)]);
    }
}

/// The bottom: the forge's sill / the hive's foot.
fn bottom(ui: &mut Ui, cv: &mut Image, a: &Assets, cls: Class) {
    match cls {
        Class::Foundry => ui.piece(cv, a, "foundry/sill", Rect::new(0, 468, 960, 72), 1.0),
        Class::Swarm => ui.put(cv, a, "swarm/foot_960", 0, 468, 1.0),
    }
}

/// The run's fifteen battles as a line of studs: the won ones lit, the next one glowing, the bosses crowned.
fn progress(ui: &mut Ui, cv: &mut Image, a: &Assets, run: &Run, y: i32) {
    let (x0, x1) = (250, 710);
    let lit = if run.class == Class::Foundry { [240, 180, 90, 255] } else { [160, 236, 70, 255] };
    cv.fill(x0, y, x1 - x0, 2, [40, 34, 42, 255]);
    for i in 0..FIGHTS {
        let x = x0 + (i as i32) * (x1 - x0) / (FIGHTS as i32 - 1);
        let n = i + 1;
        let done = n <= run.fight;
        let next = n == run.next_fight();
        let boss = n % sim::run::BOSS_EVERY == 0;
        let r = if boss { 6 } else { 4 };
        cv.fill(x - r - 1, y - r, 2 * r + 3, 2 * r + 2, [14, 10, 16, 255]);
        let c = if done { lit } else if next { [255, 240, 200, 255] } else { [70, 62, 76, 255] };
        cv.fill(x - r, y - r + 1, 2 * r + 1, 2 * r, c);
        if next {
            let k = 0.5 + 0.5 * (ui.t * 4.0).sin();
            cv.glow(x as f32, y as f32, 14.0, [lit[0], lit[1], lit[2]], 0.35 * k + 0.1);
        }
        if boss {
            let crown = if run.class == Class::Foundry { "foundry/crown" } else { "swarm/crown" };
            ui.put(cv, a, crown, x - 13, y - 30, if done || next { 1.0 } else { 0.55 });
        }
    }
}

/// The army in a row of small bodies (the broken dark), on the sill.
fn army_strip(cv: &mut Image, a: &Assets, run: &Run, x: i32, y: i32, w: i32) {
    // drawn on its own strip, so a big body (the Queen) does not stand over the sill's rim
    let top = y - 50;
    let mut strip = Image::clear(w, 70);
    army_strip_on(&mut strip, a, run, 0, y - top, w);
    cv.blit(&strip, x, top, false, 1.0);
}

fn army_strip_on(cv: &mut Image, a: &Assets, run: &Run, x: i32, y: i32, w: i32) {
    let mut gs: Vec<(Template, usize, bool)> = vec![];
    for m in &run.army {
        if let Some(g) = gs.iter_mut().find(|(t, _, b)| t.name == m.t.name && t.size == m.t.size && *b == m.broken) {
            g.1 += 1;
        } else {
            gs.push((m.t.clone(), 1, m.broken));
        }
    }
    let mut cx = x;
    for (t, n, broken) in gs {
        let wide = if t.size >= 5 { 54 } else if t.size >= 3 { 40 } else { 30 };
        if cx + wide > x + w {
            break;
        }
        small(cv, a, &t, cx + wide / 2, y, false, broken);
        if n > 1 {
            a.fonts["text16"].draw(cv, &format!("×{n}"), cx + wide / 2, y + 2, GOLD, Some(EDGE), Align::Center, 1.0);
        }
        cx += wide + 6;
    }
}

/// A little scene drawn at 1× on its own picture and shown k times larger (a vignette: the bodies as the
/// battle's camera would show them up close), cut to its frame.
fn vignette(cv: &mut Image, r: Rect, k: i32, draw: impl FnOnce(&mut Image)) {
    let mut sc = Image::new(r.w / k, r.h / k);
    draw(&mut sc);
    let big = if k == 1 { sc } else { sc.scaled(k) };
    cv.blit(&big, r.x, r.y, false, 1.0);
}

impl Game {
    /// The picture under the interface (the window's field layer): the screen's background.
    pub fn draw_bg(&mut self, cv: &mut Image) {
        let a = &self.demo.assets;
        let f8 = ((self.ui.t * 7.0) as usize) % 8;
        let name = match &self.screen {
            Screen::Menu => format!("menu_{f8}"),
            Screen::Class => format!("class_{f8}"),
            Screen::Leaders { class: Class::Foundry, .. } => "leaders_f".into(),
            Screen::Leaders { class: Class::Swarm, .. } => "leaders_s".into(),
            _ => match self.class() {
                Class::Foundry => "forge".into(),
                Class::Swarm => "hive".into(),
            },
        };
        if let Some(img) = a.bg.get(&name) {
            cv.blit(img, 0, 0, false, 1.0);
        }
    }

    /// The interface (the window's upper layer): the screen, the overlays over it, a tooltip over all.
    pub fn draw_ui(&mut self, cv: &mut Image) {
        let busy = self.next.is_some();
        // under the place-picker and the overlays the screen does not answer
        self.ui.blocked = !self.overlays.is_empty() || busy || self.targeting.is_some();
        let mut act = None;
        {
            let a = &self.demo.assets;
            let ui = &mut self.ui;
            let run = self.run.as_ref();
            act = match &mut self.screen {
                Screen::Menu => menu(ui, cv, a, self.saved),
                Screen::Class => class_pick(ui, cv, a),
                Screen::Leaders { class, chosen } => leaders(ui, cv, a, *class, chosen),
                Screen::Fork => run.and_then(|r| fork(ui, cv, a, r)),
                Screen::Battle { .. } => None,
                Screen::Rewards { list, pick } => run.and_then(|r| rewards(ui, cv, a, r, list, *pick)),
                Screen::Shop(shop) => run.and_then(|r| shop_screen(ui, cv, a, r, shop)),
                Screen::Event { id, done } => run.and_then(|r| event(ui, cv, a, r, *id, done)),
                Screen::Camp { stage, said } => run.and_then(|r| camp(ui, cv, a, r, *stage, said)),
                Screen::End { victory } => run.and_then(|r| end(ui, cv, a, r, *victory)),
            }
            .or(act);
        }
        if self.in_battle() {
            self.battle_input();
            // the camera's level, for a moment after it changed: its name and five marks
            if let Some(t0) = self.cam_note {
                let age = self.ui.t - t0;
                if age > 1.4 || !self.overlays.is_empty() {
                    self.cam_note = None;
                } else {
                    let a = &self.demo.assets;
                    let alpha = (1.4 - age).clamp(0.0, 0.35) / 0.35;
                    let l = self.settings.cam_level();
                    let s = tf("cam.note", &[("v", &t(&format!("cam.{l}")))]);
                    let w = a.fonts["text16"].width(&s);
                    let (x0, y0) = (480 - (w + 80) / 2, 46);
                    cv.fill(x0, y0, w + 80, 26, [10, 8, 12, (170.0 * alpha) as u8]);
                    a.fonts["text16"].draw(cv, &s, x0 + 10, y0 + 5, INK, Some(EDGE), Align::Left, alpha);
                    for i in 0..5 {
                        let c: [u8; 4] = if i <= l as i32 { [255, 200, 90, (255.0 * alpha) as u8] } else { [70, 60, 50, (255.0 * alpha) as u8] };
                        cv.fill(x0 + w + 20 + i * 10, y0 + 9, 7, 9, c);
                    }
                }
            }
        }
        if let (Some(tg), Some(run)) = (self.targeting.clone(), self.run.as_ref()) {
            self.ui.blocked = !self.overlays.is_empty() || busy;
            if let Some(x) = target_overlay(&mut self.ui, cv, &self.demo.assets, run, &tg) {
                act = Some(x);
            }
        }
        // the overlays: only the uppermost answers
        let n = self.overlays.len();
        let battle = self.in_battle();
        let army_at = (self.army_sel, self.army_top, self.sheet_top);
        for (i, ov) in self.overlays.clone().into_iter().enumerate() {
            self.ui.blocked = i + 1 < n || busy;
            cv.fill(0, 0, 960, 540, [6, 4, 8, 150]);
            let cls = self.class();
            let a = &self.demo.assets;
            let ui = &mut self.ui;
            let r = match ov {
                Overlay::Pause => pause(ui, cv, a, cls, self.run.as_ref(), battle),
                Overlay::Settings => settings(ui, cv, a, cls, &self.settings),
                Overlay::Army => self.run.as_ref().and_then(|r| army(ui, cv, a, r, army_at.0, army_at.1, army_at.2)),
                Overlay::About => about(ui, cv, a, cls),
                Overlay::Evolution => self.run.as_ref().and_then(|r| evolution(ui, cv, a, r)),
            };
            if r.is_some() {
                act = r;
            }
        }
        self.ui.blocked = busy;
        let cls = self.class();
        // the currency's changes float up from its number
        if let Some(run) = &self.run {
            if !self.in_battle() && matches!(self.screen, Screen::Fork | Screen::Rewards { .. } | Screen::Shop(_) | Screen::Event { .. } | Screen::Camp { .. }) {
                if let Some(seen) = self.money_seen {
                    if seen != run.money {
                        self.floats.push((self.ui.t, run.money - seen));
                    }
                }
                self.money_seen = Some(run.money);
            }
        }
        let now = self.ui.t;
        self.floats.retain(|(t0, _)| now - t0 < 1.2);
        for (t0, d) in &self.floats {
            let age = now - t0;
            let (x, y) = self.ui.money_at;
            let s = if *d > 0 { format!("+{d}") } else { format!("-{}", -d) };
            let col = if *d > 0 { GOLD } else { RED };
            let alpha = (1.2 - age).clamp(0.0, 1.0);
            self.demo.assets.fonts["title16"].draw(cv, &s, x, y + 8 + (age * 22.0) as i32, col, Some(EDGE), Align::Center, alpha);
        }
        self.ui.draw_tip(cv, &self.demo.assets, cls);
        ui::shutters(cv, self.fade, cls);
        if let Some(x) = act {
            self.apply(x);
        }
        self.play_sounds();
    }

    pub fn apply(&mut self, act: Act) {
        match act {
            Act::NewRun | Act::ToClass => self.go(Screen::Class),
            Act::Continue => self.continue_run(),
            Act::Settings => {
                self.overlays.push(Overlay::Settings);
                self.ui.opened = self.ui.t;
            }
            Act::About => {
                self.overlays.push(Overlay::About);
                self.ui.opened = self.ui.t;
            }
            Act::Army => {
                self.overlays.push(Overlay::Army);
                self.ui.opened = self.ui.t;
                self.army_sel = 0;
                self.army_top = 0;
                self.sheet_top = 0;
            }
            Act::ArmySel(k) => {
                self.army_sel = k;
                self.sheet_top = 0;
                self.demo.ui_sound("toggle");
            }
            Act::ArmyScroll(d) => {
                let rows = self.run.as_ref().map(|r| army_rows(r).len()).unwrap_or(0);
                self.army_top = (self.army_top as i32 + d).clamp(0, rows.saturating_sub(ARMY_ROWS) as i32) as usize;
            }
            Act::SheetScroll(d) => {
                let n = self.run.as_ref().and_then(|r| army_rows(r).get(self.army_sel).map(|&(i, _)| sheet_lines(r, &r.army[i]).len())).unwrap_or(0);
                self.sheet_top = (self.sheet_top as i32 + d).clamp(0, n.saturating_sub(1) as i32) as usize;
            }
            Act::Evolution => {
                self.overlays.push(Overlay::Evolution);
                self.ui.opened = self.ui.t;
            }
            Act::Evolve(form, key) => {
                if let Some(run) = &mut self.run {
                    if run.evolve(&form, &key) {
                        self.demo.ui_sound("heal");
                    }
                }
            }
            Act::Quit => self.quit = true,
            Act::ToLeaders(c) => self.go(Screen::Leaders { class: c, chosen: 0 }),
            Act::ToMenu => self.back_to_menu(),
            Act::StartRun(c, l) => self.new_run(c, l),
            Act::Road(i) => self.take_road(i),
            Act::Take(i) => {
                if let (Some(run), Screen::Rewards { list, .. }) = (&mut self.run, &mut self.screen) {
                    if let Some((r, taken)) = list.get_mut(i) {
                        if !*taken && run.can_take(r) {
                            run.take(r);
                            *taken = true;
                            self.demo.ui_sound("toggle");
                        }
                    }
                }
            }
            Act::OpenFind(i) => {
                if let Screen::Rewards { pick, .. } = &mut self.screen {
                    *pick = Some(i);
                    self.ui.opened = self.ui.t;
                }
            }
            Act::Pick(i, card) => {
                if let (Some(run), Screen::Rewards { list, pick }) = (&mut self.run, &mut self.screen) {
                    // the leader's growth: one of two, for good (no passing it by)
                    if let Some((Reward::Growth(keys), taken)) = list.get_mut(i) {
                        if let Some(k) = card.and_then(|c| keys.get(c)) {
                            run.grow(k);
                            *taken = true;
                            *pick = None;
                        }
                        return;
                    }
                    if let Some((Reward::Find(offers), taken)) = list.get_mut(i) {
                        match card.and_then(|c| offers.get(c)) {
                            // a module or a mutation: where it goes is asked next
                            Some(o) if o.find != Find::Units => {
                                if !run.targets(o).is_empty() {
                                    self.targeting = Some(Targeting { offer: o.clone(), from: From::Reward(i) });
                                    self.ui.opened = self.ui.t;
                                    *pick = None;
                                }
                                return;
                            }
                            Some(o) => run.recruit(o),
                            None => {
                                run.pass_find();
                            }
                        }
                        *taken = true;
                    }
                    *pick = None;
                }
            }
            Act::LeaveRewards => self.leave_rewards(),
            Act::BuyOffer(i) => {
                if let (Some(run), Screen::Shop(shop)) = (&mut self.run, &mut self.screen) {
                    let Some((o, sold)) = shop.offers.get(i).cloned() else { return };
                    if o.find != Find::Units {
                        if !sold && run.money >= o.price && !run.targets(&o).is_empty() {
                            self.targeting = Some(Targeting { offer: o, from: From::Shop(i) });
                            self.ui.opened = self.ui.t;
                        }
                    } else if run.buy_offer(shop, i, None) {
                        self.demo.ui_sound("toggle");
                    }
                }
            }
            Act::Place(to) => {
                let Some(tg) = self.targeting.take() else { return };
                if let Some(run) = &mut self.run {
                    match (tg.from, &mut self.screen) {
                        (From::Reward(i), Screen::Rewards { list, .. }) => {
                            if run.take_find(&tg.offer, Some(&to)) {
                                if let Some((_, taken)) = list.get_mut(i) {
                                    *taken = true;
                                }
                            }
                        }
                        (From::Shop(i), Screen::Shop(shop)) => {
                            run.buy_offer(shop, i, Some(&to));
                        }
                        _ => {}
                    }
                }
                self.demo.ui_sound("toggle");
            }
            Act::CancelTarget => self.cancel_target(),
            Act::BuyArtifact(i) => {
                if let (Some(run), Screen::Shop(shop)) = (&mut self.run, &mut self.screen) {
                    if run.buy_artifact(shop, i) {
                        self.demo.ui_sound("toggle");
                    }
                }
            }
            Act::BuyService => {
                if let (Some(run), Screen::Shop(shop)) = (&mut self.run, &mut self.screen) {
                    if run.buy_service(shop) {
                        self.demo.ui_sound("toggle");
                    }
                }
            }
            Act::LeaveStop => self.leave_stop(),
            Act::EventChoose(o) => {
                if let (Some(run), Screen::Event { id, done }) = (&mut self.run, &mut self.screen) {
                    if done.is_none() && run.event_can(*id, o) {
                        let got = run.event_choose(*id, o);
                        *done = Some(match got {
                            Some(art) => tf("event.got", &[("name", &t(&format!("art.{}", art.key())))]),
                            None => t("event.done"),
                        });
                    }
                }
            }
            Act::CampRest => {
                if let (Some(run), Screen::Camp { stage, said }) = (&mut self.run, &mut self.screen) {
                    let n = run.camp_rest();
                    *said = tf(&format!("camp.done.{}", ci(run.class)), &[("n", &n)]);
                    *stage = CampStage::Done;
                }
            }
            Act::CampUp => {
                if let Screen::Camp { stage, .. } = &mut self.screen {
                    *stage = CampStage::Pick;
                }
            }
            Act::CampBack => {
                // back to the camp's choice — or, the choice made already (its words said), to the camp's end
                if let Screen::Camp { stage, said } = &mut self.screen {
                    *stage = if said.is_empty() { CampStage::Choose } else { CampStage::Done };
                }
            }
            Act::Workshop => {
                if let Screen::Camp { stage, .. } = &mut self.screen {
                    *stage = CampStage::Workshop { held: None };
                    self.ui.opened = self.ui.t;
                }
            }
            Act::Socket(m, j) => {
                if let (Some(run), Screen::Camp { stage: CampStage::Workshop { held }, .. }) = (&mut self.run, &mut self.screen) {
                    let Some(member) = run.army.get(m) else { return };
                    let filled = j < member.mods.len();
                    match *held {
                        None if filled => *held = Some((m, j)),
                        None => return,
                        Some(h) if h == (m, j) => *held = None,
                        // an empty cell: the module moves there, free
                        Some((hm, hj)) if !filled => {
                            if !run.move_module(hm, hj, m) {
                                return;
                            }
                            *held = None;
                        }
                        // another module of the frame: the one held melted into it
                        Some((hm, hj)) if run.can_melt(hm, hj, m, j) => {
                            run.melt(hm, hj, m, j);
                            *held = None;
                            self.demo.ui_sound("heal");
                            return;
                        }
                        Some(_) => *held = Some((m, j)),
                    }
                    self.demo.ui_sound("toggle");
                }
            }
            Act::CloseFind => {
                if let Screen::Rewards { pick, .. } = &mut self.screen {
                    *pick = None;
                }
            }
            Act::CampPick(m) => {
                if let (Some(run), Screen::Camp { stage, said }) = (&mut self.run, &mut self.screen) {
                    let name = run.army[m].t.name.to_string();
                    run.camp_upgrade(m);
                    *said = tf("camp.done.up", &[("name", &name)]);
                    *stage = CampStage::Done;
                }
            }
            Act::Resume | Act::CloseOverlay => {
                self.overlays.pop();
            }
            Act::Surrender => self.surrender(),
            Act::Volume(d) => {
                self.settings.volume = (self.settings.volume as i32 + d).clamp(0, 10) as u8;
                self.settings.save();
                self.apply_volume();
            }
            Act::Fullscreen => {
                self.settings.fullscreen = !self.settings.fullscreen;
                self.want_fullscreen = Some(self.settings.fullscreen);
                self.settings.save();
            }
            Act::Camera => {
                // through the levels: the whole field, then nearer and nearer, round to the whole field again
                let next = (self.settings.cam_level() + 1) % 5;
                self.settings.set_cam_level(next);
                self.settings.save();
            }
            Act::UiScale => {
                self.settings.ui_scale = (self.settings.ui_scale + 1) % 4;
                self.settings.save();
            }
            Act::Speed => {
                self.settings.speed = match self.settings.speed {
                    1 => 2,
                    2 => 4,
                    _ => 1,
                };
                self.settings.save();
            }
        }
    }
}

// ---------------------------------------------------------------- the menu, the class, the leader

/// Which build this is: the commit it was built from (CI sets GAM2_BUILD), «dev» for a local one.
pub fn build() -> String {
    option_env!("GAM2_BUILD").map(|s| s.chars().take(7).collect()).filter(|s: &String| !s.is_empty()).unwrap_or_else(|| "dev".to_string())
}

fn menu(ui: &mut Ui, cv: &mut Image, a: &Assets, saved: Option<(u32, Class)>) -> Option<Act> {
    ui::motes(cv, ui.t, Rect::new(250, 120, 300, 300), 26, Class::Foundry, 1.0);
    ui::motes(cv, ui.t, Rect::new(680, 160, 240, 260), 14, Class::Swarm, 0.8);
    a.fonts["text16"].draw(cv, &t("menu.title"), 480, 48, [176, 150, 112], Some(EDGE), Align::Center, 1.0);
    let mut act = None;
    if ui.lever(cv, a, "new", 24, 452, (272, 64), &t("menu.new"), true) || ui.key(Key::Enter) {
        act = Some(Act::NewRun);
    }
    if let Some((n, _)) = saved {
        if ui.tag(cv, a, "cont", 360, 452, &tf("menu.continue", &[("n", &n)]), "brass", true) {
            act = Some(Act::Continue);
        }
    } else {
        ui.tag(cv, a, "cont", 360, 452, &tf("menu.continue", &[("n", &"–")]), "dull", false);
    }
    if ui.tag(cv, a, "set", 650, 452, &t("menu.settings"), "steel", true) {
        act = Some(Act::Settings);
    }
    if ui.tag(cv, a, "about", 360, 492, &t("menu.about"), "steel", true) {
        act = Some(Act::About);
    }
    if ui.tag(cv, a, "quit", 650, 492, &t("menu.quit"), "rust", true) {
        act = Some(Act::Quit);
    }
    // which build: up in the corner, clear of the buttons
    text(cv, a, &tf("menu.version", &[("v", &build())]), 948, 8, PALE, Align::Right);
    act
}

fn class_pick(ui: &mut Ui, cv: &mut Image, a: &Assets) -> Option<Act> {
    heading(cv, a, &t("class.title"), 480, 8, 24, TITLE_F, Align::Center);
    let left = Rect::new(0, 44, 480, 396);
    let right = Rect::new(480, 44, 480, 396);
    let (lo, lk) = ui.hot("half_f", left);
    let (ro, rk) = ui.hot("half_s", right);
    // the half under the mouse bright, the other sinking back
    if rk > 0.01 {
        cv.fill(0, 44, 480, 396, [0, 0, 0, (115.0 * rk) as u8]);
    }
    if lk > 0.01 {
        cv.fill(480, 44, 480, 396, [0, 0, 0, (115.0 * lk) as u8]);
    }
    ui::motes(cv, ui.t, Rect::new(140, 100, 200, 220), 18, Class::Foundry, 0.4 + 0.6 * lk);
    ui::motes(cv, ui.t, Rect::new(560, 120, 360, 200), 14, Class::Swarm, 0.4 + 0.6 * rk);
    cell(ui, cv, a, Class::Foundry, Rect::new(30, 312, 418, 98), if lo { "hi" } else { "normal" });
    heading(cv, a, &t("class.foundry"), 44, 320, 16, ([255, 210, 140], [130, 90, 40]), Align::Left);
    text(cv, a, &t("class.foundry.l1"), 44, 344, INK, Align::Left);
    text(cv, a, &t("class.foundry.l2"), 44, 364, MUTED, Align::Left);
    text(cv, a, &t("class.leaders"), 44, 384, MUTED, Align::Left);
    cell(ui, cv, a, Class::Swarm, Rect::new(512, 312, 418, 98), if ro { "hi" } else { "normal" });
    heading(cv, a, &t("class.swarm"), 526, 320, 16, (ACID, [70, 150, 50]), Align::Left);
    text(cv, a, &t("class.swarm.l1"), 526, 344, INK, Align::Left);
    text(cv, a, &t("class.swarm.l2"), 526, 364, MUTED, Align::Left);
    text(cv, a, &t("class.leaders"), 526, 384, MUTED, Align::Left);
    let mut act = None;
    if ui.lever(cv, a, "cf", 24, 462, (244, 52), &t("class.foundry"), true) || ui.clicked(left) {
        act = Some(Act::ToLeaders(Class::Foundry));
    }
    if ui.chitin(cv, a, "cs", Rect::new(660, 458, 276, 56), &t("class.swarm"), "acid", true, true) || ui.clicked(right) {
        act = Some(Act::ToLeaders(Class::Swarm));
    }
    if ui.tag(cv, a, "back", 336, 470, &t("back"), "steel", true) {
        act = Some(Act::ToMenu);
    }
    act
}

fn leaders(ui: &mut Ui, cv: &mut Image, a: &Assets, cls: Class, chosen: &mut usize) -> Option<Act> {
    let f6 = ((ui.t * 8.0) as usize) % 6;
    let c = ci(cls);
    let mut act = None;
    for i in 0..4 {
        let rect = match cls {
            Class::Foundry => Rect::new(14 + i as i32 * 236, 54, 227, 402),
            Class::Swarm => Rect::new(480 + ((i as f32 - 1.5) * 232.0) as i32 - 110, 50, 220, 410),
        };
        let (over, k) = ui.hot(&format!("lead{i}"), rect);
        if i == *chosen {
            let key = match cls {
                Class::Foundry => format!("pick_f{i}_{f6}"),
                Class::Swarm => format!("pick_s{i}"),
            };
            if let Some(p) = a.ui.get(&key) {
                let at = p.meta["at"].as_array().map(|v| (v[0].as_i64().unwrap_or(0) as i32, v[1].as_i64().unwrap_or(0) as i32)).unwrap_or((0, 0));
                cv.blit(&p.img, at.0, at.1, false, 1.0);
            }
            if cls == Class::Foundry {
                ui::sparks(cv, ui.t, rect.cx() - 50, 290, 8, 1.0, i as u32 * 7);
                ui::sparks(cv, ui.t, rect.cx() + 54, 286, 6, 1.0, i as u32 * 7 + 3);
            }
        } else if k > 0.01 {
            let g = if cls == Class::Foundry { [255, 150, 70] } else { [150, 230, 70] };
            cv.glow(rect.cx() as f32, rect.cy() as f32 - 30.0, 120.0, g, 0.08 * k);
        }
        let sel = i == *chosen;
        let name = t(&format!("leader.{c}.{i}.name"));
        let epi = t(&format!("leader.{c}.{i}.epi"));
        let rule = t(&format!("leader.{c}.{i}.rule"));
        match cls {
            Class::Foundry => {
                let cx = rect.cx();
                a.fonts["title16"].draw(cv, &name.to_uppercase(), cx, 68, if sel { [255, 210, 140] } else { INK }, Some(EDGE), Align::Center, 1.0);
                text(cv, a, &epi, cx, 86, if sel { BRASS } else { MUTED }, Align::Center);
                let mut y = 404;
                for l in a.fonts["text16"].wrap(&rule, 200) {
                    text(cv, a, &l, cx, y, if sel { GOLD } else { MUTED }, Align::Center);
                    y += 18;
                }
            }
            Class::Swarm => {
                let cx = 480 + ((i as f32 - 1.5) * 232.0) as i32;
                let ecol = [[230, 190, 80], [190, 150, 240], [230, 70, 50], [120, 210, 90]][i];
                heading(cv, a, &name.to_uppercase(), cx, 100, 16, if sel { (ACID2, [90, 150, 40]) } else { (INK, [120, 110, 130]) }, Align::Center);
                text(cv, a, &epi, cx, 122, ecol, Align::Center);
                let mut y = 352;
                for l in a.fonts["text16"].wrap(&rule, 176) {
                    text(cv, a, &l, cx, y, if sel { ACID2 } else { MUTED }, Align::Center);
                    y += 18;
                }
            }
        }
        if over && ui.clicked(rect) {
            *chosen = i;
            ui.sound("toggle");
        }
    }
    for d in 0..4u8 {
        if ui.key(Key::Digit(d + 1)) {
            *chosen = d as usize;
        }
    }
    match cls {
        Class::Foundry => {
            heading(cv, a, &t("leaders.title"), 480, 8, 24, TITLE_F, Align::Center);
            text(cv, a, &t("leaders.sub.foundry"), 16, 13, [255, 170, 80], Align::Left);
            if ui.tag(cv, a, "back", 12, 482, &t("back"), "steel", true) {
                act = Some(Act::ToClass);
            }
            if ui.lever(cv, a, "go", 652, 478, (244, 52), &t("leaders.go"), true) || ui.key(Key::Enter) {
                act = Some(Act::StartRun(cls, *chosen));
            }
        }
        Class::Swarm => {
            let w = a.fonts["title24"].width(&t("leaders.title"));
            heading(cv, a, &t("leaders.title"), 16, 6, 24, TITLE_S, Align::Left);
            heading(cv, a, &t("leaders.sub.swarm"), 16 + w + 40, 8, 24, (ACID, [70, 130, 40]), Align::Left);
            if ui.chitin(cv, a, "back", Rect::new(12, 474, 288, 50), &t("back"), "chitin", true, true) {
                act = Some(Act::ToClass);
            }
            if ui.chitin(cv, a, "go", Rect::new(660, 470, 288, 58), &t("leaders.go"), "acid", true, true) || ui.key(Key::Enter) {
                act = Some(Act::StartRun(cls, *chosen));
            }
        }
    }
    act
}

// ---------------------------------------------------------------- the fork

fn road_state(k: Kind) -> &'static str {
    match k {
        Kind::Fight => "normal",
        Kind::Elite => "rare",
        Kind::Boss => "broken",
        Kind::Merchant => "trophy",
        Kind::Event => "new",
        Kind::Camp => "hi",
    }
}

fn fork(ui: &mut Ui, cv: &mut Image, a: &Assets, run: &Run) -> Option<Act> {
    let cls = run.class;
    let c = ci(cls);
    ui::motes(cv, ui.t, Rect::new(0, 60, 960, 400), 30, cls, 0.7);
    let sub = if run.boss_next() { t("fork.sub.boss") } else { t("fork.sub") };
    top(ui, cv, a, run, &t(&format!("fork.title.{c}")), &sub);
    progress(ui, cv, a, run, 76);
    bottom(ui, cv, a, cls);
    let mut act = None;
    let n = run.path.len() as i32;
    let (cw, gap) = (262, 26);
    let x0 = (960 - n * cw - (n - 1) * gap) / 2;
    for (i, node) in run.path.iter().enumerate() {
        let r = Rect::new(x0 + i as i32 * (cw + gap), 104 + ui.rise(i), cw, 352);
        let (_, k, hit) = ui.card(cv, a, cls, &format!("road{i}"), r, road_state(node.kind), true);
        let r = r.shift(0, -(k * 4.0).round() as i32);
        let label = match node.kind {
            Kind::Fight => t("node.fight"),
            Kind::Elite => t("node.elite"),
            Kind::Boss => t("node.boss"),
            Kind::Merchant => t("node.merchant"),
            Kind::Event => t("node.event"),
            Kind::Camp => t(&format!("node.camp.{c}")),
        };
        let hc = match node.kind {
            Kind::Elite => (GOLD, [140, 96, 40]),
            Kind::Boss => ([255, 150, 120], [140, 40, 30]),
            Kind::Event => (BLUE, [60, 100, 140]),
            _ => cols(cls),
        };
        heading(cv, a, &label, r.cx(), r.y + 14, 16, hc, Align::Center);
        if node.kind.is_battle() {
            // how dangerous: a skull a step, its words under the mouse
            for d in 0..node.danger as i32 {
                ui.icon(cv, a, "glyph/гибель", r.x + r.w - 30 - d * 22, r.y + 12, 2, 1.0);
            }
            let sk = Rect::new(r.x + r.w - 30 - (node.danger as i32 - 1) * 22, r.y + 8, node.danger as i32 * 22, 24);
            if ui.hot(&format!("danger{i}"), sk).0 {
                ui.tooltip(vec![(t(&format!("danger.{}", node.danger.clamp(1, 3))), if node.danger >= 2 { RED } else { INK })]);
            }
        }
        a.fonts["text16"].draw(cv, &format!("{}", i + 1), r.x + 14, r.y + 12, PALE, Some(EDGE), Align::Left, 1.0);
        let scene = Rect::new(r.x + 14, r.y + 42, r.w - 28, 168);
        cv.fill(scene.x, scene.y, scene.w, scene.h, [8, 6, 10, 170]);
        cv.fill(scene.x, scene.y, scene.w, 1, [0, 0, 0, 255]);
        match node.kind {
            k if k.is_battle() => {
                // the enemy's army as it would stand, facing us, on a patch of the battlefield; small bodies shown
                // twice as close
                let gs = groups(&node.enemy);
                let mut sorted = gs.clone();
                sorted.sort_by_key(|(t, _)| std::cmp::Reverse(t.size));
                let zoom = if sorted.iter().all(|(t, _)| t.size <= 2) { 2 } else { 1 };
                vignette(cv, scene, zoom, |sc| {
                    let (w, h) = (sc.w, sc.h);
                    sc.blit_region(&a.ground, 300, 120, w, h, 0, 0, false, 1.0);
                    sc.dim(0, 0, w, h, 0.7);
                    let n = sorted.len().min(8) as i32;
                    let cols_n = if n <= 3 { n.max(1) } else { 4.min((n + 1) / 2) };
                    let rows_n = (n + cols_n - 1) / cols_n.max(1);
                    for (j, (t, cnt)) in sorted.iter().enumerate().take(8) {
                        let (col, row) = (j as i32 % cols_n, j as i32 / cols_n);
                        let gx = (col * 2 + 1) * w / (cols_n * 2) + if row % 2 == 1 { w / (cols_n * 4) } else { 0 };
                        let gy = (row + 1) * h / (rows_n + 1) + h / (rows_n + 1) / 3;
                        // a flock: a few bodies of it, not one
                        let show = (*cnt).min(3) as i32;
                        for b in (0..show).rev() {
                            let (dx, dy) = [(0, 0), (-7, -4), (7, -5)][b as usize];
                            sc.shadow((gx + dx) as f32, (gy + dy) as f32, 14.0, 3.0);
                            small(sc, a, t, gx + dx, gy + dy, true, false);
                        }
                    }
                });
                for (j, (_, cnt)) in sorted.iter().enumerate().take(8) {
                    let n = sorted.len().min(8) as i32;
                    let cols_n = if n <= 3 { n.max(1) } else { 4.min((n + 1) / 2) };
                    let rows_n = (n + cols_n - 1) / cols_n.max(1);
                    let (col, row) = (j as i32 % cols_n, j as i32 / cols_n);
                    let (w, h) = (scene.w / zoom, scene.h / zoom);
                    let gx = (col * 2 + 1) * w / (cols_n * 2) + if row % 2 == 1 { w / (cols_n * 4) } else { 0 };
                    let gy = (row + 1) * h / (rows_n + 1) + h / (rows_n + 1) / 3;
                    if *cnt > 1 {
                        a.fonts["text16"].draw(cv, &format!("×{cnt}"), scene.x + gx * zoom + 14, scene.y + gy * zoom - 6, GOLD, Some(EDGE), Align::Left, 1.0);
                    }
                }
                cv.glow(scene.cx() as f32, (scene.y + scene.h) as f32, 120.0, [200, 60, 30], 0.12);
                let total = node.enemy.len();
                text(cv, a, &tf("node.enemy", &[("n", &total)]), r.cx(), r.y + 220, INK, Align::Center);
                let summary: Vec<String> = gs
                    .iter()
                    .take(4)
                    .map(|(t, n)| {
                        let nm = t.name.split(' ').next().unwrap_or("");
                        if *n > 1 { format!("{nm} ×{n}") } else { nm.to_string() }
                    })
                    .collect();
                let mut y = r.y + 242;
                for l in a.fonts["text16"].wrap(&summary.join(" · "), r.w - 24).into_iter().take(2) {
                    text(cv, a, &l, r.cx(), y, MUTED, Align::Center);
                    y += 18;
                }
                // the reward
                let ry = r.y + r.h - 64;
                cv.fill(r.x + 20, ry - 6, r.w - 40, 1, [80, 70, 60, 255]);
                ui.icon(cv, a, currency_icon(cls), r.x + 30, ry + 2, 2, 1.0);
                a.fonts["title16"].draw(cv, &format!("+{}", node.reward), r.x + 58, ry + 2, GOLD, Some(EDGE), Align::Left, 1.0);
                let find = if node.danger >= 2 { t("node.find.rare") } else { t("node.find") };
                text(cv, a, &find, r.x + r.w - 20, ry + 2, if node.danger >= 2 { GOLD } else { INK }, Align::Right);
                if node.kind != Kind::Fight {
                    let p = a.ui.get("foundry/artifacts").map(|p| p.img.crop(0, 0, 16, 16).scaled(2));
                    if let Some(img) = p {
                        cv.blit(&img, r.x + 30, ry + 24, false, 1.0);
                    }
                    text(cv, a, &t("node.artifact"), r.x + 66, ry + 30, GOLD, Align::Left);
                }
            }
            Kind::Merchant => {
                let lantern = if cls == Class::Foundry { "lantern_on" } else { "swarm/lantern_on" };
                ui.put(cv, a, lantern, scene.x + 10, scene.y + 6, 1.0);
                ui.put(cv, a, lantern, scene.x + scene.w - 46, scene.y + 6, 1.0);
                let fl = 0.25 + 0.06 * (ui.t * 9.0).sin();
                cv.glow((scene.x + 28) as f32, (scene.y + 30) as f32, 40.0, [255, 170, 70], fl);
                cv.glow((scene.x + scene.w - 28) as f32, (scene.y + 30) as f32, 40.0, [255, 170, 70], fl);
                ui.put(cv, a, "anvil", scene.cx() - 36, scene.y + 110, 1.0);
                let g = ((ui.t * 6.0) as usize) % 8;
                ui.put(cv, a, &format!("gear_16_{g}"), scene.cx() - 50, scene.y + 52, 1.0);
                ui.put(cv, a, &format!("gear_10_{}", 7 - g), scene.cx() - 16, scene.y + 72, 1.0);
                ui.icon(cv, a, currency_icon(cls), scene.cx() + 20, scene.y + 66, 3, 1.0);
                let service = if cls == Class::Foundry { t("shop.service.0") } else { t("shop.service.1") };
                para(cv, a, &tf("node.merchant.l", &[("service", &service.to_lowercase())]), r.x + 20, r.y + 224, r.w - 40, MUTED);
            }
            Kind::Event => {
                let k2 = 0.6 + 0.4 * (ui.t * 2.5).sin();
                cv.glow(scene.cx() as f32, scene.cy() as f32, 70.0, [160, 120, 240], 0.25 * k2);
                a.fonts["title24"].draw_grad(cv, "?", scene.cx(), scene.cy() - 16, VIOLET, [90, 60, 140], EDGE, Align::Center, 1.0);
                para(cv, a, &t("node.event.l"), r.x + 20, r.y + 224, r.w - 40, MUTED);
            }
            Kind::Camp => {
                let fl = 0.35 + 0.1 * (ui.t * 7.0).sin() + 0.05 * (ui.t * 13.0).sin();
                let g = if cls == Class::Foundry { [255, 130, 50] } else { [140, 220, 70] };
                cv.glow(scene.cx() as f32, (scene.y + scene.h - 30) as f32, 80.0, g, fl);
                ui::motes(cv, ui.t, Rect::new(scene.cx() - 40, scene.y + 20, 80, scene.h - 40), 16, cls, 1.0);
                let icon = if cls == Class::Foundry { "glyph/ремонт" } else { "swarm/clutch" };
                let k = if cls == Class::Foundry { 4 } else { 3 };
                ui.icon(cv, a, icon, scene.cx() - 22, scene.y + 50, k, 1.0);
                para(cv, a, &t(&format!("node.camp.l.{c}")), r.x + 20, r.y + 224, r.w - 40, MUTED);
            }
            _ => {}
        }
        if hit || ui.key(Key::Digit(i as u8 + 1)) {
            act = Some(Act::Road(i));
        }
    }
    // the army on the sill, and its button
    army_strip(cv, a, run, 190, 522, 740);
    if ui.minor(cv, a, cls, "army", 14, 484, &t("bar.army"), true) {
        act = Some(Act::Army);
    }
    act
}

// ---------------------------------------------------------------- the spoils

fn rewards(ui: &mut Ui, cv: &mut Image, a: &Assets, run: &Run, list: &mut [(Reward, bool)], pick: Option<usize>) -> Option<Act> {
    let cls = run.class;
    let c = ci(cls);
    ui::motes(cv, ui.t, Rect::new(0, 60, 960, 400), 24, cls, 0.6);
    top(ui, cv, a, run, &t(&format!("rewards.title.{c}")), &t("rewards.sub"));
    bottom(ui, cv, a, cls);
    let mut act = None;
    let panel = Rect::new(258, 66, 444, 390);
    if pick.is_none() {
        plate(ui, cv, a, cls, panel);
    }
    if pick.is_none() {
        heading(cv, a, &t("battle.loot"), panel.cx(), panel.y + 22, 24, cols(cls), Align::Center);
    }
    let mut y = panel.y + 70;
    let mut left = 0;
    // with the find open, the spoils under it don't answer; an overlay over both blocks the find too
    let outer = ui.blocked;
    if pick.is_some() {
        ui.blocked = true;
    }
    for (i, (r, taken)) in list.iter().enumerate() {
        if *taken || pick.is_some() {
            continue;
        }
        left += 1;
        let row = Rect::new(panel.x + 24, y + ui.rise(left), panel.w - 48, 52);
        let can = run.can_take(r);
        let (_, _, hit) = ui.card(cv, a, cls, &format!("rw{i}"), row, if can { "normal" } else { "locked" }, can);
        let ix = row.x + 16;
        let (label, col) = match r {
            Reward::Money(n) => {
                ui.icon(cv, a, currency_icon(cls), ix, row.y + 16, 2, 1.0);
                (tf("rewards.money", &[("n", n), ("cur", &t(&format!("cur.gen.{c}")))]), GOLD)
            }
            Reward::Repair(p) => {
                ui.icon(cv, a, "glyph/ремонт", ix, row.y + 15, 2, 1.0);
                let n = run.broken();
                let g = if n == 1 { t("golems.1") } else { t("golems.n") };
                if can {
                    (tf("rewards.repair", &[("n", &n), ("golems", &g), ("p", p)]), INK)
                } else {
                    (tf("rewards.repair.no", &[("p", p)]), MUTED)
                }
            }
            Reward::Brood(ts) => {
                ui.icon(cv, a, "swarm/clutch", ix - 4, row.y + 10, 2, 1.0);
                (tf("rewards.brood", &[("n", &ts.len())]), ACID2)
            }
            Reward::Find(_) => {
                ui.icon(cv, a, "glyph/выбор", ix, row.y + 17, 2, 1.0);
                (t("rewards.find"), BLUE)
            }
            Reward::Artifact(art) => {
                artifact_icon(ui, cv, a, *art, ix - 6, row.y + 10, 2);
                (tf("rewards.artifact", &[("name", &t(&format!("art.{}", art.key())))]), GOLD)
            }
            Reward::Growth(_) => {
                ui.icon(cv, a, if cls == Class::Foundry { "glyph/рост" } else { "swarm/selection" }, ix, row.y + 15, 2, 1.0);
                (t("rewards.growth"), GOLD)
            }
        };
        a.fonts["text16"].draw(cv, &label, row.x + 52, row.y + 17, if can { col } else { MUTED }, Some(EDGE), Align::Left, 1.0);
        if let Reward::Artifact(art) = r {
            if ui.hot(&format!("rwt{i}"), row).0 {
                ui.tooltip(artifact_tip(*art));
            }
        }
        if hit || ui.key(Key::Digit(left as u8)) {
            act = Some(match r {
                Reward::Find(_) | Reward::Growth(_) => Act::OpenFind(i),
                _ => Act::Take(i),
            });
        }
        y += 60;
    }
    if left == 0 {
        text(cv, a, "·", panel.cx(), panel.y + 90, PALE, Align::Center);
    } else {
        text(cv, a, &tf("rewards.left", &[("n", &left)]), 24, 492, MUTED, Align::Left);
    }
    if ui.action(cv, a, cls, "next", 652, 478, &t("rewards.next"), true) || ui.key(Key::Enter) {
        act = Some(Act::LeaveRewards);
    }
    // the swarm spends its biomass on its forms right here, as the brood hatches
    if cls == Class::Swarm && pick.is_none() && ui.minor(cv, a, cls, "evo", 300, 484, &t("evo.open"), true) {
        act = Some(Act::Evolution);
    }
    // the find: three cards over the screen, or none
    if let Some(i) = pick {
        ui.blocked = outer;
        if let Some((Reward::Find(offers), _)) = list.get(i) {
            cv.fill(0, 44, 960, 424, [6, 4, 8, 120]);
            heading(cv, a, &t("pick.title"), 480, 58, 24, cols(cls), Align::Center);
            text(cv, a, &t("pick.sub"), 480, 92, MUTED, Align::Center);
            let n = offers.len() as i32;
            let (cw, gap) = (220, 34);
            let x0 = (960 - n * cw - (n - 1) * gap) / 2;
            for (j, o) in offers.iter().enumerate() {
                let r = Rect::new(x0 + j as i32 * (cw + gap), 126 + ui.rise_from(ui.opened, j), cw, 300);
                let (_, hit) = offer_card(ui, cv, a, run, &format!("pick{j}"), r, o, "new", true);
                if hit || ui.key(Key::Digit(j as u8 + 1)) {
                    act = Some(Act::Pick(i, Some(j)));
                }
            }
            if ui.minor(cv, a, cls, "skip", 380, 452, &tf("pick.skip", &[("cur", &t(&format!("cur.gen.{c}")))]), true) {
                act = Some(Act::Pick(i, None));
            }
            // back to the spoils, the find still there to take (Esc does the same)
            if ui.minor(cv, a, cls, "pickback", 14, 484, &t("back"), true) {
                act = Some(Act::CloseFind);
            }
        }
        // the leader's growth: two cards, one for good
        if let Some((Reward::Growth(keys), _)) = list.get(i) {
            cv.fill(0, 44, 960, 424, [6, 4, 8, 120]);
            heading(cv, a, &t("growth.title"), 480, 58, 24, cols(cls), Align::Center);
            text(cv, a, &t("growth.sub"), 480, 92, MUTED, Align::Center);
            let n = keys.len() as i32;
            let (cw, gap) = (240, 48);
            let x0 = (960 - n * cw - (n - 1) * gap) / 2;
            for (j, key) in keys.iter().enumerate() {
                let r = Rect::new(x0 + j as i32 * (cw + gap), 140 + ui.rise_from(ui.opened, j), cw, 250);
                if growth_card(ui, cv, a, run, &format!("grow{j}"), r, key) || ui.key(Key::Digit(j as u8 + 1)) {
                    act = Some(Act::Pick(i, Some(j)));
                }
            }
            if ui.minor(cv, a, cls, "pickback", 14, 484, &t("back"), true) {
                act = Some(Act::CloseFind);
            }
        }
    }
    ui.blocked = outer;
    act
}

// ---------------------------------------------------------------- the trader

fn shop_screen(ui: &mut Ui, cv: &mut Image, a: &Assets, run: &Run, shop: &sim::run::Shop) -> Option<Act> {
    let cls = run.class;
    let c = ci(cls);
    top(ui, cv, a, run, &t("shop.title"), &t(&format!("shop.sub.{c}")));
    bottom(ui, cv, a, cls);
    // the stall: a lantern either side, warm light on the counter
    let lantern = if cls == Class::Foundry { "lantern_on" } else { "swarm/lantern_on" };
    let fl = 0.22 + 0.05 * (ui.t * 9.0).sin() + 0.03 * (ui.t * 17.0).sin();
    for x in [8, 912] {
        ui.put(cv, a, lantern, x, 50, 1.0);
        cv.glow((x + 20) as f32, 74.0, 70.0, [255, 170, 70], fl);
    }
    let mut act = None;
    heading(cv, a, &t("shop.recruits"), 60, 56, 16, cols(cls), Align::Left);
    let (cw, gap) = (196, 18);
    for (i, (o, sold)) in shop.offers.iter().enumerate() {
        let r = Rect::new(60 + i as i32 * (cw + gap), 74 + ui.rise(i), cw, 226);
        let can = !sold && run.money >= o.price;
        let (_, hit) = offer_card(ui, cv, a, run, &format!("off{i}"), r, o, "normal", !sold);
        if *sold {
            sold_stamp(ui, cv, a, r);
        } else {
            price_tag(ui, cv, a, cls, r.cx(), r.y + r.h + 6, o.price, can);
        }
        if hit && can {
            act = Some(Act::BuyOffer(i));
        } else if hit {
            ui.sound("toggle");
        }
    }
    let y2 = 350;
    heading(cv, a, &t("shop.artifacts"), 60, y2 - 8, 16, cols(cls), Align::Left);
    for (i, (art, price, sold)) in shop.artifacts.iter().enumerate() {
        let r = Rect::new(60 + i as i32 * 232, y2 + 8, 222, 78);
        let can = !sold && run.money >= *price;
        let (over, _, hit) = ui.card(cv, a, cls, &format!("shopart{i}"), r, "rare", !sold);
        let sock = if cls == Class::Foundry { "foundry/artifact_socket_normal" } else { "swarm/artifact_cell_normal" };
        ui.put(cv, a, sock, r.x + 12, r.y + 10, 1.0);
        artifact_icon(ui, cv, a, *art, r.x + 10, r.y + 8, 2);
        text(cv, a, &t(&format!("art.{}", art.key())), r.x + 54, r.y + 8, GOLD, Align::Left);
        let mut yy = r.y + 28;
        for l in a.fonts["text16"].wrap(&t(&format!("art.{}.l", art.key())), r.w - 66).into_iter().take(2) {
            text(cv, a, &l, r.x + 54, yy, INK, Align::Left);
            yy += 18;
        }
        if *sold {
            sold_stamp(ui, cv, a, r);
        } else {
            price_tag(ui, cv, a, cls, r.x + 30, r.y + r.h + 4, *price, can);
        }
        if over {
            ui.tooltip(artifact_tip(*art));
        }
        if hit && can {
            act = Some(Act::BuyArtifact(i));
        }
    }
    heading(cv, a, &t("shop.service"), 540, y2 - 8, 16, cols(cls), Align::Left);
    let r = Rect::new(540, y2 + 8, 360, 78);
    let needed = cls == Class::Swarm || run.broken() > 0;
    let can = !shop.service_used && needed && run.money >= shop.service;
    let (_, _, hit) = ui.card(cv, a, cls, "svc", r, "trophy", !shop.service_used && needed);
    let icon = if cls == Class::Foundry { "glyph/ремонт" } else { "swarm/clutch" };
    ui.icon(cv, a, icon, r.x + 16, r.y + 20, if cls == Class::Foundry { 3 } else { 2 }, 1.0);
    text(cv, a, &t(&format!("shop.service.{c}")), r.x + 60, r.y + 16, INK, Align::Left);
    if !needed {
        text(cv, a, &t("shop.service.none"), r.x + 60, r.y + 38, MUTED, Align::Left);
    }
    if shop.service_used {
        sold_stamp(ui, cv, a, r);
    } else if needed {
        price_tag(ui, cv, a, cls, r.x + r.w - 60, r.y + 10, shop.service, can);
    }
    if hit && can {
        act = Some(Act::BuyService);
    }
    if ui.minor(cv, a, cls, "leave", 790, 482, &t("shop.leave"), true) || ui.key(Key::Enter) {
        act = Some(Act::LeaveStop);
    }
    army_strip(cv, a, run, 30, 522, 700);
    act
}

// ---------------------------------------------------------------- an event

fn effect_good(e: Effect) -> bool {
    !matches!(e, Effect::Hurt(_) | Effect::TradeUnit | Effect::BuyArtifact(_) | Effect::Money(i32::MIN..=-1))
}

/// The event's picture: a scene of the game's own bodies and props, drawn at 1× and shown twice as large (as the
/// battle's camera would show them up close), on the class's own wall.
fn event_scene(ui: &mut Ui, cv: &mut Image, a: &Assets, key: &str, cls: Class, r: Rect) {
    let t = ui.t;
    let wall = if cls == Class::Foundry { "forge" } else { "hive" };
    let mut sc = Image::new(r.w / 2, r.h / 2);
    let (w, h) = (sc.w, sc.h);
    if let Some(bg) = a.bg.get(wall) {
        sc.blit_region(bg, 120, 160, w, h, 0, 0, false, 1.0);
    }
    sc.dim(0, 0, w, h, 0.75);
    let floor = h - 34;
    sc.fill(0, floor, w, h - floor, [24, 19, 22, 255]);
    sc.fill(0, floor, w, 1, [44, 36, 40, 255]);
    let put = |sc: &mut Image, name: &str, x: i32, y: i32| {
        if let Some(p) = a.ui.get(name) {
            sc.blit(&p.img, x, y, false, 1.0);
        }
    };
    let body = |sc: &mut Image, name: &str, gx: i32, gy: i32, flip: bool| {
        if let Some(s) = a.sprites.get(name) {
            let ox = if flip { s.img.w - 1 - s.ox } else { s.ox };
            sc.shadow(gx as f32, gy as f32, (s.img.w as f32 * 0.6).min(40.0), 4.0);
            sc.blit(&s.img, gx - ox, gy - s.oy, flip, 1.0);
        }
    };
    match key {
        "forge" => {
            sc.glow(48.0, floor as f32 - 6.0, 70.0, [255, 110, 40], 0.45 + 0.08 * (t * 8.0).sin());
            put(&mut sc, "anvil", 16, floor - 30);
            let g = ((t * 5.0) as usize) % 8;
            put(&mut sc, &format!("gear_16_{g}"), w - 70, 14);
            put(&mut sc, &format!("gear_10_{}", 7 - g), w - 42, 38);
            put(&mut sc, "lantern_on", 98, 0);
            sc.glow(114.0, 24.0, 30.0, [255, 170, 70], 0.3);
            ui::motes(&mut sc, t, Rect::new(10, 20, 80, floor - 20), 14, Class::Foundry, 1.0);
            body(&mut sc, "Орудие_4_broken", w - 50, floor + 6, true);
        }
        "rockfall" => {
            for (i, (dx, rr)) in [(18, 22), (52, 30), (90, 26), (128, 34), (164, 20)].iter().enumerate() {
                for yy in -rr / 2..rr / 2 {
                    let hw = ((rr * rr / 4 - yy * yy) as f32).sqrt() as i32;
                    let sh = 52 + (i as i32 * 9) % 20 - yy / 2;
                    sc.fill(dx - hw, floor - rr / 2 + yy + 4, 2 * hw, 1, [sh as u8, (sh - 4) as u8, (sh + 3) as u8, 255]);
                }
            }
            body(&mut sc, "Мудрец_4_idle", 50, floor + 6, false);
            for i in 0..24u32 {
                let ph = ((t * 0.3) + i as f32 * 0.137).fract();
                sc.blend_px(8 + ((i * 53) % (w as u32 - 16)) as i32, floor - (ph * 90.0) as i32, [160, 150, 140, 255], 0.6 * (1.0 - ph));
            }
        }
        "nest" => {
            sc.glow(w as f32 / 2.0, floor as f32, 80.0, [120, 200, 60], 0.3);
            for yy in 0..22 {
                let hw = (46.0 * (1.0 - (yy as f32 / 22.0).powi(2)).sqrt()) as i32;
                sc.fill(w / 2 - hw, floor - yy, 2 * hw, 1, [44, 32, 26, 255]);
            }
            sc.fill(w / 2 - 5, floor - 12, 10, 8, [8, 6, 6, 255]);
            for (i, (dx, dy)) in [(-64, 4), (-34, 10), (40, 6), (66, 12), (-12, 16), (16, 14)].iter().enumerate() {
                let pose = if (t * 3.0 + i as f32) as i32 % 3 == 0 { "attack" } else { "idle" };
                body(&mut sc, &format!("Муравей (рабочая)_{}_{pose}", i % 4), w / 2 + dx, floor + dy - 2, *dx > 0);
            }
        }
        "carcass" => {
            body(&mut sc, "Страж_5_broken", w / 2, floor + 8, false);
            sc.glow(w as f32 / 2.0, (floor - 26) as f32, 34.0, [255, 140, 60], 0.18 + 0.06 * (t * 2.0).sin());
            for (i, dx) in [-70, -46, 52, 76].iter().enumerate() {
                let pose = if (t * 4.0 + i as f32) as i32 % 2 == 0 { "attack" } else { "idle" };
                body(&mut sc, &format!("Муравей (рабочая)_{}_{pose}", i % 4), w / 2 + dx, floor + 12, *dx > 0);
            }
        }
        "shadow" => {
            sc.glow(w as f32 / 2.0, (h / 2) as f32, 90.0, [110, 70, 180], 0.35);
            if let Some(s) = a.sprites.get("Чума_idle") {
                sc.blit_shade(&s.img, w / 2 - s.ox, floor + 8 - s.oy, false, 0.07, 1.0);
                let k = 0.6 + 0.4 * (t * 2.0).sin();
                sc.glow((w / 2 + 14) as f32, (floor - 22) as f32, 5.0, [220, 160, 255], 0.9 * k);
            }
            put(&mut sc, "lantern_off", 14, 4);
            for i in 0..36u32 {
                let ph = ((t * 0.15) + i as f32 * 0.071).fract();
                sc.blend_px(((i * 97) % w as u32) as i32, h - (ph * h as f32) as i32, [130, 110, 160, 255], 0.4 * (1.0 - ph));
            }
        }
        _ => {
            // the deserter: one of the other side's, sitting it out by the road
            sc.glow(w as f32 / 2.0, floor as f32, 60.0, [200, 160, 110], 0.2);
            let name = match cls {
                Class::Foundry => "Механик_3_idle",
                Class::Swarm => "Оса (рабочая)_1_idle",
            };
            body(&mut sc, name, w / 2, floor + 6, true);
        }
    }
    let big = sc.scaled(2);
    cv.blit(&big, r.x, r.y, false, 1.0);
    cv.fill(r.x, r.y, r.w, 2, [0, 0, 0, 255]);
    cv.fill(r.x, r.y + r.h - 2, r.w, 2, [0, 0, 0, 255]);
}

fn event(ui: &mut Ui, cv: &mut Image, a: &Assets, run: &Run, id: usize, done: &Option<String>) -> Option<Act> {
    let cls = run.class;
    let (key, _, effects) = EVENTS[id];
    top(ui, cv, a, run, &t("event.title"), &t(&format!("event.{key}.title")));
    bottom(ui, cv, a, cls);
    let mut act = None;
    let left = Rect::new(20, 62, 398, 396);
    plate(ui, cv, a, cls, left);
    event_scene(ui, cv, a, key, cls, left.inset(18));
    let x = 446;
    heading(cv, a, &t(&format!("event.{key}.title")), x, 70, 24, cols(cls), Align::Left);
    let mut y = para(cv, a, &t(&format!("event.{key}.body")), x, 112, 490, INK) + 14;
    match done {
        None => {
            for (o, eff) in effects.iter().enumerate() {
                let r = Rect::new(x, y + ui.rise(o + 1), 494, 58);
                let can = run.event_can(id, o);
                let (_, _, hit) = ui.card(cv, a, cls, &format!("opt{o}"), r, if can { "normal" } else { "locked" }, can);
                a.fonts["title16"].draw(cv, &format!("{}", o + 1), r.x + 18, r.y + 20, if can { GOLD } else { PALE }, Some(EDGE), Align::Left, 1.0);
                text(cv, a, &t(&format!("event.{key}.{o}")), r.x + 46, r.y + 10, if can { INK } else { MUTED }, Align::Left);
                let fx = if can { t(&format!("event.{key}.{o}.fx")) } else { t("event.cant") };
                let fc = if !can {
                    PALE
                } else if *eff == Effect::Leave {
                    MUTED
                } else if effect_good(*eff) {
                    GOLD
                } else {
                    RED
                };
                text(cv, a, &fx, r.x + 46, r.y + 30, fc, Align::Left);
                if hit || (can && ui.key(Key::Digit(o as u8 + 1))) {
                    act = Some(Act::EventChoose(o));
                }
                y += 66;
            }
        }
        Some(said) => {
            text(cv, a, said, x, y + 6, GOLD, Align::Left);
            if ui.action(cv, a, cls, "next", 652, 478, &t("event.next"), true) || ui.key(Key::Enter) {
                act = Some(Act::LeaveStop);
            }
        }
    }
    act
}

// ---------------------------------------------------------------- the camp

fn camp(ui: &mut Ui, cv: &mut Image, a: &Assets, run: &Run, stage: CampStage, said: &str) -> Option<Act> {
    let cls = run.class;
    let c = ci(cls);
    // the fire low in the middle
    let fl = 0.32 + 0.07 * (ui.t * 7.0).sin() + 0.04 * (ui.t * 13.0).sin();
    let g = if cls == Class::Foundry { [255, 120, 40] } else { [130, 210, 60] };
    cv.glow(480.0, 470.0, 340.0, g, fl * 0.5);
    ui::motes(cv, ui.t, Rect::new(330, 200, 300, 270), 30, cls, 1.0);
    top(ui, cv, a, run, &t(&format!("camp.title.{c}")), &t(&format!("camp.sub.{c}")));
    bottom(ui, cv, a, cls);
    let mut act = None;
    match stage {
        CampStage::Choose => {
            let opts = [
                (t(&format!("camp.rest.{c}")), tf(&format!("camp.rest.{c}.l"), &[("n", &(4 + run.fight as usize / 3))]), if cls == Class::Foundry { "glyph/ремонт" } else { "swarm/clutch" }),
                (t(&format!("camp.up.{c}")), t(&format!("camp.up.{c}.l")), if cls == Class::Foundry { "glyph/рост" } else { "swarm/selection" }),
            ];
            for (i, (title, line, icon)) in opts.iter().enumerate() {
                let r = Rect::new(150 + i as i32 * 360, 96 + ui.rise(i), 300, 300);
                let on = !(i == 0 && cls == Class::Foundry && run.broken() == 0);
                let (_, k, hit) = ui.card(cv, a, cls, &format!("camp{i}"), r, if i == 0 { "hi" } else { "rare" }, on);
                let r = r.shift(0, -(k * 4.0).round() as i32);
                cv.glow(r.cx() as f32, (r.y + 100) as f32, 70.0, g, 0.15 + 0.2 * k);
                let ik = if icon.starts_with("glyph") { 6 } else { 4 };
                ui.icon(cv, a, icon, r.cx() - 32, r.y + 64, ik, if on { 1.0 } else { 0.4 });
                heading(cv, a, title, r.cx(), r.y + 168, 24, if on { cols(cls) } else { (MUTED, PALE) }, Align::Center);
                let mut y = r.y + 210;
                let line = if on { line.clone() } else { t("shop.service.none") };
                for l in a.fonts["text16"].wrap(&line, r.w - 40) {
                    text(cv, a, &l, r.cx(), y, if on { INK } else { MUTED }, Align::Center);
                    y += 20;
                }
                if (hit || ui.key(Key::Digit(i as u8 + 1))) && on {
                    act = Some(if i == 0 { Act::CampRest } else { Act::CampUp });
                }
            }
            // the Foundry's workshop, the swarm's evolutions: the choice above still there after them
            if cls == Class::Foundry {
                let any = run.army.iter().any(|m| !m.mods.is_empty());
                if ui.minor(cv, a, cls, "workshop", 14, 484, &t("ws.open"), any) {
                    act = Some(Act::Workshop);
                }
            } else if ui.minor(cv, a, cls, "evo", 14, 484, &t("evo.open"), true) {
                act = Some(Act::Evolution);
            }
        }
        CampStage::Workshop { held } => {
            if let Some(x) = workshop(ui, cv, a, run, held) {
                act = Some(x);
            }
        }
        CampStage::Pick => {
            heading(cv, a, &t("camp.pick"), 480, 60, 16, cols(cls), Align::Center);
            // the Foundry tempers one golem; the swarm breeds one kind (all of its name)
            let mut items: Vec<(usize, Template, usize)> = vec![];
            for (i, m) in run.army.iter().enumerate() {
                if cls == Class::Swarm {
                    if let Some(it) = items.iter_mut().find(|(_, t, _)| t.name == m.t.name) {
                        it.2 += 1;
                        continue;
                    }
                }
                items.push((i, m.t.clone(), 1));
            }
            if ui.minor(cv, a, cls, "campback", 14, 484, &t("back"), true) {
                act = Some(Act::CampBack);
            }
            let (cw, ch, gap) = (140, 186, 12);
            let per = 6;
            for (j, (m, tt, n)) in items.iter().enumerate().take(12) {
                let (col, row) = (j % per, j / per);
                let r = Rect::new(36 + col as i32 * (cw + gap), 84 + row as i32 * (ch + gap), cw, ch);
                let broken = run.army[*m].broken;
                let _ = tt;
                let (_, hit) = unit_card(ui, cv, a, cls, &format!("cp{j}"), r, &run.body(&run.army[*m]), *n, if broken { "broken" } else { "normal" }, true);
                marks(ui, cv, a, run, r, &run.army[*m]);
                if hit {
                    act = Some(Act::CampPick(*m));
                }
            }
        }
        CampStage::Done => {
            heading(cv, a, said, 480, 220, 24, cols(cls), Align::Center);
            if ui.action(cv, a, cls, "next", 652, 478, &t("camp.next"), true) || ui.key(Key::Enter) {
                act = Some(Act::LeaveStop);
            }
            if cls == Class::Foundry && ui.minor(cv, a, cls, "workshop", 14, 484, &t("ws.open"), run.army.iter().any(|m| !m.mods.is_empty())) {
                act = Some(Act::Workshop);
            }
            if cls == Class::Swarm && ui.minor(cv, a, cls, "evo", 14, 484, &t("evo.open"), true) {
                act = Some(Act::Evolution);
            }
        }
    }
    army_strip(cv, a, run, 200, 522, 600);
    act
}

/// The workshop at the Foundry's camp: every golem with its cells; a module picked up goes into a free cell where it
/// fits (free) or melts into another module of the same frame (+1 level for its metal).
fn workshop(ui: &mut Ui, cv: &mut Image, a: &Assets, run: &Run, held: Option<(usize, usize)>) -> Option<Act> {
    let cls = run.class;
    let mut act = None;
    heading(cv, a, &t("ws.title"), 480, 58, 24, cols(cls), Align::Center);
    text(cv, a, &t("ws.sub"), 480, 90, MUTED, Align::Center);
    if ui.minor(cv, a, cls, "campback", 14, 484, &t("back"), true) {
        act = Some(Act::CampBack);
    }
    let golems: Vec<usize> = (0..run.army.len()).filter(|&i| run.army[i].t.golem || !run.army[i].mods.is_empty()).collect();
    // ten golems fit, lower rows for more than eight; the rest are counted
    let compact = golems.len() > 8;
    let (tw, th, gap) = if compact { (300, 58, 6) } else { (300, 72, 8) };
    let (name_y, cell_y) = if compact { (4, 20) } else { (8, 30) };
    if golems.len() > 10 {
        text(cv, a, &tf("army.more", &[("n", &(golems.len() - 10))]), 36, 442, MUTED, Align::Left);
    }
    let held_key = held.and_then(|(m, j)| run.army.get(m).and_then(|x| x.mods.get(j)).cloned());
    let mut tip = None;
    for (n, &mi) in golems.iter().enumerate().take(10) {
        let m = &run.army[mi];
        let (col, row) = ((n % 2) as i32, (n / 2) as i32);
        let r = Rect::new(36 + col * (tw + 12), 116 + row * (th + gap) + ui.rise_from(ui.opened, n), tw, th);
        plate(ui, cv, a, cls, r);
        let mut pic = Image::clear(56, th - 8);
        small(&mut pic, a, &m.t, 28, th - 14, false, m.broken);
        cv.blit(&pic, r.x + 6, r.y + 4, false, 1.0);
        a.fonts["text16"].draw(cv, &m.t.name, r.x + 70, r.y + name_y, if m.broken { MUTED } else { [255, 214, 150] }, Some(EDGE), Align::Left, 1.0);
        for j in 0..run.cells(m) {
            let s = Rect::new(r.x + 70 + j as i32 * 42, r.y + cell_y, 36, 36);
            let filled = j < m.mods.len();
            let (over, _) = ui.hot(&format!("ws{mi}_{j}"), s);
            // what a click there would do with the module held: a place for it, a module to melt it into
            let fits = held_key.as_ref().is_some_and(|k| !filled && held.map(|h| h.0) != Some(mi) && run.fits(mi, k));
            let melts = held.is_some_and(|(hm, hj)| filled && run.can_melt(hm, hj, mi, j));
            let is_held = held == Some((mi, j));
            let pulse = 0.5 + 0.5 * (ui.t * 6.0).sin();
            let rim: [u8; 4] = if is_held {
                [255, 214, 120, 255]
            } else if fits {
                [120, 200, 120, (150.0 + 100.0 * pulse) as u8]
            } else if melts {
                [255, 130, 50, (150.0 + 100.0 * pulse) as u8]
            } else if over {
                [230, 220, 200, 255]
            } else {
                [110, 92, 66, 255]
            };
            cv.fill(s.x - 1, s.y - 1, s.w + 2, s.h + 2, rim);
            cv.fill(s.x, s.y, s.w, s.h, [14, 11, 12, 255]);
            if filled {
                let key = &m.mods[j];
                ui.icon(cv, a, &format!("module/{key}"), s.x + 2, s.y + 2, 2, if is_held { 0.35 } else { 1.0 });
                // its level: pips along the cell's foot
                for p in 0..sim::run::MAX_LEVEL {
                    let c: [u8; 4] = if p < m.level(j) { [255, 200, 90, 255] } else { [60, 50, 40, 255] };
                    cv.fill(s.x + 3 + p as i32 * 6, s.y + s.h - 6, 4, 4, c);
                }
                if over {
                    let lv = t(&format!("lvl.{}", m.level(j)));
                    tip = Some(vec![(t(&format!("find.{key}")), GOLD), (tf("ws.level", &[("n", &lv)]), INK), (t(&format!("find.{key}.l")), BLUE)]);
                }
            }
            if ui.clicked(s) {
                act = Some(Act::Socket(mi, j));
            }
        }
    }
    // the crucible: what is held and what can be done with it
    let side = Rect::new(660, 116, 270, 300);
    plate(ui, cv, a, cls, side);
    heading(cv, a, &t("ws.crucible"), side.cx(), side.y + 22, 16, cols(cls), Align::Center);
    let glow = 0.18 + 0.06 * (ui.t * 3.0).sin() + if held.is_some() { 0.12 } else { 0.0 };
    cv.glow(side.cx() as f32, (side.y + 92) as f32, 60.0, [255, 130, 50], glow);
    let font = &a.fonts["text16"];
    let mut y = side.y + 56;
    let lines: Vec<(String, [u8; 3])> = match (&held_key, held) {
        (Some(k), Some((hm, hj))) => {
            ui.icon(cv, a, &format!("module/{k}"), side.cx() - 32, y, 4, 1.0);
            y += 76;
            let lv = t(&format!("lvl.{}", run.army[hm].level(hj)));
            vec![
                (format!("{} · {}", t(&format!("find.{k}")), lv), GOLD),
                (t("ws.move"), [150, 210, 150]),
                (tf("ws.melt", &[("n", &sim::run::MELT)]), [255, 160, 90]),
            ]
        }
        _ => vec![(t("ws.take"), INK), (t("ws.move"), MUTED), (tf("ws.melt", &[("n", &sim::run::MELT)]), MUTED)],
    };
    for (l, c) in lines {
        for w in font.wrap(&l, side.w - 28) {
            if y + 16 > side.y + side.h - 8 {
                break;
            }
            font.draw(cv, &w, side.cx(), y, c, Some(EDGE), Align::Center, 1.0);
            y += 18;
        }
        y += 6;
    }
    // the module held follows the mouse
    if let Some(k) = &held_key {
        ui.icon(cv, a, &format!("module/{k}"), ui.mx - 16, ui.my - 16, 2, 0.85);
    }
    if let Some(lines) = tip {
        ui.tooltip(lines);
    }
    act
}

/// The swarm's evolutions: each form of the army with its own, what the next costs; one clicked is bought (the whole
/// breed, the brood to come too).
fn evolution(ui: &mut Ui, cv: &mut Image, a: &Assets, run: &Run) -> Option<Act> {
    let cls = run.class;
    let r = Rect::new(40, 24, 880, 492);
    plate(ui, cv, a, cls, r);
    heading(cv, a, &t("evo.title"), 480, r.y + 12, 24, cols(cls), Align::Center);
    text(cv, a, &t("evo.sub"), 480, r.y + 44, MUTED, Align::Center);
    let mut act = None;
    let forms: Vec<String> = run.forms().into_iter().filter(|f| !Run::evolutions(f).is_empty()).collect();
    // every form that has evolutions gets its row (eight at most): lower rows when there are more than five
    let compact = forms.len() > 5;
    let (step, th) = if compact { (44, 40) } else { (62, 52) };
    if forms.is_empty() {
        text(cv, a, &t("evo.none"), 480, r.y + 140, PALE, Align::Center);
    }
    let font = &a.fonts["text16"];
    let mut tip = None;
    for (i, form) in forms.iter().enumerate().take(8) {
        let y = r.y + 70 + i as i32 * step + ui.rise_from(ui.opened, i);
        // the form: a body of it, its name, what its next evolution costs
        if let Some(m) = run.army.iter().find(|m| form_of(&m.t) == form && !run.is_leader(m)) {
            let mut pic = Image::clear(60, th + 4);
            small(&mut pic, a, &m.t, 30, th - 2, false, false);
            cv.blit(&pic, r.x + 24, y - 2, false, 1.0);
        }
        font.draw(cv, form, r.x + 92, y + if compact { 2 } else { 6 }, ACID2, Some(EDGE), Align::Left, 1.0);
        let price = run.evo_price(form);
        let can_pay = run.money >= price;
        let (py, ik) = if compact { (y + 21, 1) } else { (y + 30, 2) };
        ui.icon(cv, a, currency_icon(cls), r.x + 92, py, ik, 1.0);
        a.fonts["title16"].draw(cv, &price.to_string(), r.x + 100 + 8 * ik, py, if can_pay { GOLD } else { RED }, Some(EDGE), Align::Left, 1.0);
        for (j, e) in Run::evolutions(form).iter().enumerate() {
            let tile = Rect::new(r.x + 200 + j as i32 * 222, y, 212, th);
            let taken = run.breeds.iter().any(|(f, k)| f == form && k == &e.key);
            let on = !taken && can_pay;
            let (over, k) = ui.hot(&format!("evo{i}_{j}"), tile);
            let rim: [u8; 4] = if taken {
                [255, 200, 90, 255]
            } else if over && on {
                [170, 240, 90, 255]
            } else {
                [96, 80, 110, 255]
            };
            cv.fill(tile.x - 1, tile.y - 1, tile.w + 2, tile.h + 2, rim);
            cv.fill(tile.x, tile.y, tile.w, tile.h, if taken { [40, 32, 18, 255] } else { [18, 14, 22, 255] });
            if on {
                cv.glow(tile.x as f32 + 26.0, tile.cy() as f32, 30.0, [150, 230, 70], 0.1 + 0.2 * k);
            }
            ui.icon(cv, a, &format!("swarm/{}", e.key), tile.x + 8, tile.y + (th - 32) / 2, 2, if taken || on { 1.0 } else { 0.45 });
            let name = t(&format!("find.{}", e.key));
            let lines = font.wrap(&name, tile.w - 56);
            let rows = if compact { 1 } else { 2 };
            let mut ly = tile.y + if lines.len() > 1 && !compact { 2 } else { (th - 16) / 2 - 2 };
            for l in lines.iter().take(rows) {
                font.draw(cv, l, tile.x + 48, ly, if taken { GOLD } else if on { INK } else { MUTED }, Some(EDGE), Align::Left, 1.0);
                ly += 18;
            }
            if taken && !compact {
                font.draw(cv, &t("evo.taken"), tile.x + tile.w - 8, tile.y + tile.h - 20, GOLD, Some(EDGE), Align::Right, 1.0);
            }
            if over {
                tip = Some(vec![(name, GOLD), (t(&format!("find.{}.l", e.key)), BLUE)]);
            }
            if on && ui.clicked(tile) {
                act = Some(Act::Evolve(form.clone(), e.key.clone()));
            }
        }
    }
    if ui.minor(cv, a, cls, "evoback", 410, 474, &t("back"), true) {
        act = Some(Act::CloseOverlay);
    }
    if let Some(lines) = tip {
        ui.tooltip(lines);
    }
    act
}

// ---------------------------------------------------------------- the end of the run

fn end(ui: &mut Ui, cv: &mut Image, a: &Assets, run: &Run, victory: bool) -> Option<Act> {
    let cls = run.class;
    if !victory {
        cv.fill(0, 0, 960, 540, [20, 30, 50, 70]);
    }
    ui::motes(cv, ui.t, Rect::new(0, 100, 960, 400), if victory { 50 } else { 12 }, cls, if victory { 1.0 } else { 0.4 });
    let plate_name = match (cls, victory) {
        (Class::Foundry, true) => "foundry/end_plate_win",
        (Class::Foundry, false) => "foundry/end_plate_lose",
        (Class::Swarm, true) => "swarm/end_plate_win",
        (Class::Swarm, false) => "swarm/end_plate_lose",
    };
    if let Some(p) = a.ui.get(plate_name) {
        cv.blit(&p.img, 480 - p.img.w / 2, 70, false, 1.0);
        let title = if victory { t("end.win") } else { t("end.lose") };
        let c = if victory { (ACID, [70, 150, 50]) } else { ([190, 192, 200], [70, 72, 84]) };
        let c = if victory && cls == Class::Foundry { (GOLD, [140, 90, 40]) } else { c };
        heading(cv, a, &title, 480, 70 + p.img.h / 2 - 14, 24, c, Align::Center);
    }
    let panel = Rect::new(250, 184, 460, 230);
    plate(ui, cv, a, cls, panel);
    let c = ci(cls);
    let rows = [
        (t("end.won"), run.stats.won.to_string()),
        (t("end.kills"), run.stats.kills.to_string()),
        (format!("{} ({})", t("end.earned"), t(&format!("cur.{c}"))), run.stats.earned.to_string()),
        (t("end.lost"), run.stats.lost.to_string()),
    ];
    for (i, (k, v)) in rows.iter().enumerate() {
        let y = panel.y + 26 + i as i32 * 26;
        text(cv, a, k, panel.x + 30, y, MUTED, Align::Left);
        a.fonts["title16"].draw(cv, v, panel.x + panel.w - 30, y, GOLD, Some(EDGE), Align::Right, 1.0);
    }
    text(cv, a, &t("end.artifacts"), panel.x + 30, panel.y + 140, MUTED, Align::Left);
    for (i, art) in run.artifacts.iter().enumerate() {
        artifact_icon(ui, cv, a, *art, panel.x + 150 + i as i32 * 36, panel.y + 132, 2);
    }
    army_strip(cv, a, run, panel.x + 30, panel.y + 214, panel.w - 60);
    bottom(ui, cv, a, cls);
    let mut act = None;
    if ui.minor(cv, a, cls, "menu", 20, 482, &t("end.menu"), true) {
        act = Some(Act::ToMenu);
    }
    if ui.action(cv, a, cls, "again", 652, 478, &t("end.again"), true) || ui.key(Key::Enter) {
        act = Some(Act::NewRun);
    }
    act
}

// ---------------------------------------------------------------- the overlays

fn pause(ui: &mut Ui, cv: &mut Image, a: &Assets, cls: Class, run: Option<&Run>, battle: bool) -> Option<Act> {
    let r = Rect::new(330, 70, 300, 400);
    plate(ui, cv, a, cls, r);
    heading(cv, a, &t("pause.title"), 480, r.y + 18, 24, cols(cls), Align::Center);
    cv.fill(r.x + 16, r.y + 50, r.w - 32, 1, [180, 140, 70, 255]);
    if let Some(run) = run {
        let c = ci(cls);
        let line = tf("pause.line", &[("n", &run.next_fight().min(FIGHTS)), ("all", &FIGHTS), ("cur", &t(&format!("cur.{c}"))), ("m", &run.money)]);
        text(cv, a, &line, 480, r.y + 62, INK, Align::Center);
    }
    let mut act = None;
    let x = r.x + 26;
    match cls {
        Class::Foundry => {
            if ui.lever(cv, a, "resume", x - 6, r.y + 96, (200, 44), &t("pause.resume"), true) {
                act = Some(Act::Resume);
            }
        }
        Class::Swarm => {
            if ui.chitin(cv, a, "resume", Rect::new(x, r.y + 92, r.w - 52, 50), &t("pause.resume"), "acid", true, true) {
                act = Some(Act::Resume);
            }
        }
    }
    let items: [(&str, &str, Act); 5] = [
        ("pause.settings", "steel", Act::Settings),
        ("pause.army", "steel", Act::Army),
        ("pause.surrender", "rust", Act::Surrender),
        ("pause.menu", "steel", Act::ToMenu),
        ("pause.quit", "dull", Act::Quit),
    ];
    let mut y = r.y + 160;
    for (k, kind, a2) in items {
        let on = run.is_some() || !matches!(a2, Act::Surrender | Act::Army);
        let hit = match cls {
            Class::Foundry => ui.tag(cv, a, k, x + 10, y, &t(k), if kind == "dull" { "steel" } else { kind }, on),
            Class::Swarm => ui.chitin(cv, a, k, Rect::new(x + 10, y + 2, r.w - 72, 36), &t(k), if kind == "rust" { "blood" } else { "chitin" }, on, false),
        };
        if hit {
            act = Some(a2);
        }
        y += 42;
    }
    let _ = battle;
    text(cv, a, &t("pause.esc"), 480, r.y + r.h - 28, PALE, Align::Center);
    act
}

fn settings(ui: &mut Ui, cv: &mut Image, a: &Assets, cls: Class, s: &crate::game::Settings) -> Option<Act> {
    let r = Rect::new(230, 80, 500, 380);
    plate(ui, cv, a, cls, r);
    heading(cv, a, &t("settings.title"), 480, r.y + 18, 24, cols(cls), Align::Center);
    let mut act = None;
    let lx = r.x + 36;
    let cx = r.x + 300;
    let mut y = r.y + 70;
    // the volume: ten notches, arrows either side
    text(cv, a, &t("settings.volume"), lx, y + 2, INK, Align::Left);
    if arrow(ui, cv, a, "vol-", cx - 30, y, true) {
        act = Some(Act::Volume(-1));
    }
    for i in 0..10 {
        let on = (i as u8) < s.volume;
        let c = if !on {
            [52, 44, 60, 255]
        } else if cls == Class::Foundry {
            [240, 170, 70, 255]
        } else {
            [150, 230, 70, 255]
        };
        cv.fill(cx + i * 12, y + 3, 9, 14, [14, 10, 18, 255]);
        cv.fill(cx + i * 12 + 1, y + 4, 7, 12, c);
    }
    if arrow(ui, cv, a, "vol+", cx + 124, y, false) {
        act = Some(Act::Volume(1));
    }
    y += 52;
    let rows: [(&str, String, Act); 4] = [
        ("settings.screen", if s.fullscreen { t("settings.full") } else { t("settings.window") }, Act::Fullscreen),
        ("settings.camera", t(&format!("cam.{}", s.cam_level())), Act::Camera),
        ("settings.scale", if s.ui_scale == 0 { t("settings.auto") } else { format!("×{}", s.ui_scale) }, Act::UiScale),
        ("settings.speed", format!("×{}", s.speed), Act::Speed),
    ];
    for (i, (k, v, a2)) in rows.into_iter().enumerate() {
        text(cv, a, &t(k), lx, y + 2, INK, Align::Left);
        let row = Rect::new(cx - 30, y - 4, 174, 28);
        let (over, kk) = ui.hot(&format!("set{i}"), row);
        cell(ui, cv, a, cls, row, if over { "hover" } else { "normal" });
        if kk > 0.01 {
            cv.glow(row.cx() as f32, row.cy() as f32, 80.0, [255, 200, 120], 0.06 * kk);
        }
        text(cv, a, &v, row.cx(), y + 2, GOLD, Align::Center);
        if ui.clicked(row) {
            ui.sound("toggle");
            act = Some(a2);
        }
        y += 46;
    }
    let done = match cls {
        Class::Foundry => ui.tag(cv, a, "done", r.cx() - 60, r.y + r.h - 62, &t("settings.done"), "brass", true),
        Class::Swarm => ui.chitin(cv, a, "done", Rect::new(r.cx() - 90, r.y + r.h - 62, 180, 42), &t("settings.done"), "acid", true, false),
    };
    if done {
        act = Some(Act::CloseOverlay);
    }
    act
}

fn arrow(ui: &mut Ui, cv: &mut Image, a: &Assets, id: &str, x: i32, y: i32, left: bool) -> bool {
    let r = Rect::new(x, y, 20, 20);
    let (_, k) = ui.hot(id, r);
    ui.put(cv, a, if left { "foundry/arrow_left" } else { "foundry/arrow_right" }, x, y, 1.0);
    if k > 0.01 {
        cv.glow((x + 10) as f32, (y + 10) as f32, 14.0, [255, 220, 160], 0.25 * k);
    }
    let hit = ui.clicked(r);
    if hit {
        ui.sound("click");
    }
    hit
}

// ---------------------------------------------------------------- the army: every body, its full sheet

/// A damage type's word and glyph.
fn dmg_word(d: Dmg) -> (String, &'static str) {
    match d {
        Dmg::Pierce => (t("dmg.pierce"), "glyph/dmg:кол"),
        Dmg::Slash => (t("dmg.slash"), "glyph/dmg:руб"),
        Dmg::Blunt => (t("dmg.blunt"), "glyph/dmg:дроб"),
        Dmg::Fire => (t("dmg.fire"), "glyph/dmg:огонь"),
        Dmg::Cold => (t("dmg.cold"), "glyph/dmg:холод"),
        Dmg::Shock => (t("dmg.shock"), "glyph/dmg:молния"),
        Dmg::Poison => (t("dmg.poison"), "glyph/dmg:яд"),
        Dmg::Acid => (t("dmg.acid"), "glyph/dmg:кисл"),
    }
}

/// An armor type's word.
fn armor_word(a: sim::model::ArmorType) -> String {
    use sim::model::ArmorType as A;
    t(match a {
        A::None => "at.none",
        A::Soft => "at.soft",
        A::Leather => "at.leather",
        A::Chain => "at.chain",
        A::Plate => "at.plate",
        A::Cast => "at.cast",
        A::Chitin => "at.chitin",
        A::HeavyChitin => "at.heavychitin",
        A::Bone => "at.bone",
        A::Wood => "at.wood",
        A::Stone => "at.stone",
        A::Iron => "at.iron",
        A::Flame => "at.flame",
    })
}

/// «+2», «−1» or nothing: a blow's bonus as the sheet writes it.
fn plus(b: i32) -> String {
    match b {
        0 => String::new(),
        b if b > 0 => format!("+{b}"),
        b => format!("-{}", -b),
    }
}

/// A trait's name and what it does, its numbers in.
pub fn trait_words(tr: &sim::model::Trait) -> (String, String) {
    use sim::model::Trait as T;
    let n = |k: &str, l: &str| (t(k), t(l));
    match *tr {
        T::Zaslon => n("tr.zaslon", "tr.zaslon.l"),
        T::Probivnoy => n("tr.probivnoy", "tr.probivnoy.l"),
        T::Caster => n("tr.caster", "tr.caster.l"),
        T::Pitanie => n("tr.pitanie", "tr.pitanie.l"),
        T::Zamykanie => n("tr.zamykanie", "tr.zamykanie.l"),
        T::ZharGorna => n("tr.zhar", "tr.zhar.l"),
        T::Navodka => n("tr.navodka", "tr.navodka.l"),
        T::Naladka => n("tr.naladka", "tr.naladka.l"),
        T::NoAttack => n("tr.noattack", "tr.noattack.l"),
        T::FireResist75 => n("tr.fireresist", "tr.fireresist.l"),
        T::Mindless => n("tr.mindless", "tr.mindless.l"),
        T::PoisonImmune => n("tr.poisonimmune", "tr.poisonimmune.l"),
        T::Unstoppable => n("tr.unstoppable", "tr.unstoppable.l"),
        T::Fear { die, radius } => (t("tr.fear"), tf("tr.fear.l", &[("d", &die), ("r", &radius)])),
        T::Leader => n("tr.leader", "tr.leader.l"),
        T::Staya => n("tr.staya", "tr.staya.l"),
        T::Devour => n("tr.devour", "tr.devour.l"),
        T::Stroy => n("tr.stroy", "tr.stroy.l"),
        T::Flyer => n("tr.flyer", "tr.flyer.l"),
        T::Venom { die } => (t("tr.venom"), tf("tr.venom.l", &[("d", &die)])),
        T::BurstAcid { die } => (t("tr.burstacid"), tf("tr.burstacid.l", &[("d", &die)])),
        T::Charge => n("tr.charge", "tr.charge.l"),
        T::Thorns { die } => (t("tr.thorns"), tf("tr.thorns.l", &[("d", &die)])),
        T::CurlUp => n("tr.curlup", "tr.curlup.l"),
        T::Leap => n("tr.leap", "tr.leap.l"),
        T::TwinBlades => n("tr.twinblades", "tr.twinblades.l"),
        T::Glow => n("tr.glow", "tr.glow.l"),
        T::HiveMind => n("tr.hivemind", "tr.hivemind.l"),
        T::Grows => n("tr.grows", "tr.grows.l"),
        T::Infects => n("tr.infects", "tr.infects.l"),
        T::Changeling => n("tr.changeling", "tr.changeling.l"),
        T::Viviparous => n("tr.viviparous", "tr.viviparous.l"),
        T::Spitter => n("tr.spitter", "tr.spitter.l"),
    }
}

/// What an ability does, its numbers in.
pub fn ability_line(ab: &Ability) -> String {
    let hit = |die: u32, bonus: i32| format!("1–{die}{}", plus(bonus));
    match *ab {
        Ability::Volley { every, die, bonus, dmg } => tf("ab.volley.l", &[("e", &every), ("h", &hit(die, bonus)), ("t", &dmg_word(dmg).0)]),
        Ability::Repair { every, amount } => tf("ab.repair.l", &[("e", &every), ("n", &amount)]),
        Ability::Bolt { every, die, bonus, dmg, range } => tf("ab.bolt.l", &[("e", &every), ("h", &hit(die, bonus)), ("t", &dmg_word(dmg).0), ("r", &range)]),
        Ability::Flail => t("ab.flail.l"),
        Ability::Plates(n) => tf("ab.plates.l", &[("n", &n)]),
        Ability::PointBlank => t("ab.pointblank.l"),
        Ability::Intercept => t("ab.intercept.l"),
        Ability::Flash { every } => tf("ab.flash.l", &[("e", &every)]),
        Ability::Spit { every, die } => tf("ab.spit.l", &[("e", &every), ("d", &die)]),
        Ability::Brood { every, n } => tf("ab.brood.l", &[("e", &every), ("n", &n)]),
        Ability::Mark { every } => tf("ab.mark.l", &[("e", &every)]),
        Ability::Overload { every } => tf("ab.overload.l", &[("e", &every)]),
        Ability::Fireball { every, die, bonus, range } => tf("ab.fireball.l", &[("e", &every), ("h", &hit(die, bonus)), ("r", &range)]),
        Ability::Quake { every, die, bonus, .. } => tf("ab.quake.l", &[("e", &every), ("h", &hit(die, bonus))]),
        Ability::Augment => t("ab.augment.l"),
        Ability::Tinker { every } => tf("ab.tinker.l", &[("e", &every)]),
    }
}

/// The army's rows: a golem (or the leader) a row; the swarm a row a kind (how many of it) — broken ones apart.
pub fn army_rows(run: &Run) -> Vec<(usize, usize)> {
    let mut gs: Vec<(usize, usize)> = vec![];
    for (i, m) in run.army.iter().enumerate() {
        if run.class == Class::Swarm && !run.is_leader(m) {
            if let Some(g) = gs.iter_mut().find(|(j, _)| run.army[*j].t.name == m.t.name && run.army[*j].broken == m.broken && !run.is_leader(&run.army[*j])) {
                g.1 += 1;
                continue;
            }
        }
        gs.push((i, 1));
    }
    gs
}

/// How many rows of the army's list show at once.
pub const ARMY_ROWS: usize = 9;

/// The army, as in the strategy games of old: every body down the left (the wheel scrolls), the one picked —
/// its whole sheet on the right: how it goes into battle, its numbers, what it does, what it carries.
#[allow(clippy::too_many_arguments)]
fn army(ui: &mut Ui, cv: &mut Image, a: &Assets, run: &Run, sel: usize, top: usize, sheet_top: usize) -> Option<Act> {
    let cls = run.class;
    let r = Rect::new(24, 24, 912, 492);
    plate(ui, cv, a, cls, r);
    heading(cv, a, &t("army.title"), 480, r.y + 10, 24, cols(cls), Align::Center);
    let mut act = None;
    let rows = army_rows(run);
    let sel = sel.min(rows.len().saturating_sub(1));
    let font = &a.fonts["text16"];
    // the list
    let list = Rect::new(r.x + 18, r.y + 54, 286, ARMY_ROWS as i32 * 40);
    let (over_list, _) = ui.hot("armylist", list);
    if over_list && ui.wheel != 0 {
        act = Some(Act::ArmyScroll(-ui.wheel));
    }
    let top = top.min(rows.len().saturating_sub(ARMY_ROWS));
    for (k, &(i, n)) in rows.iter().enumerate().skip(top).take(ARMY_ROWS) {
        let m = &run.army[i];
        let row = Rect::new(list.x, list.y + (k - top) as i32 * 40, list.w, 36);
        let (over, kk) = ui.hot(&format!("arow{k}"), row);
        let picked = k == sel;
        cell(ui, cv, a, cls, row, if picked { "hover" } else { "normal" });
        if kk > 0.01 || picked {
            cv.glow(row.cx() as f32, row.cy() as f32, 120.0, if cls == Class::Foundry { [255, 190, 110] } else { [150, 230, 70] }, if picked { 0.12 } else { 0.06 * kk });
        }
        let mut pic = Image::clear(44, 34);
        small(&mut pic, a, &m.t, 22, 32, false, m.broken);
        cv.blit(&pic, row.x + 4, row.y + 1, false, 1.0);
        let name = if run.is_leader(m) { format!("{} · {}", m.t.name, t("sheet.leader")) } else { m.t.name.to_string() };
        let col = if m.broken { MUTED } else if picked { GOLD } else { INK };
        let w = row.w - 110;
        let shown = font.wrap(&name, w).into_iter().next().unwrap_or_default();
        font.draw(cv, &shown, row.x + 52, row.y + 10, col, Some(EDGE), Align::Left, 1.0);
        let right = if m.broken { t("card.broken") } else if n > 1 { tf("card.count", &[("n", &n)]) } else { String::new() };
        font.draw(cv, &right, row.x + row.w - 8, row.y + 10, if m.broken { RED } else { GOLD }, Some(EDGE), Align::Right, 1.0);
        if over && ui.clicked(row) {
            act = Some(Act::ArmySel(k));
        }
    }
    // where the list stands, and the way along it
    if rows.len() > ARMY_ROWS {
        let bar = Rect::new(list.x + list.w + 6, list.y, 6, list.h);
        cv.fill(bar.x, bar.y, bar.w, bar.h, [20, 16, 22, 200]);
        let h = (bar.h as usize * ARMY_ROWS / rows.len()).max(16) as i32;
        let y = bar.y + ((bar.h - h) as usize * top / (rows.len() - ARMY_ROWS)) as i32;
        cv.fill(bar.x, y, bar.w, h, [200, 170, 110, 255]);
        text(cv, a, &tf("army.count", &[("n", &run.army.len())]), list.x, list.y + list.h + 4, MUTED, Align::Left);
    }
    // the artifacts under the list
    let ay = r.y + r.h - 44;
    text(cv, a, &t("army.artifacts"), list.x, ay + 8, MUTED, Align::Left);
    if run.artifacts.is_empty() {
        text(cv, a, &t("army.none"), list.x + 120, ay + 8, PALE, Align::Left);
    }
    for (i, art) in run.artifacts.iter().enumerate() {
        let (x, y) = (list.x + 120 + i as i32 * 36, ay);
        artifact_icon(ui, cv, a, *art, x, y, 2);
        if ui.hot(&format!("aa{i}"), Rect::new(x, y, 32, 32)).0 {
            ui.tooltip(artifact_tip(*art));
        }
    }
    // the sheet of the one picked; the wheel over it goes down its lines
    if let Some(&(i, n)) = rows.get(sel) {
        let sr = Rect::new(r.x + 330, r.y + 50, r.w - 348, r.h - 104);
        sheet(ui, cv, a, run, &run.army[i], n, sr, sheet_top);
        if ui.hot("armysheet", sr).0 && ui.wheel != 0 {
            act = Some(Act::SheetScroll(-ui.wheel));
        }
    }
    if ui.minor(cv, a, cls, "close", r.x + r.w - 190, r.y + r.h - 44, &t("army.close"), true) {
        act = Some(Act::CloseOverlay);
    }
    act
}

/// The lines of a body's sheet: its abilities, its traits, its modules (with their levels) or its breed's
/// mutations — (name, what it does, its icon).
pub fn sheet_lines(run: &Run, m: &sim::run::Member) -> Vec<(String, String, Option<String>)> {
    let b = run.body(m);
    let mut lines = vec![];
    for ab in &b.abilities {
        lines.push((ability_name(ab), ability_line(ab), None));
    }
    for tr in &b.traits {
        let (nm, l) = trait_words(tr);
        lines.push((nm, l, None));
    }
    if run.class == Class::Foundry {
        for (j, k) in m.mods.iter().enumerate() {
            let lv = t(&format!("lvl.{}", m.level(j)));
            lines.push((format!("{} {lv}", t(&format!("find.{k}"))), t(&format!("find.{k}.l")), Some(format!("module/{k}"))));
        }
    } else {
        let f = form_of(&m.t);
        for (_, k) in run.breeds.iter().filter(|(x, _)| x == f) {
            lines.push((t(&format!("find.{k}")), t(&format!("find.{k}.l")), Some(format!("swarm/{k}"))));
        }
    }
    lines
}

/// One body's whole sheet: its picture, name and kind; its numbers as it goes into battle (modules, mutations and
/// artifacts in); what it does; what it carries.
#[allow(clippy::too_many_arguments)]
fn sheet(ui: &mut Ui, cv: &mut Image, a: &Assets, run: &Run, m: &sim::run::Member, n: usize, r: Rect, skip: usize) {
    let cls = run.class;
    let font = &a.fonts["text16"];
    let b = run.body(m);
    cv.fill(r.x, r.y, r.w, r.h, [10, 8, 12, 110]);
    // the picture, cut to its frame
    let pr = Rect::new(r.x + 8, r.y + 8, 132, 132);
    cv.fill(pr.x, pr.y, pr.w, pr.h, [16, 12, 18, 255]);
    cv.shadow(pr.cx() as f32, (pr.y + pr.h - 14) as f32, 50.0, 8.0);
    let mut pic = Image::clear(pr.w, pr.h);
    portrait(ui, &mut pic, a, &b, pr.w / 2, pr.h - 12, if m.broken { 0.5 } else { 1.0 }, false);
    cv.blit(&pic, pr.x, pr.y, false, 1.0);
    // name and kind
    let title = if cls == Class::Foundry { [255, 214, 150] } else { ACID2 };
    a.fonts["title16"].draw(cv, &b.name, r.x + 152, r.y + 12, title, Some(EDGE), Align::Left, 1.0);
    let kind = if run.is_leader(m) {
        t("sheet.leader")
    } else if m.t.golem {
        t("sheet.golem")
    } else {
        t("sheet.creature")
    };
    let mut sub = format!("{kind} · {}", armor_word(b.armor_type));
    if n > 1 {
        sub = format!("{sub} · {}", tf("card.count", &[("n", &n)]));
    }
    if m.broken {
        sub = format!("{sub} · {}", t("card.broken"));
    }
    font.draw(cv, &sub, r.x + 152, r.y + 34, if m.broken { RED } else { MUTED }, Some(EDGE), Align::Left, 1.0);
    // the numbers: a glyph, a word, the number
    let (dw, dg) = dmg_word(b.dmg);
    let blow = if b.die == 0 || b.has(sim::model::Trait::NoAttack) { t("card.nohit") } else { format!("1–{}{} · {dw}", b.die, plus(b.bonus)) };
    let morale = if b.has(sim::model::Trait::Mindless) { "—".to_string() } else { b.morale.to_string() };
    let stats: [(&str, String, String); 8] = [
        ("glyph/здоровье", t("sheet.hp"), b.hp.to_string()),
        ("glyph/броня", t("sheet.armor"), b.armor.to_string()),
        (dg, t("sheet.hit"), blow),
        ("glyph/дальность", t("sheet.range"), b.range.to_string()),
        ("glyph/скорость", t("sheet.speed"), b.speed.to_string()),
        ("glyph/инициатива", t("sheet.init"), b.init.to_string()),
        ("glyph/дух", t("sheet.morale"), morale),
        ("glyph/размер", t("sheet.size"), b.size.to_string()),
    ];
    for (k, (g, word, v)) in stats.iter().enumerate() {
        let (col, row) = ((k % 2) as i32, (k / 2) as i32);
        let x = r.x + 152 + col * 196;
        let y = r.y + 58 + row * 22;
        ui.icon(cv, a, g, x, y, 1, 1.0);
        font.draw(cv, word, x + 22, y, MUTED, Some(EDGE), Align::Left, 1.0);
        font.draw(cv, v, x + 190, y, INK, Some(EDGE), Align::Right, 1.0);
    }
    // what it does and what it carries: a line each, the name gold, the rest after it
    let lines = sheet_lines(run, m);
    let mut y = r.y + 152;
    font.draw(cv, &t("sheet.does"), r.x + 10, y, cols(cls).0, Some(EDGE), Align::Left, 1.0);
    y += 22;
    if lines.is_empty() {
        font.draw(cv, &t("sheet.nothing"), r.x + 10, y, PALE, Some(EDGE), Align::Left, 1.0);
    }
    let bottom = r.y + r.h - 6;
    let skip = skip.min(lines.len().saturating_sub(1));
    if skip > 0 {
        font.draw(cv, &tf("sheet.above", &[("n", &skip)]), r.x + r.w - 10, y - 22, MUTED, Some(EDGE), Align::Right, 1.0);
    }
    for (k, (nm, l, icon)) in lines.iter().enumerate().skip(skip) {
        if y + 18 > bottom {
            font.draw(cv, &tf("sheet.below", &[("n", &(lines.len() - k))]), r.x + r.w - 10, bottom - 16, MUTED, Some(EDGE), Align::Right, 1.0);
            break;
        }
        let mut x = r.x + 10;
        if let Some(ic) = icon {
            ui.icon(cv, a, ic, x, y, 1, 1.0);
            x += 22;
        }
        let nw = font.width(nm);
        font.draw(cv, nm, x, y, GOLD, Some(EDGE), Align::Left, 1.0);
        let rest = r.x + r.w - 10 - (x + nw + 12);
        let parts = font.wrap(l, rest.max(80));
        for (p, part) in parts.iter().enumerate() {
            if y + 18 > bottom {
                break;
            }
            font.draw(cv, part, x + nw + 12, y, INK, Some(EDGE), Align::Left, 1.0);
            if p + 1 < parts.len() {
                y += 18;
            }
        }
        y += 20;
    }
}

fn about(ui: &mut Ui, cv: &mut Image, a: &Assets, cls: Class) -> Option<Act> {
    let r = Rect::new(170, 70, 620, 400);
    plate(ui, cv, a, cls, r);
    heading(cv, a, &t("about.title"), 480, r.y + 18, 24, cols(cls), Align::Center);
    para(cv, a, &t("about.body"), r.x + 34, r.y + 66, r.w - 68, INK);
    if ui.minor(cv, a, cls, "back", r.cx() - 60, r.y + r.h - 60, &t("about.back"), true) {
        Some(Act::CloseOverlay)
    } else {
        None
    }
}
