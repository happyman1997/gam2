//! Sound: kira plays the demo's sounds (all CC0 — game/assets/sfx, made by tools/audio/sfx_build.py). Each game
//! sound has a few variants; one is picked at random and played a touch higher or lower, panned to where it happens on
//! the field, so a hundred bites don't sound like one. A limiter on the output keeps a pile of blows from clipping.

use kira::sound::static_sound::{StaticSoundData, StaticSoundHandle};
use kira::effect::compressor::CompressorBuilder;
use kira::track::MainTrackBuilder;
use kira::{AudioManager, AudioManagerSettings, DefaultBackend, Decibels, Panning, PlaybackRate, Tween};
use std::time::Duration;
use std::collections::HashMap;

/// Every sound a little under its file's level: room for several at once before the limiter has to step in.
const HEADROOM: f32 = -4.0;

pub struct Audio {
    mgr: AudioManager<DefaultBackend>,
    sounds: HashMap<String, Vec<StaticSoundData>>,
    seed: u64,
    bed: Option<StaticSoundHandle>,
    /// The battle's sounds and the interface's, in dB under the whole (the settings' two lower sliders).
    battle_db: f32,
    ui_db: f32,
}

/// A slider's 0..1 as dB: a little steeper than the plain law, so its lower notches are quiet indeed; 0 — silence.
fn db(v: f32) -> f32 {
    if v <= 0.001 {
        -80.0
    } else {
        20.0 * v.log10() * 1.5
    }
}

impl Audio {
    /// None when there is no sound device or no sounds — the demo plays on silent.
    pub fn new() -> Option<Self> {
        let root = crate::assets::dir();
        let text = std::fs::read_to_string(root.join("sfx").join("sfx.json")).ok()?;
        let m: serde_json::Value = serde_json::from_str(&text).ok()?;
        let mut sounds = HashMap::new();
        for (name, files) in m.as_object()? {
            let v: Vec<StaticSoundData> = files
                .as_array()?
                .iter()
                .filter_map(|f| StaticSoundData::from_file(root.join(f.as_str()?)).ok())
                .collect();
            if !v.is_empty() {
                sounds.insert(name.clone(), v);
            }
        }
        // the limiter: whatever piles up past −4 dB is held there (fast to catch a blow, slow to let go, so it does
        // not pump), so a volley that kills five at once is loud but never cracks; with HEADROOM it acts only on the
        // peaks of a volley (a few per cent of a battle), not on the battle itself
        let limiter = CompressorBuilder::new()
            .threshold(-4.0)
            .ratio(20.0)
            .attack_duration(Duration::from_millis(1))
            .release_duration(Duration::from_millis(150));
        let settings = AudioManagerSettings { main_track_builder: MainTrackBuilder::new().with_effect(limiter), ..Default::default() };
        let mgr = AudioManager::<DefaultBackend>::new(settings).ok()?;
        Some(Audio { mgr, sounds, seed: 0x2545_f491_4f6c_dd1d, bed: None, battle_db: 0.0, ui_db: 0.0 })
    }

    /// The loudness, each 0..1 (the settings' sliders): the whole game's on the main track (under the limiter's
    /// input), the battle's and the interface's on each sound of theirs (the battle's bed at once).
    pub fn set_volume(&mut self, all: f32, battle: f32, ui: f32) {
        self.mgr.main_track().set_volume(Decibels(db(all)), Tween::default());
        self.battle_db = db(battle);
        self.ui_db = db(ui);
        if let Some(h) = &mut self.bed {
            h.set_volume(Decibels(HEADROOM + self.battle_db), Tween::default());
        }
    }

    fn rand(&mut self) -> f32 {
        self.seed ^= self.seed << 13;
        self.seed ^= self.seed >> 7;
        self.seed ^= self.seed << 17;
        (self.seed % 10_000) as f32 / 10_000.0
    }

    /// The swarm's chirring under the battle, looped, while the swarm lives; off when it is gone or the battle is over.
    pub fn bed(&mut self, on: bool) {
        match (on, self.bed.is_some()) {
            (true, false) => {
                if let Some(v) = self.sounds.get("swarm_bed") {
                    self.bed = self.mgr.play(v[0].loop_region(..).volume(Decibels(HEADROOM + self.battle_db))).ok();
                }
            }
            (false, true) => {
                if let Some(mut h) = self.bed.take() {
                    h.stop(Tween::default());
                }
            }
            _ => {}
        }
    }

    /// A battle's sound: `gain` in dB on top of the sound's own level; `x` — where on the 960-wide field, for the
    /// panning.
    pub fn play(&mut self, name: &str, gain: f32, x: f32) {
        self.sound(name, gain + self.battle_db, x);
    }

    /// The interface's sound (a click, a toggle), in the middle.
    pub fn play_ui(&mut self, name: &str) {
        self.sound(name, self.ui_db, 480.0);
    }

    fn sound(&mut self, name: &str, gain: f32, x: f32) {
        let r1 = self.rand();
        let r2 = self.rand();
        let Some(v) = self.sounds.get(name) else { return };
        let data = v[(r1 * v.len() as f32) as usize % v.len()]
            .volume(Decibels(gain + HEADROOM))
            .playback_rate(PlaybackRate(0.94 + 0.12 * r2 as f64))
            .panning(Panning(((x / 960.0) * 2.0 - 1.0).clamp(-1.0, 1.0) * 0.6));
        let _ = self.mgr.play(data);
    }
}

#[cfg(test)]
mod tests {
    /// Every sound the game names decodes (no sound device needed).
    #[test]
    fn every_sound_decodes() {
        let root = crate::assets::dir();
        let m: serde_json::Value = serde_json::from_str(&std::fs::read_to_string(root.join("sfx/sfx.json")).unwrap()).unwrap();
        for (name, files) in m.as_object().unwrap() {
            for f in files.as_array().unwrap() {
                let d = super::StaticSoundData::from_file(root.join(f.as_str().unwrap()));
                assert!(d.is_ok(), "{name}: {f}");
            }
        }
        for name in ["bite", "hit_metal", "hit_flesh", "zap", "shot", "blast", "squish", "death_rattle", "break", "heal", "miss", "step",
                     "swarm_bed", "click", "toggle", "win", "lose"] {
            assert!(m.get(name).is_some(), "missing {name}");
        }
    }
}
