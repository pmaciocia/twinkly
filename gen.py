import struct
import random

import numpy as np
from points import random_point

rainbow_rgb = [
    (255, 0, 0),     # Red
    (255, 127, 0),   # Orange
    (255, 255, 0),   # Yellow
    (0, 255, 0),     # Green
    (0, 0, 255),     # Blue
    (75, 0, 130),    # Indigo
    (148, 0, 211)    # Violet
]


def gen_sweep(layout, width=20, color=(255,0,0,0), max_loops=2):
    count = -width
    dir = 1
    loops = 0
    size = len(layout)
    lower, upper = -(width+5), size + (width+5)
    frame = np.zeros((size,4), dtype=np.uint8)
    while loops < max_loops:
        for i, y in enumerate(layout):
            dist = abs(i - count)/100.0
            c = rainbow_rgb[int(len(rainbow_rgb) * dist) % len(rainbow_rgb)]
            if (count-width) < i < (count+width):
                # r,g,b,w = map(lambda x: int(x * (1 - dist)), color)
                (r,g,b),w = c,0
                # (r,g,b),w = map(lambda x: int(x * (1 - dist)), c),255
            else:
                r,g,b,w = (0,0,0,0)

            frame[y] = [w, r, g, b]

        count = count+dir
        if count >= upper or count <= lower:
            loops += 1
            dir = -dir

        yield frame


def gen_frame(layout):
    # points = [random_grower() for _ in range(10)]
    frame = np.zeros((250,4), dtype=np.uint8)
    points = [random_point() for _ in range(10)]
    while True:
        for point in points:
            point.update()

        for iy, y in enumerate(layout):
            r,g,b,w = tuple(map(sum, zip(*(p.dist(iy) for p in points))))
            frame[y] = [w%255, r%255, g%255, b%255]
        yield frame


def gen_rainbow(layout):
    frame = np.zeros((250,4), dtype=np.uint8)
    offset = 0
    while True:
        for x in range(len(layout)):
            pos = layout[x]
            r,g,b,w =  *rainbow_rgb[(x+offset) % len(rainbow_rgb)], random.randint(0,125)
            frame[pos] = [w, r, g, b]

        yield frame
        offset = (offset + 1) % 250