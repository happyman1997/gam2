// The Devourer eats one fallen beside it: a wet burst of ichor and blood where its jaws close on the body, spattering
// the ground and soaking in. pixelfx's acid splash (nature/acid-splash.js, its drops adapted from Sprite Fusion's
// open-source blood, MIT, Hugo Duprez) in the colours of blood, a beat quicker.
import * as base from "../nature/acid-splash.js";

export const meta = {
  ...base.meta,
  name: "Devour splash",
  desc: "Jaws close on a fallen body: a wet burst of blood and ichor crowns up, spatters and soaks into the ground.",
  tags: ["swarm", "blood", "devour", "splash", "liquid", "ground", "one-shot"],
  options: { ...base.meta.options, palette: ["#14040a", "#2a0810", "#4a0c16", "#7a121e", "#a81c26", "#d43a34", "#ff6a58", "#ffb4a0"], seed: 11 },
};

export const create = base.create;
