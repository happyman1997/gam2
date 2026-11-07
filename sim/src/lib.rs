//! Battle logic for the game: deterministic, no graphics.
//! Two armies and a seed in, an outcome and (optionally) an event list out.

pub mod battle;
pub mod data;
pub mod model;
pub mod power;
pub mod rng;

pub use battle::{fight, Battle, Event, Outcome};
