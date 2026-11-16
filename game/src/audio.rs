//! Sound: kira plays the demo's sounds (Kenney, CC0 — game/assets/sfx, made by tools/audio/kenney_sfx.py). Each
//! game sound has a few variants; one is picked at random and played a touch higher or lower, panned to where it
//! happens on the field, so a hundred bites don't sound like one.

use kira::sound::static_sound::StaticSoundData;
use kira::{AudioManager, AudioManagerSettings, DefaultBackend, Decibels, Panning, PlaybackRate};
use std::collections::HashMap;

pub struct Audio {
    mgr: AudioManager<DefaultBackend>,
    sounds: HashMap<String, Vec<StaticSoundData>>,
    seed: u64,
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
        let mgr = AudioManager::<DefaultBackend>::new(AudioManagerSettings::default()).ok()?;
        Some(Audio { mgr, sounds, seed: 0x2545_f491_4f6c_dd1d })
    }

    fn rand(&mut self) -> f32 {
        self.seed ^= self.seed << 13;
        self.seed ^= self.seed >> 7;
        self.seed ^= self.seed << 17;
        (self.seed % 10_000) as f32 / 10_000.0
    }

    /// `gain` in dB on top of the sound's own level; `x` — where on the 960-wide field, for the panning.
    pub fn play(&mut self, name: &str, gain: f32, x: f32) {
        let r1 = self.rand();
        let r2 = self.rand();
        let Some(v) = self.sounds.get(name) else { return };
        let data = v[(r1 * v.len() as f32) as usize % v.len()]
            .volume(Decibels(gain))
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
        for name in ["hit_metal", "hit_flesh", "zap", "blast", "squish", "break", "heal", "miss", "step", "click", "toggle", "win", "lose"] {
            assert!(m.get(name).is_some(), "missing {name}");
        }
    }
}
