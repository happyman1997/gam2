// The Foundry's forge fire, for the smelting hearth: the tongue, lick, flame-puff, smoke, ember and spark recipe of
// pixelfx's brazier (fire/_lib.js burn, adapted there from Sprite Fusion's open-source fire, MIT, Hugo Duprez),
// spread wide over a heap of coal and with no bowl or stand of its own — the game draws the coals and the crucible.
import { fit, mix, WHITE } from "../../core/index.js";
import { noiseFor, hotFirst, burn, looped, drift, spark, ember } from "../fire/_lib.js";

export const meta = {
  name: "Forge fire",
  desc: "A wide fire roaring up off a heap of coal round a crucible: tongues of different heights licking and leaping, puffs torn off the tips, smoke curling up, sparks streaming up in the draught.",
  tags: ["fire", "forge", "hearth", "loop", "foundry"],
  size: [232, 176],
  origin: [116, 150],
  duration: 3,
  loop: true,
  fps: 24,
  bg: "dark",
  options: {
    palette: ["#4a1712", "#8a1f17", "#c9281f", "#f2561d", "#ff8a2a", "#ffc23d", "#ffe26b", "#fff3a6", "#ffffff"],
    seed: 11,
  },
};

const D = meta.duration, NL = noiseFor(D);
// [x, y from the coals, height share, half-width, back row?] — tall behind the crucible's sides, low in front
const TONGUES = [
  [-40, -6, 0.78, 13, 1], [38, -6, 0.86, 13, 1], [-66, 0, 0.42, 9, 1], [66, 0, 0.4, 9, 1], [0, -10, 0.5, 11, 1],
  [-50, 6, 0.34, 9, 0], [-24, 6, 0.28, 8, 0], [24, 6, 0.3, 8, 0], [50, 6, 0.36, 9, 0],
];

export function draw(p, t, o) {
  const F = fit(o.palette, 9), H = hotFirst(F), S = o.seed;
  const SPARKS = [H[1], H[2], H[4], H[5]], EMB = [H[1], H[2], H[4], H[6]];
  burn(p, t, TONGUES, {
    H, D, NL, S, x: 0, y: 0, height: 66, lean: 0.12, spread: 46,
    puffs: 6, licks: 3, smoke: 16, smokeSize: 6, smokeLife: [1.8, 2.6], embers: 22, glowR: 90, glow: 0.7, wind: 4,
  });
  looped(t, D, 70, S + 600, (r) => {
    const side = r.range(-1, 1);
    return { x: side * 60, y: -r.range(10, 40), vx: side * r.range(5, 30), vy: -r.range(70, 150), life: r.range(0.7, 1.6), a: r.range(0, 6.3), w: r.range(1.8, 3.2), m: r.range(3, 8), big: r.chance(0.12) };
  }, (q, age) => {
    const [x, y, vx, vy] = drift(q.x, q.y, q.vx, q.vy, age, 0, -22, 1.9, 1.9), k = 1 - age / q.life;
    const wob = q.m * (Math.sin(age * q.w + q.a) - Math.sin(q.a)) * Math.min(1, age * 1.5);
    const wv = q.m * q.w * Math.cos(age * q.w + q.a) * Math.min(1, age * 1.5);
    if (Math.hypot(vx + wv, vy) > 40) spark(p, x + wob, y, vx + wv, vy, k, SPARKS);
    else ember(p, x + wob, y, k, q.big ? 2 : 1, EMB, age * 40 + q.a);
  });
}
