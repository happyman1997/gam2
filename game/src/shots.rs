//! Every screen to a PNG, no window needed (`--screens dir`): a run of each class set up and walked to each screen,
//! the mouse put on one of its controls so its hover shows, the picture put together as the window would at
//! 1920×1080. For a look at the screens from the cloud.

use crate::camera::{self, Frame};
use crate::game::{CampStage, From, Game, Overlay, Screen, Targeting};
use crate::gfx::Image;
use crate::render::{H, W};
use crate::Demo;
use sim::run::{Artifact, Class, Kind, Reward, Run};
use std::path::Path;

fn snap(g: &mut Game, dir: &str, name: &str, mouse: (i32, i32)) {
    snap_n(g, dir, name, mouse, 12)
}

fn snap_n(g: &mut Game, dir: &str, name: &str, mouse: (i32, i32), frames: usize) {
    g.ui.mx = mouse.0;
    g.ui.my = mouse.1;
    let mut field = Image::new(W, H);
    let mut hud = Image::clear(W, H);
    // a few frames, so a hover has eased in and the fade is gone
    for _ in 0..frames {
        field = Image::new(W, H);
        hud = Image::clear(W, H);
        g.step_fade(0.05);
        g.draw_bg(&mut field);
        g.draw_ui(&mut hud);
        g.ui.end(0.05);
    }
    let fr = Frame::fit(1920, 1080);
    let mut buf = vec![0u8; 1920 * 1080 * 3];
    camera::compose(&field, &hud, camera::whole(&fr), g.light(), &mut buf, &fr, 3);
    let mut img = Image::new(1920, 1080);
    for (i, p) in img.px.iter_mut().enumerate() {
        *p = [buf[i * 3], buf[i * 3 + 1], buf[i * 3 + 2], 255];
    }
    img.save(&Path::new(dir).join(format!("{name}.png"))).expect("save");
    println!("{dir}/{name}.png");
}

fn set(g: &mut Game, s: Screen) {
    g.screen = s;
    g.overlays.clear();
    g.next = None;
}

pub fn run(demo: Demo, dir: &str) {
    std::fs::create_dir_all(dir).expect("dir");
    let mut g = Game::new(demo);
    set(&mut g, Screen::Menu);
    snap(&mut g, dir, "01_menu", (150, 484));
    set(&mut g, Screen::Class);
    snap(&mut g, dir, "02_class", (240, 200));
    set(&mut g, Screen::Leaders { class: Class::Foundry, chosen: 1 });
    snap(&mut g, dir, "03_leaders_foundry", (600, 300));
    set(&mut g, Screen::Leaders { class: Class::Swarm, chosen: 2 });
    snap(&mut g, dir, "04_leaders_swarm", (300, 300));
    for (cls, leader, tag) in [(Class::Foundry, 1, "f"), (Class::Swarm, 0, "s")] {
        let mut run = Run::new(cls, leader, 21);
        run.artifacts = vec![Artifact::Znamya, Artifact::Grani];
        // something already put on: a module on the first golem that takes one, a mutation on the first breed
        for _ in 0..3 {
            if let Some(o) = run.find(3, false).into_iter().find(|o| o.find != sim::run::Find::Units) {
                let to = run.targets(&o).into_iter().next();
                run.take_find(&o, to.as_ref());
            }
        }
        run.money = 37;
        run.fight = 3;
        run.fork();
        // a fork with a stop on it
        let mut guard = 0;
        while !run.path.iter().any(|n| !n.kind.is_battle()) && guard < 20 {
            run.stopped = false;
            run.fork();
            guard += 1;
        }
        g.run = Some(run.clone());
        set(&mut g, Screen::Fork);
        snap(&mut g, dir, &format!("10_{tag}_fork"), (480, 300));
        // a battle's spoils, a find open
        let mut r2 = run.clone();
        let node = r2.path.iter().find(|n| n.kind.is_battle()).cloned().unwrap();
        let mut elite = node.clone();
        elite.kind = Kind::Elite;
        let rewards = r2.after_battle(&elite, &sim::run::BattleResult { won: true, dead: vec![0], kills: 9 });
        g.run = Some(r2.clone());
        let list: Vec<(Reward, bool)> = rewards.into_iter().map(|r| (r, false)).collect();
        let find = list.iter().position(|(r, _)| matches!(r, Reward::Find(_))).unwrap_or(0);
        set(&mut g, Screen::Rewards { list: list.clone(), pick: None });
        snap(&mut g, dir, &format!("11_{tag}_rewards"), (480, 200));
        set(&mut g, Screen::Rewards { list: list.clone(), pick: Some(find) });
        snap(&mut g, dir, &format!("12_{tag}_find"), (480, 280));
        // a module or a mutation of the find being given its place
        if let Some((Reward::Find(offers), _)) = list.get(find) {
            if let Some(o) = offers.iter().find(|o| o.find != sim::run::Find::Units) {
                set(&mut g, Screen::Rewards { list: list.clone(), pick: None });
                g.targeting = Some(Targeting { offer: o.clone(), from: From::Reward(find) });
                g.ui.opened = g.ui.t;
                snap(&mut g, dir, &format!("12b_{tag}_target"), (180, 200));
                g.targeting = None;
            }
        }
        // a boss beaten: the leader's growth among the spoils, its two cards open
        let mut r5 = run.clone();
        r5.fight = 4;
        let mut boss = node.clone();
        boss.kind = Kind::Boss;
        let spoils = r5.after_battle(&boss, &sim::run::BattleResult { won: true, dead: vec![], kills: 30 });
        if let Some(gi) = spoils.iter().position(|r| matches!(r, Reward::Growth(_))) {
            g.run = Some(r5);
            let list: Vec<(Reward, bool)> = spoils.into_iter().map(|r| (r, false)).collect();
            set(&mut g, Screen::Rewards { list: list.clone(), pick: None });
            snap(&mut g, dir, &format!("11b_{tag}_boss_rewards"), (480, 200));
            set(&mut g, Screen::Rewards { list, pick: Some(gi) });
            g.ui.opened = g.ui.t;
            snap(&mut g, dir, &format!("12c_{tag}_growth"), (340, 300));
        }
        // the trader
        let mut r3 = run.clone();
        let shop = r3.shop();
        g.run = Some(r3);
        set(&mut g, Screen::Shop(shop));
        snap(&mut g, dir, &format!("13_{tag}_shop"), (370, 200));
        // an event of the class
        let ev = sim::run::EVENTS.iter().position(|e| e.1 == Some(cls)).unwrap_or(0);
        g.run = Some(run.clone());
        set(&mut g, Screen::Event { id: ev, done: None });
        snap(&mut g, dir, &format!("14_{tag}_event"), (600, 330));
        set(&mut g, Screen::Event { id: 4, done: None });
        snap(&mut g, dir, &format!("15_{tag}_event_shadow"), (600, 400));
        // the camp
        set(&mut g, Screen::Camp { stage: CampStage::Choose, said: String::new() });
        snap(&mut g, dir, &format!("16_{tag}_camp"), (660, 250));
        set(&mut g, Screen::Camp { stage: CampStage::Pick, said: String::new() });
        snap(&mut g, dir, &format!("17_{tag}_camp_pick"), (110, 170));
        // the end
        let mut r4 = run.clone();
        r4.stats.won = 15;
        r4.stats.kills = 214;
        r4.stats.earned = 188;
        r4.stats.lost = 9;
        g.run = Some(r4);
        set(&mut g, Screen::End { victory: tag == "f" });
        snap(&mut g, dir, &format!("18_{tag}_end"), (700, 500));
        // the overlays over the fork
        g.run = Some(run.clone());
        set(&mut g, Screen::Fork);
        g.overlays.push(Overlay::Pause);
        snap(&mut g, dir, &format!("20_{tag}_pause"), (420, 290));
        g.overlays.push(Overlay::Settings);
        snap(&mut g, dir, &format!("21_{tag}_settings"), (600, 200));
        g.overlays.clear();
        g.overlays.push(Overlay::Army);
        snap(&mut g, dir, &format!("22_{tag}_army"), (200, 200));
    }
    set(&mut g, Screen::Menu);
    g.overlays.push(Overlay::About);
    snap(&mut g, dir, "05_about", (0, 0));
    // the shutters half shut between two screens, and the fork's cards coming up
    let run = Run::new(Class::Foundry, 0, 3);
    g.run = Some(run);
    set(&mut g, Screen::Fork);
    snap(&mut g, dir, "30_shutters_from", (0, 0));
    let shop = g.run.as_mut().unwrap().shop();
    g.go(Screen::Shop(shop));
    snap_n(&mut g, dir, "31_shutters", (0, 0), 3);
    g.next = None;
    g.fade = 0.0;
    g.ui.entered = g.ui.t;
    snap_n(&mut g, dir, "32_rising", (0, 0), 2);
}
