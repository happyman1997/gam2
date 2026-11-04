"""Smooth value noise for ground textures."""
import numpy as np
from PIL import Image


def value_noise(w, h, cell, seed):
    rng = np.random.default_rng(seed)
    small = rng.random((h // cell + 3, w // cell + 3)).astype(np.float32)
    im = Image.fromarray((small * 255).astype(np.uint8), "L").resize(((w // cell + 3) * cell, (h // cell + 3) * cell), Image.BICUBIC)
    return np.asarray(im, dtype=np.float32)[:h, :w] / 255.0
