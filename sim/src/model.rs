//! Units as data: damage and armor types, passives, abilities, unit templates.

/// Damage types.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Dmg {
    Pierce,
    Slash,
    Blunt,
    Fire,
    Cold,
    Shock,
    Poison,
    Acid,
}

/// Armor types: what the protection is made of.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ArmorType {
    None,
    Soft,
    Leather,
    Chain,
    Plate,
    Cast,
    Chitin,
    HeavyChitin,
    Bone,
    Wood,
    Stone,
    Iron,
    Flame,
}

impl ArmorType {
    /// Holds the blow: damage halved.
    pub fn resists(self, d: Dmg) -> bool {
        use ArmorType::*;
        use Dmg::*;
        match self {
            Leather => d == Blunt,
            Chain => d == Slash,
            Plate => matches!(d, Slash | Pierce),
            Cast => d == Pierce,
            Chitin => d == Slash,
            HeavyChitin => matches!(d, Slash | Pierce),
            Bone => d == Pierce,
            Wood => d == Pierce,
            Stone | Iron => matches!(d, Slash | Pierce),
            _ => false,
        }
    }

    /// Breaks under the blow: damage doubled.
    pub fn weak_to(self, d: Dmg) -> bool {
        use ArmorType::*;
        use Dmg::*;
        match self {
            Soft => d == Pierce,
            Leather => d == Slash,
            Chain => d == Pierce,
            Plate | Chitin | HeavyChitin | Bone | Stone => d == Blunt,
            Wood => matches!(d, Fire | Slash),
            Flame => d == Cold,
            _ => false,
        }
    }

    pub fn immune(self, d: Dmg) -> bool {
        self == ArmorType::Flame && d == Dmg::Fire
    }

    /// Metal conducts: +50% from lightning.
    pub fn metal(self) -> bool {
        matches!(self, ArmorType::Chain | ArmorType::Plate | ArmorType::Cast | ArmorType::Iron)
    }

    /// Armor taken off by one acid hit.
    pub fn acid_strip(self) -> i32 {
        if matches!(self, ArmorType::Cast | ArmorType::Iron) {
            2
        } else {
            1
        }
    }
}

/// Passives and weaknesses that the battle rules know about.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Trait {
    /// Adjacent enemies must hit this unit first (Страж).
    Zaslon,
    /// Blows ignore half of the target's armor (Молот).
    Probivnoy,
    /// Each round sets one adjacent enemy on fire (Горн).
    ZharGorna,
    /// Ranged: aims at the far rows and loses nothing at long range (Орудие).
    Navodka,
    /// Adjacent allied golems mend 1 each round (Механик).
    Naladka,
    /// Does not attack (Механик).
    NoAttack,
    /// Fire deals a quarter (the Foundry class).
    FireResist75,
    /// Morale 99, never afraid (golems).
    Mindless,
    /// Poison does nothing (golems).
    PoisonImmune,
    /// Cannot be moved or knocked back (Отец колосса).
    Unstoppable,
    /// Enemies within `radius` check fear `1–die` against morale every round.
    Fear { die: u32, radius: u32 },
}

/// Abilities with a condition.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Ability {
    /// Every `every` rounds, instead of the normal attack: area blow on a cell and its neighbours (Мортира).
    Volley { every: u32, die: u32, bonus: i32, dmg: Dmg },
    /// Every `every` rounds: mend the most damaged adjacent golem (Ремонт).
    Repair { every: u32, amount: i32 },
    /// Every `every` rounds, instead of the normal attack: one bolt within `range`
    /// (Грозовая катушка: range 1; Голова-катапульта: range 3).
    Bolt { every: u32, die: u32, bonus: i32, dmg: Dmg, range: u32 },
    /// The melee blow also hits a second adjacent enemy (Кистень).
    Flail,
    /// The first `n` damaging blows of the battle are absorbed (Броневые листы).
    Plates(u32),
    /// Ranged unit with an enemy adjacent fires at up to 3 adjacent enemies at full power (Картечь).
    PointBlank,
    /// Once per round takes a blow meant for an adjacent allied golem (Перехват).
    Intercept,
}

#[derive(Clone, Debug)]
pub struct Template {
    pub name: &'static str,
    pub size: u32,
    pub hp: i32,
    pub die: u32,
    pub bonus: i32,
    pub dmg: Dmg,
    pub init: u32,
    pub armor: i32,
    pub morale: u32,
    pub speed: u32,
    pub range: u32,
    pub armor_type: ArmorType,
    pub golem: bool,
    pub traits: Vec<Trait>,
    pub abilities: Vec<Ability>,
}

impl Template {
    pub fn has(&self, t: Trait) -> bool {
        self.traits.contains(&t)
    }

    pub fn fear(&self) -> Option<(u32, u32)> {
        self.traits.iter().find_map(|t| match t {
            Trait::Fear { die, radius } => Some((*die, *radius)),
            _ => None,
        })
    }

    pub fn has_ability(&self, pred: impl Fn(&Ability) -> bool) -> bool {
        self.abilities.iter().any(pred)
    }

    pub fn with(mut self, a: Ability) -> Self {
        self.abilities.push(a);
        self
    }

    pub fn with_trait(mut self, t: Trait) -> Self {
        self.traits.push(t);
        self
    }

    /// The Inventor's frames: one size smaller, ×0.7 durability, −2 to the damage bonus.
    pub fn smaller(mut self) -> Self {
        self.size -= 1;
        self.hp = self.hp * 7 / 10;
        self.bonus -= 2;
        self
    }

    pub fn morale_eff(&self) -> u32 {
        if self.has(Trait::Mindless) {
            99
        } else {
            self.morale
        }
    }
}

/// Damage that gets through: vulnerability, stun, armor (halved by Пробивной), resistance,
/// elemental resistance, metal conducting lightning. The order of docs/CONCEPT.md.
pub fn mitigate(raw: i32, dmg: Dmg, t: &Template, armor_now: i32, stunned: bool, probivnoy: bool) -> i32 {
    let at = t.armor_type;
    if at.immune(dmg) || (dmg == Dmg::Poison && t.has(Trait::PoisonImmune)) {
        return 0;
    }
    let mut d = raw;
    if at.weak_to(dmg) {
        d *= 2;
    }
    if stunned {
        d += 1;
    }
    if dmg != Dmg::Fire && dmg != Dmg::Poison {
        let mut arm = armor_now.max(0);
        if probivnoy {
            arm /= 2;
        }
        d -= arm;
    }
    if d <= 0 {
        return 0;
    }
    if at.resists(dmg) {
        d /= 2;
    }
    if dmg == Dmg::Fire && t.has(Trait::FireResist75) {
        d = (d / 4).max(1);
    }
    if dmg == Dmg::Shock && at.metal() {
        d = d * 3 / 2;
    }
    d.max(0)
}
