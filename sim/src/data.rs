//! Draft numbers from docs/CONCEPT.md. Later this moves to data files.

use crate::model::{Ability, ArmorType, Dmg, Template, Trait};

fn golem(name: &'static str, size: u32, hp: i32, die: u32, bonus: i32, init: u32, armor: i32, speed: u32) -> Template {
    Template {
        name: name.into(),
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
    golem("Страж", 6, 100, 6, 3, 3, 4, 1).with_trait(Trait::Zaslon)
}

/// Мудрец, the mage: the spell Разряд (lightning 1–8 +1, range 4), Питание, Замыкание.
pub fn mudrets() -> Template {
    let mut t = golem("Мудрец", 5, 40, 8, 1, 5, 2, 1)
        .with_trait(Trait::Caster)
        .with_trait(Trait::Pitanie)
        .with_trait(Trait::Zamykanie);
    t.dmg = Dmg::Shock;
    t.range = 4;
    t
}

pub fn gorn() -> Template {
    golem("Горн", 5, 50, 6, 1, 3, 2, 1).with_trait(Trait::ZharGorna)
}

pub fn orudie() -> Template {
    let mut t = golem("Орудие", 5, 55, 10, 3, 4, 2, 1).with_trait(Trait::Navodka);
    t.range = 3;
    t
}

pub fn mekhanik() -> Template {
    let mut t = golem("Механик", 4, 35, 0, 0, 0, 2, 2)
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
    golem("Отец колосса", 7, 160, 8, 2, 1, 3, 1)
        .with_trait(Trait::Unstoppable)
        .with_trait(Trait::Fear { die: 9, radius: 3 })
}

fn human_leader(name: &'static str, size: u32, hp: i32, die: u32, bonus: i32, dmg: Dmg, init: u32, morale: u32, speed: u32) -> Template {
    Template {
        name: name.into(),
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
    Ability::Repair { every: 2, amount: 4 }
}

pub fn grozovaya_katushka() -> Ability {
    Ability::Bolt { every: 2, die: 6, bonus: 0, dmg: Dmg::Shock, range: 1 }
}

pub fn peregruzka() -> Ability {
    Ability::Overload { every: 2 }
}

pub fn ognenny_shar() -> Ability {
    Ability::Fireball { every: 3, die: 4, bonus: 0, range: 5 }
}

pub fn golova_katapulta() -> Ability {
    Ability::Bolt { every: 2, die: 6, bonus: 2, dmg: Dmg::Blunt, range: 3 }
}

// ---------------------------------------------------------------- the Swarm and others
fn creature(name: &'static str, size: u32, hp: i32, die: u32, bonus: i32, dmg: Dmg, init: u32, armor: i32, morale: u32, speed: u32, at: ArmorType) -> Template {
    Template {
        name: name.into(),
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

/// Изобретатель: small Мудрец with Перегрузка and Грозовая катушка, small Орудие with Мортира
/// and Грозовая катушка, small Механик with Ремонт (Отражатель — not yet).
pub fn start_izobretatel() -> Vec<Template> {
    vec![
        mudrets().smaller().with(peregruzka()).with(grozovaya_katushka()),
        orudie().smaller().with(mortira()).with(grozovaya_katushka()),
        mekhanik().smaller().with(remont()),
        izobretatel(),
    ]
}

/// Маньяк: Мудрец with Огненный шар (Ноги-пилы — not yet), Орудие with Голова-катапульта and Картечь.
pub fn start_manyak() -> Vec<Template> {
    vec![mudrets().with(ognenny_shar()), orudie().with(golova_katapulta()).with(Ability::PointBlank), manyak()]
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

// ---------------------------------------------------------------- the Swarm: castes × forms
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Caste {
    Worker,
    Soldier,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Form {
    Ant,
    Wasp,
    Scorpion,
    Barrel,
    Beetle,
    Isopod,
    Grasshopper,
    Mantis,
    Firefly,
}

pub const FORMS: [Form; 9] = [
    Form::Ant,
    Form::Wasp,
    Form::Scorpion,
    Form::Barrel,
    Form::Beetle,
    Form::Isopod,
    Form::Grasshopper,
    Form::Mantis,
    Form::Firefly,
];

impl Form {
    pub fn name(self) -> &'static str {
        match self {
            Form::Ant => "Муравей",
            Form::Wasp => "Оса",
            Form::Scorpion => "Скорпион",
            Form::Barrel => "Бочонок",
            Form::Beetle => "Жук",
            Form::Isopod => "Мокрица",
            Form::Grasshopper => "Кузнечик",
            Form::Mantis => "Богомол",
            Form::Firefly => "Светляк",
        }
    }
}

/// Health of each form by caste (see the `swarm` tool for what each is worth).
pub const SWARM_HP: [[i32; 9]; 2] = [
    // Ant Wasp Scorp Barrel Beetle Isopod Grass Mantis Firefly
    [8, 8, 8, 11, 8, 8, 8, 7, 8],
    [14, 11, 14, 19, 12, 11, 14, 11, 14],
];

pub fn swarm(c: Caste, f: Form) -> Template {
    let ci = (c == Caste::Soldier) as usize;
    let fi = FORMS.iter().position(|&x| x == f).unwrap();
    let (size, die, bonus, dmg, init, armor, morale, speed) = match c {
        Caste::Worker => (1, 4, 1, Dmg::Pierce, 8, 0, 6, 3),
        Caste::Soldier => (2, 8, 0, Dmg::Slash, 6, 2, 9, 2),
    };
    let mut t = creature("", size, SWARM_HP[ci][fi], die, bonus, dmg, init, armor, morale, speed, ArmorType::Chitin);
    t.name = format!("{} ({})", f.name(), if ci == 0 { "рабочая" } else { "солдат" }).into();
    t.traits = vec![Trait::Staya, Trait::Devour];
    let big = ci == 1;
    match f {
        Form::Ant => t.traits.push(Trait::Stroy),
        Form::Wasp => {
            t.traits.push(Trait::Flyer);
            t.speed += 1;
            t.dmg = Dmg::Pierce;
        }
        Form::Scorpion => {
            t.traits.push(Trait::Venom { die: if big { 6 } else { 4 } });
            t.dmg = Dmg::Pierce;
            t.speed = (t.speed - 1).max(1);
        }
        Form::Barrel => {
            t.range = 3;
            t.die += 2;
            t.dmg = Dmg::Acid;
            t.armor_type = ArmorType::Soft;
            t.traits.push(Trait::BurstAcid { die: if big { 6 } else { 4 } });
        }
        Form::Beetle => {
            t.armor_type = ArmorType::HeavyChitin;
            t.dmg = Dmg::Blunt;
            t.speed = (t.speed - 1).max(1);
            t.traits.push(Trait::Charge);
        }
        Form::Isopod => {
            t.armor_type = ArmorType::HeavyChitin;
            t.armor += 1;
            t.bonus -= 1;
            t.speed = (t.speed - 1).max(1);
            t.traits.push(Trait::Thorns { die: if big { 3 } else { 2 } });
            t.traits.push(Trait::CurlUp);
        }
        Form::Grasshopper => t.traits.push(Trait::Leap),
        Form::Mantis => {
            t.traits.retain(|x| *x != Trait::Staya);
            t.traits.push(Trait::TwinBlades);
            t.dmg = Dmg::Slash;
            t.init += 2;
        }
        Form::Firefly => {
            t.traits.push(Trait::Glow);
            t.bonus -= 1;
            t.abilities.push(Ability::Flash { every: 3 });
        }
    }
    t
}

// ---------------------------------------------------------------- the Swarm: leaders
fn swarm_leader(name: &'static str, size: u32, hp: i32, die: u32, bonus: i32, dmg: Dmg, init: u32, armor: i32, morale: u32, speed: u32, at: ArmorType) -> Template {
    let mut t = creature(name, size, hp, die, bonus, dmg, init, armor, morale, speed, at);
    t.traits = vec![Trait::Leader, Trait::Devour];
    t
}

pub fn matka() -> Template {
    swarm_leader("Матка", 6, 80, 6, 2, Dmg::Slash, 4, 2, 14, 1, ArmorType::Chitin).with(Ability::Brood { every: 3, n: 2 })
}

pub fn razum() -> Template {
    swarm_leader("Разум улья", 4, 22, 4, 0, Dmg::Pierce, 6, 0, 12, 1, ArmorType::Soft)
        .with_trait(Trait::HiveMind)
        .with(Ability::Mark { every: 2 })
}

pub fn pozhiratel() -> Template {
    swarm_leader("Пожиратель", 5, 41, 8, 2, Dmg::Slash, 5, 2, 14, 2, ArmorType::HeavyChitin).with_trait(Trait::Grows)
}

pub fn kukushka() -> Template {
    swarm_leader("Кукушка", 3, 12, 6, 0, Dmg::Pierce, 7, 1, 11, 2, ArmorType::Chitin)
        .with_trait(Trait::Infects)
        .with_trait(Trait::Changeling)
}

// ---------------------------------------------------------------- the Swarm: starting armies
// The Swarm's limit is counted in points: a worker 1, a soldier 3 (1 point ≈ 0.33 of a reference
// fighter). A start is 30 points plus the leader.
fn mix(parts: &[(Caste, Form, usize)]) -> Vec<Template> {
    let mut v = vec![];
    for &(c, f, n) in parts {
        v.extend(vec![swarm(c, f); n]);
    }
    v
}

pub fn start_matka() -> Vec<Template> {
    use Caste::*;
    use Form::*;
    let mut v = mix(&[(Worker, Ant, 12), (Worker, Wasp, 3), (Worker, Scorpion, 3), (Soldier, Ant, 2), (Soldier, Beetle, 1), (Soldier, Isopod, 1)]);
    v.push(matka());
    v
}

pub fn start_razum() -> Vec<Template> {
    use Caste::*;
    use Form::*;
    let mut v = mix(&[(Worker, Ant, 9), (Worker, Firefly, 3), (Soldier, Ant, 3), (Soldier, Mantis, 2), (Soldier, Scorpion, 1)]);
    v.push(razum());
    v
}

pub fn start_pozhiratel() -> Vec<Template> {
    use Caste::*;
    use Form::*;
    let mut v = mix(&[(Worker, Ant, 15), (Worker, Grasshopper, 3), (Soldier, Ant, 2)]);
    v.push(pozhiratel());
    v
}

pub fn start_kukushka() -> Vec<Template> {
    use Caste::*;
    use Form::*;
    let mut v = mix(&[(Worker, Ant, 15), (Worker, Scorpion, 3), (Worker, Barrel, 3), (Soldier, Ant, 3)]);
    v.push(kukushka());
    v
}
