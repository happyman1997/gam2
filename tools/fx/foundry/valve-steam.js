// The Foundry's valve letting off steam when it is turned: a hiss of vapour jetting up and to the side from the
// spindle, then billowing, slowing and thinning away. Built on pixelfx's particles (core/sim.js, adapted from Sprite
// Fusion's open-source effects, MIT, Hugo Duprez).
import { Particles, P, Rng, fit } from "../../core/index.js";

export const meta = {
  name: "Valve steam",
  desc: "A valve turned: a hiss of steam jets up off the spindle, billows into a few soft clouds that drift up and thin away.",
  tags: ["steam", "valve", "foundry", "ui", "one-shot"],
  size: [128, 128],
  origin: [44, 104],
  duration: 1.4,
  loop: false,
  fps: 24,
  bg: "dark",
  options: { palette: ["#3a3644", "#5a5664", "#8a8694", "#c8c4d0", "#f0eef4"], seed: 3 },
};

export function create(o) {
  const C = fit(o.palette, 5), R = new Rng(o.seed);
  const ps = new Particles({ rng: R });
  let t = 0, acc = 0;
  return {
    update(dt) {
      t += dt;
      // the jet for the first half second, thinning as the valve shuts the hiss off
      if (t < 0.55) {
        acc += dt * (120 - t * 160);
        while (acc > 1) {
          acc -= 1;
          const a = -Math.PI / 2 + 0.55 + R.range(-0.25, 0.25), sp = R.range(80, 150);
          ps.spawn(P.VAPOUR, R.range(-1, 1), -R.range(0, 2), Math.cos(a) * sp, Math.sin(a) * sp, R.range(0.8, 1.3), C[R.range(0, 1) < 0.6 ? 2 : 3], R.range(7.0, 12.0));
        }
      }
      for (const q of ps.list) { q.vx *= Math.pow(0.12, dt); q.vy = q.vy * Math.pow(0.25, dt) - 26 * dt; }
      ps.update(dt);
    },
    draw(p) { ps.draw(p); },
  };
}
