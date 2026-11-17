//! The game's units, modules and armies, read from the data files in sim/data (RON): units.ron (every unit's
//! numbers), modules.ron (what a module gives), swarm.ron (the swarm's castes × forms), armies.ron (starting armies
//! and test squads). The files are built into the program (the simulation stays a pure function: no file can be
//! missing at run time); a new unit, module or army is a change of data, not of code. The functions here are the
//! ways the code asks for them, under the names the tools and the game have always used.

use crate::model::{Ability, ArmorType, Dmg, Template, Trait};
use serde::Deserialize;
use std::collections::BTreeMap;
use std::sync::LazyLock;

#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, serde::Serialize, serde::Deserialize)]
pub enum Caste {
    Worker,
    Soldier,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, serde::Serialize, serde::Deserialize)]
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
    Spitter,
}

pub const FORMS: [Form; 10] = [
    Form::Ant,
    Form::Wasp,
    Form::Scorpion,
    Form::Barrel,
    Form::Beetle,
    Form::Isopod,
    Form::Grasshopper,
    Form::Mantis,
    Form::Firefly,
    Form::Spitter,
];

impl Form {
    pub fn name(self) -> &'static str {
        DATA.swarm.forms.iter().find(|d| d.form == self).map(|d| d.name.as_str()).unwrap_or("?")
    }
}

// ---------------------------------------------------------------- the files' shapes

#[derive(Deserialize)]
struct CasteDef {
    suffix: String,
    size: u32,
    die: u32,
    bonus: i32,
    dmg: Dmg,
    init: u32,
    armor: i32,
    morale: u32,
    speed: u32,
}

#[derive(Deserialize)]
struct FormDef {
    form: Form,
    name: String,
    hp: (i32, i32),
    #[serde(default)]
    dmg: Option<Dmg>,
    #[serde(default)]
    armor_type: Option<ArmorType>,
    #[serde(default)]
    range: Option<u32>,
    #[serde(default)]
    die: i32,
    #[serde(default)]
    bonus: i32,
    #[serde(default)]
    armor: i32,
    #[serde(default)]
    init: i32,
    #[serde(default)]
    speed: i32,
    #[serde(default)]
    add: (Vec<Trait>, Vec<Trait>),
    #[serde(default)]
    remove: Vec<Trait>,
    #[serde(default)]
    abilities: (Vec<Ability>, Vec<Ability>),
}

#[derive(Deserialize)]
struct SwarmDef {
    castes: BTreeMap<Caste, CasteDef>,
    armor_type: ArmorType,
    traits: Vec<Trait>,
    forms: Vec<FormDef>,
}

#[derive(Deserialize)]
struct Entry {
    #[serde(default)]
    unit: Option<String>,
    #[serde(default)]
    swarm: Option<(Caste, Form)>,
    #[serde(default = "one")]
    count: usize,
    #[serde(default)]
    smaller: bool,
    #[serde(default)]
    modules: Vec<String>,
    #[serde(default)]
    abilities: Vec<Ability>,
}

fn one() -> usize {
    1
}

struct Data {
    units: BTreeMap<String, Template>,
    modules: BTreeMap<String, Ability>,
    swarm: SwarmDef,
    armies: BTreeMap<String, Vec<Entry>>,
}

fn parse<T: serde::de::DeserializeOwned>(file: &str, text: &str) -> T {
    ron::from_str(text).unwrap_or_else(|e| panic!("sim/data/{file}: {e}"))
}

static DATA: LazyLock<Data> = LazyLock::new(|| Data {
    units: parse("units.ron", include_str!("../data/units.ron")),
    modules: parse("modules.ron", include_str!("../data/modules.ron")),
    swarm: parse("swarm.ron", include_str!("../data/swarm.ron")),
    armies: parse("armies.ron", include_str!("../data/armies.ron")),
});

/// A unit by its key in units.ron.
pub fn unit(key: &str) -> Template {
    DATA.units.get(key).cloned().unwrap_or_else(|| panic!("sim/data/units.ron: no unit \"{key}\""))
}

/// A module by its key in modules.ron: the ability it gives.
pub fn module(key: &str) -> Ability {
    *DATA.modules.get(key).unwrap_or_else(|| panic!("sim/data/modules.ron: no module \"{key}\""))
}

/// An army by its key in armies.ron, every body written out.
pub fn army(key: &str) -> Vec<Template> {
    let entries = DATA.armies.get(key).unwrap_or_else(|| panic!("sim/data/armies.ron: no army \"{key}\""));
    let mut out = vec![];
    for e in entries {
        let mut t = match (&e.unit, e.swarm) {
            (Some(u), _) => unit(u),
            (None, Some((c, f))) => swarm(c, f),
            (None, None) => panic!("sim/data/armies.ron, \"{key}\": a line with neither unit nor swarm"),
        };
        if e.smaller {
            t = t.smaller();
        }
        for m in &e.modules {
            t = t.with(module(m));
        }
        for a in &e.abilities {
            t = t.with(*a);
        }
        out.extend(std::iter::repeat_n(t, e.count));
    }
    out
}

/// Every key the files name, checked: each army's units, swarm forms and modules exist (a test runs it).
pub fn check() -> Result<(), String> {
    for (key, entries) in &DATA.armies {
        for e in entries {
            if let Some(u) = &e.unit {
                if !DATA.units.contains_key(u) {
                    return Err(format!("armies.ron \"{key}\": no unit \"{u}\" in units.ron"));
                }
            }
            if let Some((_, f)) = e.swarm {
                if !DATA.swarm.forms.iter().any(|d| d.form == f) {
                    return Err(format!("armies.ron \"{key}\": no form {f:?} in swarm.ron"));
                }
            }
            if e.unit.is_none() && e.swarm.is_none() {
                return Err(format!("armies.ron \"{key}\": a line with neither unit nor swarm"));
            }
            for m in &e.modules {
                if !DATA.modules.contains_key(m) {
                    return Err(format!("armies.ron \"{key}\": no module \"{m}\" in modules.ron"));
                }
            }
        }
    }
    for f in FORMS {
        if !DATA.swarm.forms.iter().any(|d| d.form == f) {
            return Err(format!("swarm.ron: no form {f:?}"));
        }
    }
    Ok(())
}

// ---------------------------------------------------------------- the Foundry: frames and leaders
pub fn strazh() -> Template {
    unit("strazh")
}

/// Мудрец, the mage: the spell Разряд (lightning 1–8 +1, range 4), Питание, Замыкание.
pub fn mudrets() -> Template {
    unit("mudrets")
}

pub fn gorn() -> Template {
    unit("gorn")
}

pub fn orudie() -> Template {
    unit("orudie")
}

pub fn mekhanik() -> Template {
    unit("mekhanik")
}

pub fn kamenshchik() -> Template {
    unit("kamenshchik")
}

pub fn otets_kolossa() -> Template {
    unit("otets_kolossa")
}

pub fn izobretatel() -> Template {
    unit("izobretatel")
}

pub fn manyak() -> Template {
    unit("manyak")
}

pub fn zodchiy() -> Template {
    unit("zodchiy")
}

// ---------------------------------------------------------------- modules
pub fn mortira() -> Ability {
    module("mortira")
}

pub fn remont() -> Ability {
    module("remont")
}

pub fn grozovaya_katushka() -> Ability {
    module("grozovaya_katushka")
}

pub fn peregruzka() -> Ability {
    module("peregruzka")
}

pub fn ognenny_shar() -> Ability {
    module("ognenny_shar")
}

pub fn golova_katapulta() -> Ability {
    module("golova_katapulta")
}

// ---------------------------------------------------------------- the Swarm and others
pub fn rabochaya() -> Template {
    unit("rabochaya")
}

pub fn soldat() -> Template {
    unit("soldat")
}

/// Not in the concept's number table yet: a probe for "the swarm's answer to metal".
pub fn zhuk() -> Template {
    unit("zhuk")
}

/// Not in the concept's number table yet: an acid spitter, range 2.
pub fn kislotnik() -> Template {
    unit("kislotnik")
}

pub fn voin() -> Template {
    unit("voin")
}

pub fn many(t: Template, n: usize) -> Vec<Template> {
    vec![t; n]
}

// ---------------------------------------------------------------- armies
pub fn start_otets() -> Vec<Template> {
    army("start_otets")
}

pub fn start_izobretatel() -> Vec<Template> {
    army("start_izobretatel")
}

pub fn start_manyak() -> Vec<Template> {
    army("start_manyak")
}

pub fn start_zodchiy() -> Vec<Template> {
    army("start_zodchiy")
}

pub fn swarm_start() -> Vec<Template> {
    army("swarm_start")
}

pub fn humans_squad() -> Vec<Template> {
    army("humans_squad")
}

// ---------------------------------------------------------------- the reference squad (the yardstick)
// Neutral humans of size 3 with every physical damage type and armor type, so no class profits
// from the yardstick itself. A unit's strength is how many of them it beats half of the time.
pub fn kopeyshchik() -> Template {
    unit("kopeyshchik")
}

pub fn mechnik() -> Template {
    unit("mechnik")
}

pub fn bulavshchik() -> Template {
    unit("bulavshchik")
}

pub fn luchnik() -> Template {
    unit("luchnik")
}

pub fn etalon_types() -> Vec<Template> {
    army("etalon_types")
}

/// `n` fighters of the reference squad: spear, sword, mace, bow, spear, sword…
pub fn etalon(n: usize) -> Vec<Template> {
    let types = etalon_types();
    (0..n).map(|i| types[i % types.len()].clone()).collect()
}

// ---------------------------------------------------------------- the Swarm: castes × forms
/// Health of each form by caste (from swarm.ron; see the `swarm` tool for what each is worth).
pub fn swarm_hp() -> [[i32; 10]; 2] {
    let mut hp = [[0; 10]; 2];
    for (fi, f) in FORMS.iter().enumerate() {
        let d = DATA.swarm.forms.iter().find(|d| d.form == *f).expect("every form in swarm.ron");
        hp[0][fi] = d.hp.0;
        hp[1][fi] = d.hp.1;
    }
    hp
}

/// A swarm body: its caste's numbers, then its form's (swarm.ron).
pub fn swarm(c: Caste, f: Form) -> Template {
    let sw = &DATA.swarm;
    let k = &sw.castes[&c];
    let d = sw.forms.iter().find(|d| d.form == f).unwrap_or_else(|| panic!("sim/data/swarm.ron: no form {f:?}"));
    let soldier = c == Caste::Soldier;
    let mut traits: Vec<Trait> = sw.traits.iter().copied().filter(|t| !d.remove.contains(t)).collect();
    traits.extend(if soldier { &d.add.1 } else { &d.add.0 }.iter().copied());
    Template {
        name: format!("{} ({})", d.name, k.suffix).into(),
        size: k.size,
        hp: if soldier { d.hp.1 } else { d.hp.0 },
        die: (k.die as i32 + d.die) as u32,
        bonus: k.bonus + d.bonus,
        dmg: d.dmg.unwrap_or(k.dmg),
        init: (k.init as i32 + d.init) as u32,
        armor: k.armor + d.armor,
        morale: k.morale,
        speed: (k.speed as i32 + d.speed).max(1) as u32,
        range: d.range.unwrap_or(1),
        armor_type: d.armor_type.unwrap_or(sw.armor_type),
        golem: false,
        traits,
        abilities: if soldier { d.abilities.1.clone() } else { d.abilities.0.clone() },
    }
}

// ---------------------------------------------------------------- the Swarm: leaders
pub fn matka() -> Template {
    unit("matka")
}

pub fn razum() -> Template {
    unit("razum")
}

pub fn pozhiratel() -> Template {
    unit("pozhiratel")
}

pub fn kukushka() -> Template {
    unit("kukushka")
}

// ---------------------------------------------------------------- the Swarm: starting armies
// The Swarm's limit is counted in points: a worker 1, a soldier 3 (1 point ≈ 0.33 of a reference
// fighter). A start is 30 points plus the leader.
pub fn start_matka() -> Vec<Template> {
    army("start_matka")
}

pub fn start_razum() -> Vec<Template> {
    army("start_razum")
}

pub fn start_pozhiratel() -> Vec<Template> {
    army("start_pozhiratel")
}

pub fn start_kukushka() -> Vec<Template> {
    army("start_kukushka")
}
