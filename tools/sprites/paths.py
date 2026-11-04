"""Where fonts are read from and where rendered sheets are written."""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "fonts")
OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)


def font(name):
    return os.path.join(FONTS, name)


def out(name):
    return os.path.join(OUT, name)
