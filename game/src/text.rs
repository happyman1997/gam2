//! The game's words: every line the interface shows is in game/assets/text/ru.json under a key, none in the code or
//! baked into a picture (the game will be translated — docs/STEAM.md). `t("key")`; with values put in:
//! `tf("key", &[("n", 3)])` replaces `{n}`. A key with no line shows itself, so a missing one is easy to see.

use std::collections::HashMap;
use std::fmt::Display;
use std::sync::OnceLock;

static TEXT: OnceLock<HashMap<String, String>> = OnceLock::new();

fn table() -> &'static HashMap<String, String> {
    TEXT.get_or_init(|| {
        let path = crate::assets::dir().join("text").join("ru.json");
        std::fs::read_to_string(path).ok().and_then(|s| serde_json::from_str(&s).ok()).unwrap_or_default()
    })
}

pub fn t(key: &str) -> String {
    table().get(key).cloned().unwrap_or_else(|| key.to_string())
}

pub fn tf(key: &str, args: &[(&str, &dyn Display)]) -> String {
    let mut s = t(key);
    for (k, v) in args {
        s = s.replace(&format!("{{{k}}}"), &v.to_string());
    }
    s
}

#[cfg(test)]
mod tests {
    /// Every key the code asks for has its line (the code's calls of t/tf with a literal key).
    #[test]
    fn every_key_has_a_line() {
        let dir = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("src");
        let mut missing = vec![];
        for e in std::fs::read_dir(dir).unwrap() {
            let path = e.unwrap().path();
            if path.ends_with("text.rs") {
                continue; // its own examples
            }
            let src = std::fs::read_to_string(path).unwrap();
            for pat in ["t(\"", "tf(\""] {
                for (i, _) in src.match_indices(pat) {
                    // a call of t/tf itself, not of get( or the like
                    if src[..i].chars().last().is_some_and(|c| c.is_alphanumeric() || c == '_' || c == '.') {
                        continue;
                    }
                    let rest = &src[i + pat.len()..];
                    let key = &rest[..rest.find('"').unwrap()];
                    if !key.contains('{') && !super::table().contains_key(key) {
                        missing.push(key.to_string());
                    }
                }
            }
        }
        assert!(missing.is_empty(), "no line for {missing:?}");
    }
}
