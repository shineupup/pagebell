#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 Pagebell 图标：蓝青渐变圆角底 + 白色声波点（与界面同一套视觉）"""
import os
from PIL import Image, ImageDraw, ImageFilter

OUT_DIR = r'C:\Users\Administrator\WorkBuddy\2026-09-19-15-16-07\output'
os.makedirs(OUT_DIR, exist_ok=True)

S = 1024
A = (77, 150, 255)      # #4D96FF
B = (46, 196, 182)      # #2EC4B6


def lerp(c1, c2, t):
    return tuple(round(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def make_base():
    grad = Image.new('RGBA', (S, S))
    px = grad.load()
    for y in range(S):
        for x in range(S):
            t = (x + y) / (2 * (S - 1))
            r, g, b = lerp(A, B, t)
            px[x, y] = (r, g, b, 255)
    mask = Image.new('L', (S, S), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, S - 1, S - 1),
                                           radius=int(S * 0.22), fill=255)
    base = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    base.paste(grad, (0, 0), mask)
    return base


def add_glow(img):
    glow = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse(
        (int(S * -0.15), int(S * -0.25), int(S * 0.75), int(S * 0.55)),
        fill=(255, 255, 255, 62))
    glow = glow.filter(ImageFilter.GaussianBlur(S * 0.09))
    out = Image.alpha_composite(img, glow)
    mask = Image.new('L', (S, S), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, S - 1, S - 1),
                                           radius=int(S * 0.22), fill=255)
    out.putalpha(Image.composite(out.getchannel('A'),
                                 Image.new('L', (S, S), 0), mask))
    return out


def draw_mark(img):
    layer = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    c = S / 2
    r0 = S * 0.115
    d.ellipse((c - r0, c - r0, c + r0, c + r0), fill=(255, 255, 255, 255))
    for r, w, alpha in ((S * 0.235, int(S * 0.042), 225),
                        (S * 0.345, int(S * 0.036), 130)):
        box = (c - r, c - r, c + r, c + r)
        d.arc(box, start=32, end=148, fill=(255, 255, 255, alpha), width=w)
        d.arc(box, start=212, end=328, fill=(255, 255, 255, alpha), width=w)
    return Image.alpha_composite(img, layer)


def main():
    img = draw_mark(add_glow(make_base()))
    png = os.path.join(OUT_DIR, '图标_当前版本.png')
    img.resize((512, 512), Image.LANCZOS).save(png)
    ico = os.path.join(OUT_DIR, 'icon.ico')
    img.save(ico, format='ICO',
             sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64),
                    (128, 128), (256, 256)])
    print('png ->', png)
    print('ico ->', ico, os.path.getsize(ico))


if __name__ == '__main__':
    main()
