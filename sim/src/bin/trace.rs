//! Prints one battle round by round: `cargo run --release --bin trace -- <scenario> <seed>`

use sim::data::*;
use sim::{Battle, Event};

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let which = args.get(1).map(String::as_str).unwrap_or("molot_orudie");
    let seed: u64 = args.get(2).and_then(|s| s.parse().ok()).unwrap_or(1);
    let (a, b) = match which {
        "strazh" => (vec![strazh(), mekhanik()], many(rabochaya(), 25)),
        "otets" => (start_otets(), swarm_start()),
        "gorn" => (vec![gorn()], many(rabochaya(), 10)),
        _ => (vec![molot(), orudie()], many(rabochaya(), 25)),
    };
    let mut bt = Battle::new(seed).with_log();
    bt.add_army(0, &a);
    bt.add_army(1, &b);
    let o = bt.run();
    let name = |i: usize| format!("{}#{}", bt.units[i].t.name, i);
    let (mut kills, mut flees, mut left, mut hits0, mut dmg0, mut hits1, mut dmg1) = (0, 0, 0, 0, 0, 0, 0);
    for e in bt.log.as_ref().unwrap() {
        match e {
            Event::Round(r) => println!("--- раунд {}", r),
            Event::Hit { a, t, dmg } => {
                if bt.units[*a].side == 0 {
                    hits0 += 1;
                    dmg0 += dmg;
                } else {
                    hits1 += 1;
                    dmg1 += dmg;
                }
                if bt.units[*t].side == 0 || *dmg > 0 && bt.units[*a].side == 0 && bt.units[*t].t.size > 2 {
                    println!("{} бьёт {} на {}", name(*a), name(*t), dmg);
                }
            }
            Event::Kill { t } => {
                if bt.units[*t].side == 1 {
                    kills += 1;
                }
                if bt.units[*t].side == 0 {
                    println!("{} сломан", name(*t));
                }
            }
            Event::Flee { t } => {
                flees += 1;
                let _ = t;
            }
            Event::Left { .. } => left += 1,
            Event::Absorbed { t } => println!("{}: лист брони принял удар", name(*t)),
            _ => {}
        }
    }
    println!("\nитог: {:?}", o);
    println!("врагов убито {}, побежало {}, ушло с поля {}", kills, flees, left);
    println!("Литейщик: ударов {}, урона {}; противник: ударов {}, урона {}", hits0, dmg0, hits1, dmg1);
}
