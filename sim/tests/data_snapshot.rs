//! Every unit, module and army the data defines, written out in full — so a change of how the data is stored (code
//! or files) can be checked to leave every number as it was.
use sim::data::*;

pub fn dump() -> String {
    let mut s = String::new();
    let mut put = |name: &str, v: String| {
        s.push_str(name);
        s.push_str(" = ");
        s.push_str(&v);
        s.push('\n');
    };
    for (n, t) in [
        ("strazh", strazh()), ("mudrets", mudrets()), ("gorn", gorn()), ("orudie", orudie()), ("mekhanik", mekhanik()),
        ("kamenshchik", kamenshchik()), ("otets_kolossa", otets_kolossa()), ("izobretatel", izobretatel()),
        ("manyak", manyak()), ("zodchiy", zodchiy()), ("rabochaya", rabochaya()), ("soldat", soldat()), ("zhuk", zhuk()),
        ("kislotnik", kislotnik()), ("voin", voin()), ("kopeyshchik", kopeyshchik()), ("mechnik", mechnik()),
        ("bulavshchik", bulavshchik()), ("luchnik", luchnik()), ("matka", matka()), ("razum", razum()),
        ("pozhiratel", pozhiratel()), ("kukushka", kukushka()),
    ] {
        put(n, format!("{t:?}"));
    }
    for (n, a) in [("mortira", mortira()), ("remont", remont()), ("grozovaya_katushka", grozovaya_katushka()),
                   ("peregruzka", peregruzka()), ("ognenny_shar", ognenny_shar()), ("golova_katapulta", golova_katapulta())] {
        put(n, format!("{a:?}"));
    }
    for (n, v) in [("start_otets", start_otets()), ("start_izobretatel", start_izobretatel()), ("start_manyak", start_manyak()),
                   ("start_zodchiy", start_zodchiy()), ("swarm_start", swarm_start()), ("humans_squad", humans_squad()),
                   ("etalon_types", etalon_types()), ("etalon7", etalon(7)), ("start_matka", start_matka()),
                   ("start_razum", start_razum()), ("start_pozhiratel", start_pozhiratel()), ("start_kukushka", start_kukushka())] {
        put(n, format!("{v:?}"));
    }
    for c in [Caste::Worker, Caste::Soldier] {
        for f in FORMS {
            put(&format!("swarm {c:?} {f:?}"), format!("{:?}", swarm(c, f)));
        }
    }
    s
}

/// The data as it was when it moved from code to files (tests/data_snapshot.txt): every number the same.
#[test]
fn data_unchanged() {
    let now = dump();
    let path = concat!(env!("CARGO_MANIFEST_DIR"), "/tests/data_snapshot.txt");
    if std::env::var_os("WRITE_SNAPSHOT").is_some() {
        std::fs::write(path, &now).unwrap();
    }
    let was = std::fs::read_to_string(path).expect("snapshot");
    for (a, b) in was.lines().zip(now.lines()) {
        assert_eq!(a, b);
    }
    assert_eq!(was.lines().count(), now.lines().count());
}

/// Every army names only units, forms and modules that exist.
#[test]
fn data_consistent() {
    sim::data::check().unwrap();
}
