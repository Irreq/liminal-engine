from __future__ import annotations
from typing import Generator, Callable, Dict, Tuple, Any, List, Set

"""This code is translated to python but originates from:

https://evannorton.github.io/acerolas-epic-color-palettes/colors.js

(https://github.com/evannorton/acerolas-epic-color-palettes)

From Acerolas epic OKLAB colortheme palette. All credits to the creators.
"""
import math
import random

# Colors
RGBColor = Tuple[int, int, int]
Color = RGBColor

BLACK: Color = (0, 0, 0)
WHITE: Color = (255, 255, 255)
RED: Color = (255, 0, 0)


def oklch_to_oklab(L, c, h):
    return [L, c * math.cos(h), c * math.sin(h)]


def lerp(min_val: float, max_val: float, t: float) -> float:
    return min_val + (max_val - min_val) * t


def random_range(min_val, max_val):
    return random.uniform(min_val, max_val)


def hsl_to_rgb(h: float, s: float, l: float) -> RGBColor:
    h = h % 1
    r, g, b = 0, 0, 0

    if s == 0:
        r = g = b = l  # achromatic
    else:

        def hue2rgb(p, q, t):
            if t < 0:
                t += 1
            if t > 1:
                t -= 1
            if t < 1 / 6:
                return p + (q - p) * 6 * t
            if t < 1 / 2:
                return q
            if t < 2 / 3:
                return p + (q - p) * (2 / 3 - t) * 6
            return p

        q = l * (1 + s) if l < 0.5 else l + s - l * s
        p = 2 * l - q

        r = hue2rgb(p, q, h + 1 / 3)
        g = hue2rgb(p, q, h)
        b = hue2rgb(p, q, h - 1 / 3)

    return (round(r * 255), round(g * 255), round(b * 255))


def hsv_to_rgb(h: float, s: float, v: float) -> RGBColor:
    r, g, b = 0, 0, 0

    i = int(h * 6)
    f = h * 6 - i
    p = v * (1 - s)
    q = v * (1 - f * s)
    t = v * (1 - (1 - f) * s)

    switch = {
        0: (v, t, p),
        1: (q, v, p),
        2: (p, v, t),
        3: (p, q, v),
        4: (t, p, v),
        5: (v, p, q),
    }

    r, g, b = switch.get(i % 6, (0, 0, 0))

    return (round(r * 255), round(g * 255), round(b * 255))


def oklab_to_linear_srgb(L, a, b):
    l_ = L + 0.3963377774 * a + 0.2158037573 * b
    m_ = L - 0.1055613458 * a - 0.0638541728 * b
    s_ = L - 0.0894841775 * a - 1.2914855480 * b

    l = l_ * l_ * l_
    m = m_ * m_ * m_
    s = s_ * s_ * s_

    return [
        +4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
        -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
        -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s,
    ]


def generate_oklch(HUE_MODE, settings):
    oklch_colors = []

    hue_base = settings["hueBase"] * 2 * math.pi
    hue_contrast = lerp(0.33, 1.0, settings["hueContrast"])

    chroma_base = lerp(0.01, 0.1, settings["saturationBase"])
    chroma_contrast = lerp(0.075, 0.125 - chroma_base, settings["saturationContrast"])
    chroma_fixed = lerp(0.01, 0.125, settings["fixed"])

    lightness_base = lerp(0.3, 0.6, settings["luminanceBase"])
    lightness_contrast = lerp(0.3, 1.0 - lightness_base, settings["luminanceContrast"])
    lightness_fixed = lerp(0.6, 0.9, settings["fixed"])

    chroma_constant = settings.get("saturationConstant", False)
    lightness_constant = not chroma_constant

    if HUE_MODE == "monochromatic":
        chroma_constant = False
        lightness_constant = False

    for i in range(settings["colorCount"]):
        linear_iterator = i / (settings["colorCount"] - 1)

        hue_offset = linear_iterator * hue_contrast * 2 * math.pi + (math.pi / 4)

        if HUE_MODE == "monochromatic":
            hue_offset *= 0.0
        elif HUE_MODE == "analagous":
            hue_offset *= 0.25
        elif HUE_MODE == "complementary":
            hue_offset *= 0.33
        elif HUE_MODE == "triadic complementary":
            hue_offset *= 0.66
        elif HUE_MODE == "tetradic complementary":
            hue_offset *= 0.75

        if HUE_MODE != "monochromatic":
            hue_offset += (random.random() * 2 - 1) * 0.01

        chroma = chroma_base + linear_iterator * chroma_contrast
        lightness = lightness_base + linear_iterator * lightness_contrast

        if chroma_constant:
            chroma = chroma_fixed
        if lightness_constant:
            lightness = lightness_fixed

        lab = oklch_to_oklab(lightness, chroma, hue_base + hue_offset)
        rgb = oklab_to_linear_srgb(lab[0], lab[1], lab[2])

        rgb[0] = round(max(0.0, min(rgb[0], 1.0)) * 255)
        rgb[1] = round(max(0.0, min(rgb[1], 1.0)) * 255)
        rgb[2] = round(max(0.0, min(rgb[2], 1.0)) * 255)

        oklch_colors.append(rgb)

    return oklch_colors


def randomColorSettings(n: int = 8) -> dict:
    settings = {
        "hueBase": random.random(),
        "hueContrast": random.random(),
        "saturationBase": random.random(),
        "saturationContrast": random.random(),
        "luminanceBase": random.random(),
        "luminanceContrast": random.random(),
        "fixed": random.random(),
        "saturationConstant": True,
        "colorCount": n,
    }
    return settings


settings = randomColorSettings()

# Fire
settings = {
    "hueBase": 0.1636667131884218,
    "hueContrast": 0.5206572795815642,
    "saturationBase": 0.99648981724148222,
    "saturationContrast": 0.49951444756622,
    "luminanceBase": 0.20380366851128384,
    "luminanceContrast": 0.9993941291960157,
    "fixed": 0.30948837760991355,
    "saturationConstant": True,
    "colorCount": 11,
}
generate_color_map = generate_oklch
# print(settings)
# settings = {
#     "hueBase": 0.14794220295472715,
#     "hueContrast": 0.3560270438861026,
#     "saturationBase": 0.45604965303415235,
#     "saturationContrast": 0.8903397812949359,
#     "luminanceBase": 0.49334904841149796,
#     "luminanceContrast": 0.5541572718274318,
#     "fixed": 0.5269127531174445,
#     "saturationConstant": True,
#     "colorCount": 8,
# }


# colors = generate_oklch("monochromatic", settings)
# print(colors)


class ColorManager:
    def __init__(self, n: int, settings: Dict[str, Any] = settings):
        self.n = n
        self.settings = settings
        self.colors: List[Color] = generate_color_map("monochromatic", self.settings)

    def computeRange(self, n: int) -> List[Color]:
        assert isinstance(n, int), "Must be an integer"
        assert n > 0, "Must be an positive integer"
        self.settings["colorCount"] = n
        self.colors = generate_color_map("monochromatic", self.settings)

        return self.colors
