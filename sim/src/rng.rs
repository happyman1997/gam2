//! Small deterministic generator (SplitMix64): the same seed always replays the same battle.

#[derive(Clone, Debug)]
pub struct Rng(u64);

impl Rng {
    pub fn new(seed: u64) -> Self {
        Rng(seed ^ 0x5DEE_CE66_D1CE_4E5B)
    }

    pub fn next_u64(&mut self) -> u64 {
        self.0 = self.0.wrapping_add(0x9E37_79B9_7F4A_7C15);
        let mut z = self.0;
        z = (z ^ (z >> 30)).wrapping_mul(0xBF58_476D_1CE4_E5B9);
        z = (z ^ (z >> 27)).wrapping_mul(0x94D0_49BB_1331_11EB);
        z ^ (z >> 31)
    }

    /// A die from 1 to `n` (0 for `n == 0`).
    pub fn die(&mut self, n: u32) -> u32 {
        if n == 0 {
            0
        } else {
            (self.next_u64() % n as u64) as u32 + 1
        }
    }

    /// Damage roll "1–die +bonus": the maximum rolls again and adds (open-ended, as in CoE).
    pub fn damage(&mut self, die: u32, bonus: i32) -> i32 {
        if die == 0 {
            return bonus.max(0);
        }
        let mut total = 0i32;
        loop {
            let r = self.die(die);
            total += r as i32;
            if r < die || die == 1 || total > 1000 {
                break;
            }
        }
        (total + bonus).max(0)
    }
}
