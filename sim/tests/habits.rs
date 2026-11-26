//! Not numbers but habits (CONCEPT.md, «Повадки вместо цифр»): what used to be +armor, +health, +damage is now a way
//! of fighting — and each one changes the battle.

use sim::battle::{Battle, Event};
use sim::data::*;
use sim::model::{Template, Trait};

fn still(mut t: Template) -> Template {
    t.speed = 0;
    t
}

fn with(mut t: Template, x: Trait) -> Template {
    t.traits.push(x);
    t
}

/// Every habit, given to one side, changes how a battle goes (its log is not the same as without it).
#[test]
fn every_habit_does_something() {
    use Trait::*;
    // the Foundry's (on golems against a swarm) and the swarm's (on bugs against golems)
    let foundry = [
        TowerShield,
        Pierce,
        Sparks,
        Torch,
        Banner,
        Chalice,
        Crush,
        Bell,
        LoadedDice,
        Hourglass,
        Flare,
        ShedPlates,
        Chain,
        Whirl,
        Rubble,
        Lob,
        Shockwave,
        Regen,
    ];
    // (Отрыжка: its own test below — the Devourer seldom digests a whole meal in a battle of starts)
    let swarm_ = [Reach, Splash, Ricochet, Bulwark, Escort, Rally, MindWard, AcidBlood, PlagueBlood, Cocoon, Ambush];
    let golems = || {
        let mut a = start_zodchiy();
        a.extend([strazh(), mudrets(), orudie(), gorn(), otets_kolossa(), izobretatel(), manyak()]);
        a
    };
    let bugs = || {
        let mut b = army("start_matka");
        b.extend([pozhiratel(), razum(), kukushka()]);
        b.extend((0..6).map(|_| swarm(Caste::Soldier, Form::Beetle)));
        b.extend((0..6).map(|_| swarm(Caste::Worker, Form::Scorpion)));
        b.extend((0..12).map(|_| swarm(Caste::Worker, Form::Barrel)));
        b.extend((0..6).map(|_| swarm(Caste::Worker, Form::Spitter)));
        b.extend((0..6).map(|_| swarm(Caste::Soldier, Form::Isopod)));
        b
    };
    let log = |a: &[Template], b: &[Template], seed: u64| {
        let mut bt = Battle::new(seed).with_log();
        bt.add_armies(a, b);
        bt.run();
        format!("{:?}", bt.log.unwrap())
    };
    for x in foundry {
        let plain = golems();
        let given: Vec<Template> = plain.iter().cloned().map(|t| with(t, x)).collect();
        let changed = (0..8).any(|seed| log(&plain, &bugs(), seed) != log(&given, &bugs(), seed));
        assert!(changed, "{x:?} on the golems changed nothing");
    }
    for x in swarm_ {
        let plain = bugs();
        let given: Vec<Template> = plain.iter().cloned().map(|t| with(t, x)).collect();
        let changed = (0..8).any(|seed| log(&golems(), &plain, seed) != log(&golems(), &given, seed));
        assert!(changed, "{x:?} on the swarm changed nothing");
    }
}

#[test]
fn a_tower_shield_covers_the_one_behind_it() {
    let mut bt = Battle::new(1);
    let mut gun = still(orudie());
    gun.range = 30;
    bt.place(1, gun, 30, 10);
    let guard = bt.place(0, with(still(strazh()), Trait::TowerShield), 10, 9);
    let sage = bt.place(0, still(mudrets()), 8, 10);
    bt.units[guard].hp = 999;
    bt.units[sage].hp = 999;
    for _ in 0..4 {
        bt.step();
    }
    assert_eq!(bt.units[sage].hp, 999, "the Gun shot the Sage behind the tower shield");
    assert!(bt.units[guard].hp < 999, "the Gun shot no one");
}

#[test]
fn the_hourglass_turns_time_back_once() {
    let mut bt = Battle::new(2).with_log();
    // unstoppable: the crushing blow does not throw it out of reach
    let a = bt.place(1, with(with(still(soldat()), Trait::Hourglass), Trait::Unstoppable), 14, 10);
    let mut heavy = still(strazh());
    heavy.die = 80;
    heavy.dmg = sim::model::Dmg::Blunt;
    bt.place(0, heavy, 11, 9);
    bt.step();
    assert!(bt.units[a].alive, "the hourglass did not turn its time back");
    assert!(bt.log.as_ref().unwrap().iter().any(|e| matches!(e, Event::Rewind { .. })));
    bt.step();
    bt.step();
    assert!(!bt.units[a].alive, "it turned its time back twice");
}

#[test]
fn the_banner_rises_when_half_the_army_is_down() {
    let mut risen = false;
    for seed in 0..6 {
        let mut a = start_zodchiy();
        let lead = a.iter().position(|t| t.has(Trait::Leader)).unwrap();
        a[lead].traits.push(Trait::Banner);
        let mut bt = Battle::new(seed).with_log();
        bt.add_armies(&a, &army("start_matka"));
        bt.run();
        risen |= bt.log.unwrap().iter().any(|e| matches!(e, Event::Banner { .. }));
    }
    assert!(risen, "the banner never rose");
}

#[test]
fn the_bell_stuns_the_enemies_round_it() {
    let mut bt = Battle::new(3).with_log();
    let b = bt.place(0, with(still(izobretatel()), Trait::Bell), 10, 10);
    bt.units[b].hp = 999;
    for k in 0..3 {
        let a = bt.place(1, still(soldat()), 12, 9 + k);
        bt.units[a].hp = 999;
    }
    for _ in 0..4 {
        bt.step();
    }
    assert!(bt.log.as_ref().unwrap().iter().any(|e| matches!(e, Event::Bell { .. })), "the bell never rang");
}

#[test]
fn the_mother_is_shielded_by_her_own() {
    let mut bt = Battle::new(4);
    let m = bt.place(1, with(still(matka()), Trait::Escort), 20, 10);
    let guardling = bt.place(1, still(soldat()), 19, 13);
    bt.units[guardling].hp = 999;
    bt.units[guardling].t.hp = 999;
    bt.place(0, still(strazh()), 17, 10);
    let full = bt.units[m].hp;
    for _ in 0..3 {
        bt.step();
    }
    assert_eq!(bt.units[m].hp, full, "a blow got through to the Mother past her living shield");
    assert!(bt.units[guardling].hp < 999, "the body beside her took nothing");
}

#[test]
fn the_devourer_belches_acid_over_them() {
    let mut bt = Battle::new(5).with_log();
    let d = bt.place(1, with(still(pozhiratel()), Trait::Belch), 10, 10);
    bt.units[d].hp = 999;
    let mason = bt.place(0, still(kamenshchik()), 9, 10);
    bt.units[mason].hp = 999;
    // two cells off: out of his bite, in the belch's reach
    let g = bt.place(0, still(strazh()), 13, 12);
    bt.units[g].hp = 999;
    for _ in 0..4 {
        bt.step();
        if bt.units[mason].inside.is_some() {
            bt.units[mason].hp = 1; // as good as digested
            break;
        }
    }
    for _ in 0..2 {
        bt.step();
    }
    assert!(bt.log.as_ref().unwrap().iter().any(|e| matches!(e, Event::Hit { a, t, .. } if *a == d && *t == g)), "no belch reached the Guard");
}
