import struct
import random
import math

import numpy as np
from points import random_point
from noise import pnoise1

rainbow_rgb = [
    (255, 0, 0),     # Red
    (255, 127, 0),   # Orange
    (255, 255, 0),   # Yellow
    (0, 255, 0),     # Green
    (0, 0, 255),     # Blue
    (75, 0, 130),    # Indigo
    (148, 0, 211)    # Violet
]

def interpolate_rainbow(t):
    """
    Interpolate between rainbow colors.
    
    Args:
        t: Float between 0 and 1 representing position in the rainbow
    
    Returns:
        Tuple of (r, g, b) values
    """
    t = t % 1.0
    idx = t * (len(rainbow_rgb) - 1)
    lower_idx = int(idx)
    upper_idx = min(lower_idx+1, len(rainbow_rgb)-1)
    blend = idx - lower_idx
    
    r1, g1, b1 = rainbow_rgb[lower_idx]
    r2, g2, b2 = rainbow_rgb[upper_idx]
    
    r = int(r1 * (1 - blend) + r2 * blend)
    g = int(g1 * (1 - blend) + g2 * blend)
    b = int(b1 * (1 - blend) + b2 * blend)
    
    return (r, g, b)

def gen_sweep(layout, width=20, color=(255,0,0,0), max_loops=2):
    """Sweep a colored band across the given index layout.

    Intensity is computed based on distance from the sweep center and clamped
    to the 0-255 range so it cannot overflow the uint8 frame buffer.
    """
    point = -width
    dir = 1
    loops = 0
    size = len(layout)
    lower, upper = -(width+5), size + (width+5)
    frame = np.zeros((size, 4), dtype=np.uint8)

    while loops < max_loops:
        for i, y in enumerate(layout):
            if (point - width) < i < (point + width):
                # Compute a normalized intensity [0..1] based on distance inside the band
                dist = abs(point - i) / max(1.0, float(width))
                intensity = max(0.0, 1.0 - dist)
                # Apply intensity and clamp into 0..255
                r, g, b, w = [int(max(0, min(255, int(x * intensity)))) for x in color]
            else:
                r, g, b, w = (0, 0, 0, 0)

            frame[y] = [w, r, g, b]

        point = point + dir
        if point >= upper or point <= lower:
            loops += 1
            dir = -dir

        yield frame


def gen_sweep_2(points_list, width=20, max_loops=2, axis=0):
    """
    Generate frames with a sweeping plane that colors LEDs based on distance.
    
    Args:
        points_list: List of dicts with 3D coordinates {'x': ..., 'y': ..., 'z': ...}
        width: Width of the sweep gradient
        max_loops: Number of complete sweeps
        axis: Axis along which to sweep ('x', 'y', or 'z')
    """
    dir = 1
    loops = 0
    size = len(points_list)
    coords = np.array([[p['x'], p['y'], p['z']] for p in points_list])
    # Normalize coordinates so min is 0 and max is array length
    axis_map = {'x': 0, 'y': 1, 'z': 2}
    axis_idx = axis_map.get(axis, 0) if isinstance(axis, str) else int(axis)
    min_coord = coords[:, axis_idx].min()
    max_coord = coords[:, axis_idx].max()
    denom = (max_coord - min_coord)
    if denom == 0:
        coords[:, axis_idx] = np.zeros_like(coords[:, axis_idx])
    else:
        coords[:, axis_idx] = (coords[:, axis_idx] - min_coord) / denom * (size - 1)

    lower, upper = -(width + 5), size + (width + 5)
    plane = -width
    frame = np.zeros((size, 4), dtype=np.uint8)

    while loops < max_loops:
        for i, point in enumerate(coords):
            coord = point[axis_idx]
            if (plane - width) < coord < (plane + width):
                # distance-based rainbow index, keep values bounded
                dist = abs(plane - coord) / max(1.0, float(width))
                ci = int(dist * (2 * len(rainbow_rgb))) % len(rainbow_rgb)
                r, g, b = rainbow_rgb[ci]
                w = 0
            else:
                r, g, b, w = (0, 0, 0, 0)

            frame[i] = [w, r, g, b]

        plane += dir
        if plane >= upper or plane <= lower:
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
    size = max(layout) + 1 if len(layout) > 0 else 0
    frame = np.zeros((size, 4), dtype=np.uint8)
    offset = 0
    while True:
        for x in range(len(layout)):
            pos = layout[x]
            r, g, b = rainbow_rgb[(x + offset) % len(rainbow_rgb)]
            w = random.randint(0, 125)
            frame[pos] = [w, r, g, b]

        yield frame
        offset = (offset + 1) % max(1, size)

def gen_perlin_rainbow(layout, scale=0.1, speed=0.01):
    """
    Generate frames with rainbow patterns using Perlin noise.
    
    Args:
        layout: List of LED positions
        scale: Perlin noise scale factor
        speed: how fast the noise offset moves
    """

    size = max(layout) + 1 if len(layout) > 0 else 0
    frame = np.zeros((size, 4), dtype=np.uint8)
    offset = 0.0

    while True:
        for x in range(len(layout)):
            pos = layout[x]
            # Use Perlin noise to smoothly vary between rainbow colors
            noise_val = pnoise1(x * scale + offset, repeat=max(1, size))
            # Map noise (-1 to 1) to color index (0 to len(rainbow_rgb)-1)
            r, g, b = interpolate_rainbow((noise_val + 1) / 2)
            frame[pos] = [0, r, g, b]

        yield frame
        offset += speed


def random_xmas_tree(n_leds=250, height=1.0, base_radius=1.0, jitter=0.02, seed=None):
    """
    Generate a random 3D layout shaped like a Christmas tree.

    Args:
        n_leds: total number of LEDs to generate
        height: height of the tree (arbitrary units)
        base_radius: radius of the tree base
        trunk_fraction: fraction of LEDs assigned to the trunk (0..1)
        trunk_height: fraction of total height occupied by the trunk (0..1)
        trunk_radius: radius of trunk jitter
        jitter: random displacement added to each LED (to make layout less regular)
        seed: optional PRNG seed for reproducibility

    Returns:
        List[dict]: each dict has 'x','y','z' coordinates
    """
    if seed is not None:
        random.seed(seed)


    leds = []
    bias = 0.8 * height / 10.0  # leave some space at the bottom

    for _ in range(n_leds):
        # bias density towards the lower part of the foliage
        y = bias + (random.random() ** 0.8 ) * (height-bias)

        r_at_y = base_radius * (1 - (y / height))
        theta = random.random() * 2 * math.pi
        rad = r_at_y * (random.random() ** 0.5)

        x = rad * math.cos(theta) + random.uniform(-jitter, jitter)
        z = rad * math.sin(theta) + random.uniform(-jitter, jitter)
        leds.append({'x': x, 'y': y, 'z': z})

    random.shuffle(leds)
    return leds


if __name__ == "__main__":
    # quick demo when run as a script
    import pprint
    t = random_xmas_tree(100, height=1.0, base_radius=0.6, seed=42)
    print(f"Generated tree with {len(t)} LEDs (sample):")
    pprint.pprint(t[:5])