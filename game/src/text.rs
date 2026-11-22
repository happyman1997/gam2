//! The game's words: every line the interface shows is in game/assets/text/ru.json under a key, none in the code or
//! baked into a picture (the game will be translated — docs/STEAM.md). `t("key")`; with values put in:
//! `tf("key", &[("n", 3)])` replaces `{n}`. A key with no line shows itself, so a missing one is easy to see.
//! Another language is another file beside ru.json (en.json…), chosen in the settings; a line it lacks is Russian.

use std::collections::HashMap;
use std::fmt::Display;
use std::sync::{LazyLock, RwLock};

/// The language the words come from; Russian is the game's own, a line another language lacks is taken from it.
pub const BASE: &str = "ru";

struct Table {
    lang: String,
    lines: HashMap<String, String>,
    base: HashMap<String, String>,
}

fn load(lang: &str) -> HashMap<String, String> {
    let path = crate::assets::dir().join("text").join(format!("{lang}.json"));
    std::fs::read_to_string(path).ok().and_then(|s| serde_json::from_str(&s).ok()).unwrap_or_default()
}

static TEXT: LazyLock<RwLock<Table>> =
    LazyLock::new(|| RwLock::new(Table { lang: BASE.into(), lines: HashMap::new(), base: load(BASE) }));

/// The words of a language from now on (its file text/{lang}.json; an unknown one — the base language's).
pub fn set_lang(lang: &str) {
    let mut tb = TEXT.write().unwrap_or_else(|e| e.into_inner());
    if tb.lang != lang {
        tb.lines = if lang == BASE { HashMap::new() } else { load(lang) };
        tb.lang = lang.into();
    }
}

/// The languages there are words for: each file's code (its name without .json) and its own name for itself
/// (`lang.name`), the base language first.
pub fn langs() -> Vec<(String, String)> {
    let mut v: Vec<(String, String)> = std::fs::read_dir(crate::assets::dir().join("text"))
        .into_iter()
        .flatten()
        .flatten()
        .filter_map(|e| {
            let p = e.path();
            let code = p.file_stem()?.to_str()?.to_string();
            (p.extension()? == "json").then_some(code)
        })
        .map(|code| {
            let name = load(&code).remove("lang.name").unwrap_or_else(|| code.clone());
            (code, name)
        })
        .collect();
    v.sort_by_key(|(c, _)| (c != BASE, c.clone()));
    v
}

pub fn t(key: &str) -> String {
    let tb = TEXT.read().unwrap_or_else(|e| e.into_inner());
    tb.lines.get(key).or_else(|| tb.base.get(key)).cloned().unwrap_or_else(|| key.to_string())
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
                    if !key.contains('{') && !super::TEXT.read().unwrap().base.contains_key(key) {
                        missing.push(key.to_string());
                    }
                }
            }
        }
        assert!(missing.is_empty(), "no line for {missing:?}");
    }

    /// Every letter of every line is in each of the game's fonts (a missing one would not be drawn).
    #[test]
    fn every_letter_is_in_the_fonts() {
        let assets = crate::assets::Assets::load().expect("assets");
        let tb = super::TEXT.read().unwrap();
        let mut chars: Vec<char> = tb.base.values().flat_map(|v| v.chars()).filter(|c| *c != '\n').collect();
        chars.sort_unstable();
        chars.dedup();
        for (name, font) in &assets.fonts {
            let missing: String = chars.iter().filter(|c| !font.glyphs.contains_key(c)).collect();
            assert!(missing.is_empty(), "{name} has no glyph for «{missing}»");
        }
    }

    /// The languages: Russian first, by its own name; a language with no file — its lines are Russian.
    #[test]
    fn the_languages() {
        let l = super::langs();
        assert_eq!(l[0].0, super::BASE);
        assert_eq!(l[0].1, super::t("lang.name"));
        let ru = super::t("menu.help");
        super::set_lang("xx");
        assert_eq!(super::t("menu.help"), ru);
        super::set_lang(super::BASE);
    }
}
