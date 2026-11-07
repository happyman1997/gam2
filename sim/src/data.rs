//! Draft numbers from docs/CONCEPT.md. Later this moves to data files.

use crate::model::{Ability, ArmorType, Dmg, Template, Trait};

fn golem(name: &'static str, size: u32, hp: i32, die: u32, bonus: i32, init: u32, armor: i32, speed: u32) -> Template {
    Template {
        name,
        size,
        hp,
        die,
        bonus,
        dmg: Dmg::Blunt,
        init,
        armor,
        morale: 99,
        speed,
        range: 1,
        armor_type: ArmorType::Cast,
        golem: true,
        traits: vec![Trait::FireResist75, Trait::Mindless, Trait::PoisonImmune],
        abilities: vec![],
    }
}

// ---------------------------------------------------------------- the Foundry: frames
pub fn strazh() -> Template {
    golem("Страж", 6, 140, 6, 4, 3, 6, 1).with_trait(Trait::Zaslon)
}

pub fn molot() -> Template {
    golem("Молот", 5, 90, 10, 10, 2, 4, 1).with_trait(Trait::Probivnoy)
}

pub fn gorn() -> Template {
    golem("Горн", 5, 100, 6, 2, 3, 5, 1).with_trait(Trait::ZharGorna)
}

pub fn orudie() -> Template {
    let mut t = golem("Орудие", 5, 70, 12, 4, 4, 3, 1).with_trait(Trait::Navodka);
    t.range = 3;
    t
}

pub fn mekhanik() -> Template {
    let mut t = golem("Механик", 4, 50, 0, 0, 0, 3, 2)
        .with_trait(Trait::Naladka)
        .with_trait(Trait::NoAttack);
    t.dmg = Dmg::Blunt;
    t
}

pub fn kamenshchik() -> Template {
    golem("Каменщик", 2, 14, 4, 0, 4, 2, 2)
}

// ---------------------------------------------------------------- the Foundry: leaders
pub fn otets_kolossa() -> Template {
    golem("Отец колосса", 7, 320, 12, 18, 1, 7, 1)
        .with_trait(Trait::Unstoppable)
        .with_trait(Trait::Fear { die: 9, radius: 3 })
}

fn human_leader(name: &'static str, size: u32, hp: i32, die: u32, bonus: i32, dmg: Dmg, init: u32, morale: u32, speed: u32) -> Template {
    Template {
        name,
        size,
        hp,
        die,
        bonus,
        dmg,
        init,
        armor: 1,
        morale,
        speed,
        range: 1,
        armor_type: ArmorType::Leather,
        golem: false,
        traits: vec![Trait::FireResist75],
        abilities: vec![],
    }
}

pub fn izobretatel() -> Template {
    human_leader("Изобретатель", 3, 20, 6, 0, Dmg::Shock, 7, 10, 2)
}

pub fn manyak() -> Template {
    human_leader("Маньяк", 4, 30, 8, 2, Dmg::Slash, 5, 12, 2).with_trait(Trait::Fear { die: 8, radius: 2 })
}

pub fn zodchiy() -> Template {
    let mut t = human_leader("Зодчий", 4, 25, 4, 1, Dmg::Blunt, 5, 9, 1);
    t.range = 2;
    t
}

// ---------------------------------------------------------------- modules
pub fn mortira() -> Ability {
    Ability::Volley { every: 3, die: 6, bonus: 7, dmg: Dmg::Blunt }
}

pub fn remont() -> Ability {
    Ability::Repair { every: 2, amount: 10 }
}

pub fn grozovaya_katushka() -> Ability {
    Ability::Bolt { every: 2, die: 6, bonus: 0, dmg: Dmg::Shock, range: 1 }
}

pub fn golova_katapulta() -> Ability {
    Ability::Bolt { every: 2, die: 6, bonus: 2, dmg: Dmg::Blunt, range: 3 }
}

// ---------------------------------------------------------------- the Swarm and others
fn creature(name: &'static str, size: u32, hp: i32, die: u32, bonus: i32, dmg: Dmg, init: u32, armor: i32, morale: u32, speed: u32, at: ArmorType) -> Template {
    Template {
        name,
        size,
        hp,
        die,
        bonus,
        dmg,
        init,
        armor,
        morale,
        speed,
        range: 1,
        armor_type: at,
        golem: false,
        traits: vec![],
        abilities: vec![],
    }
}

pub fn rabochaya() -> Template {
    creature("Рабочая", 1, 5, 4, 0, Dmg::Pierce, 8, 0, 6, 3, ArmorType::Chitin)
}

pub fn soldat() -> Template {
    creature("Солдат", 2, 14, 8, 0, Dmg::Slash, 6, 2, 9, 2, ArmorType::Chitin)
}

/// Not in the concept's number table yet: a probe for "the swarm's answer to metal".
pub fn zhuk() -> Template {
    creature("Жук-носорог", 2, 16, 8, 0, Dmg::Blunt, 4, 3, 9, 2, ArmorType::HeavyChitin)
}

/// Not in the concept's number table yet: an acid spitter, range 2.
pub fn kislotnik() -> Template {
    let mut t = creature("Кислотник", 1, 6, 4, 0, Dmg::Acid, 6, 0, 6, 2, ArmorType::Soft);
    t.range = 2;
    t
}

pub fn voin() -> Template {
    creature("Воин", 3, 12, 6, 1, Dmg::Pierce, 6, 2, 10, 2, ArmorType::Chain)
}

pub fn many(t: Template, n: usize) -> Vec<Template> {
    vec![t; n]
}

// ---------------------------------------------------------------- starting armies (only modules the sim knows)
/// Отец колосса: Броневые листы, Кистень (Магнит — not yet); Механик with Ремонт.
pub fn start_otets() -> Vec<Template> {
    vec![otets_kolossa().with(Ability::Plates(3)).with(Ability::Flail), mekhanik().with(remont())]
}

/// Изобретатель: small Молот (Гусеницы, Пружинный рывок — not yet), small Орудие with Мортира
/// and Грозовая катушка, small Механик with Ремонт (Отражатель — not yet).
pub fn start_izobretatel() -> Vec<Template> {
    vec![
        molot().smaller(),
        orudie().smaller().with(mortira()).with(grozovaya_katushka()),
        mekhanik().smaller().with(remont()),
        izobretatel(),
    ]
}

/// Маньяк: Молот (Ноги-пилы, Отбойник — not yet), Орудие with Голова-катапульта and Картечь.
pub fn start_manyak() -> Vec<Template> {
    vec![molot(), orudie().with(golova_katapulta()).with(Ability::PointBlank), manyak()]
}

/// Зодчий: Страж with Перехват (Щит-стена — not yet), Механик with Ремонт, two masons.
pub fn start_zodchiy() -> Vec<Template> {
    vec![strazh().with(Ability::Intercept), mekhanik().with(remont()), kamenshchik(), kamenshchik(), zodchiy()]
}

pub fn swarm_start() -> Vec<Template> {
    let mut v = many(rabochaya(), 20);
    v.extend(many(soldat(), 4));
    v
}

pub fn humans_squad() -> Vec<Template> {
    many(voin(), 8)
}

// ---------------------------------------------------------------- the reference squad (the yardstick)
// Neutral humans of size 3 with every physical damage type and armor type, so no class profits
// from the yardstick itself. A unit's strength is how many of them it beats half of the time.
pub fn kopeyshchik() -> Template {
    creature("Копейщик", 3, 12, 6, 1, Dmg::Pierce, 6, 2, 10, 2, ArmorType::Chain)
}

pub fn mechnik() -> Template {
    creature("Мечник", 3, 12, 6, 1, Dmg::Slash, 6, 2, 10, 2, ArmorType::Leather)
}

pub fn bulavshchik() -> Template {
    creature("Булавщик", 3, 12, 6, 1, Dmg::Blunt, 5, 3, 10, 2, ArmorType::Plate)
}

pub fn luchnik() -> Template {
    let mut t = creature("Лучник", 3, 10, 6, 0, Dmg::Pierce, 6, 1, 9, 2, ArmorType::Leather);
    t.range = 4;
    t
}

pub fn etalon_types() -> Vec<Template> {
    vec![kopeyshchik(), mechnik(), bulavshchik(), luchnik()]
}

/// `n` fighters of the reference squad: spear, sword, mace, bow, spear, sword…
pub fn etalon(n: usize) -> Vec<Template> {
    let types = etalon_types();
    (0..n).map(|i| types[i % types.len()].clone()).collect()
}
