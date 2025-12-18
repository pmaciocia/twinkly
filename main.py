
import random
import xled
import time
import struct
import signal
import uuid
import os
import sys
from colorist import ColorRGB
from points import random_point, random_grower
import pygame as pg
import numpy as np

ip = '192.168.1.44'
hw = 'e8:31:cd:6d:8e:7d'
default_layout = list(range(125, 250)) + list(range(124,-1,-1))

on = struct.pack(">BBBB", 255, 255, 255, 255)
off = struct.pack(">BBBB", 0, 0, 0, 0)

# rainbow colors
rainbow_colors = [
    struct.pack(">BBBB", 0, 255, 0, 0),     # Red
    struct.pack(">BBBB", 0, 255, 127, 0),   # Orange
    struct.pack(">BBBB", 0, 255, 255, 0),   # Yellow
    struct.pack(">BBBB", 0, 0, 255, 0),     # Green
    struct.pack(">BBBB", 0, 0, 0, 255),     # Blue
    struct.pack(">BBBB", 0, 75, 0, 130),    # Indigo
    struct.pack(">BBBB", 0, 148, 0, 211)    # Violet
]

rainbow_rgb = [
    (255, 0, 0),     # Red
    (255, 127, 0),   # Orange
    (255, 255, 0),   # Yellow
    (0, 255, 0),     # Green
    (0, 0, 255),     # Blue
    (75, 0, 130),    # Indigo
    (148, 0, 211)    # Violet
]

def create_movie(d: xled.ControlInterface, frames: int, fps: int, name: str, uid: str = None, gen = None):
    if uid is None:
        uid = str(uuid.uuid4()).upper()

    if gen is None:
        gen = gen_frame(default_layout)

    # Collect frames into a list of numpy arrays (copy each frame so
    # generators that reuse a buffer don't corrupt previous frames).
    frames_list = []

    count = 0
    frame = next(gen, None)
    while frame is not None and count < frames:
        print(f"Generating frame {count+1}/{frames}")
        frames_list.append(frame.copy())
        count += 1
        frame = next(gen, None)

    if count == 0:
        return

    movie_array = np.stack(frames_list)  # shape (count, 250, 4)

    d.set_mode("off")
    r = d.set_movies_new(name, uid, "rgbw_raw", 250, count, fps)
    print(r.data)
    # Send raw bytes to the device
    r = d.set_movies_full(movie_array.tobytes())
    print(r.data)

    movies = d.get_movies().data["movies"]
    new_movie = list((m for m in movies if m["unique_id"] == uid))[0]
    d.set_movies_current(new_movie["id"])
    d.set_mode("movie")

def run_movie(d: xled.ControlInterface, gen):
    d.set_mode("rt")

    for frame in gen:
        d.set_rt_frame_socket(version=3,frame=frame.tobytes())
        print_tree(frame)
        time.sleep(0.2)

    d.set_mode("off")


def interrupt_handler(device):
    device.set_mode("off")
    exit(0)

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
            if (count-width) < i < (count+width):
                r,g,b,w = map(lambda x: int(x * (1 - dist)), color)
            else:
                r,g,b,w = (0,0,0,0)
            
            frame[y] = [w, r, g, b]

        count = count+dir
        if  count >= upper or count <= lower:
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

def get_client():
    d = xled.ControlInterface(ip, hw)
    return d

def main():
    uid = "CA3BB670-E598-4F67-A328-F271C25626AC"
    d = get_client()

    led_layout = d.get_led_layout().data['coordinates']
    el = list(enumerate(led_layout))
    el.sort(key=lambda x: x[1]['x'])
    l = [x[0] for x in el]
    
    gen = gen_sweep(l, width=100, max_loops=sys.maxsize)

    # signal.signal(signal.SIGINT, lambda s, f: interrupt_handler(d))
    # create_movie(d=d, frames=1000, fps=250, name="sweep", gen=gen)
    # run_movie(d, gen=gen)
    display_tree(led_layout, gen=gen)


def print_tree(frame):
    os.system('clear')
    for y in range(25):
        row = ""
        for x in range(10):
            _, r, g, b = frame[x]
            if (r, g, b) == (0, 0, 0):
                row += ". "
                continue
            else:
                color = ColorRGB(r, g, b)
                row += f"{color}# {color.OFF}"
        print(row)
    print("\n")

def display_tree(led_layout, gen):
    pg.init()
    window_w, window_h = 512, 512
    bg = (30,30,50)

    window = pg.display.set_mode((window_w, window_h))
    pg.display.set_caption("Twinkly Visualiser")
    window.fill(bg)

    layout = led_layout[:]
    min_x, max_x = min(c['x'] for c in layout), max(c['x'] for c in layout)
    min_y, max_y = min(c['y'] for c in layout), max(c['y'] for c in layout)

    dx = max_x - min_x or 1
    dy = max_y - min_y or 1

    for c in layout:
        c['x'] = ((c['x'] - min_x) / dx)
        c['y'] = ((c['y'] - min_y) / dy)

    # visual parameters
    led_radius = 6
    pad = led_radius * 3  # padding so LEDs near edges do not get clipped

    # create a drawing surface that includes padding around the normalized coordinates
    surf_w = window_w + pad * 2
    surf_h = window_h + pad * 2
    surface = pg.Surface((surf_w, surf_h))

    # initial view transform
    zoom = 1.0

    rect = surface.get_rect(center=window.get_rect().center)

    clock = pg.time.Clock()

    running = True
    while running:
        sw = (surf_w - pad * 2)
        sh = (surf_h - pad * 2)
        for frame in gen:
            surface.fill(bg)

            # draw LEDs with padding offset so the full circle can be visible at edges
            for x in range(len(layout)):
                c = layout[x]
                _, r, g, b = frame[x]

                cx = int(pad + c['x'] * sw)
                cy = int(pad + (1 - c['y']) * sh)

                # draw background halo for better visibility when colors are dark
                if (r, g, b) == (0, 0, 0):
                    color = (20, 20, 20)
                else:
                    color = (r, g, b)

                pg.draw.circle(surface, color, (cx, cy), led_radius)

            # scale the surface according to current zoom and blit using the rect for panning
            scaled_size = (max(1, int(surf_w * zoom)), max(1, int(surf_h * zoom)))
            scaled_win = pg.transform.scale(surface, scaled_size)

            # preserve the current center when zooming
            prev_center = rect.center
            rect = scaled_win.get_rect()
            rect.center = prev_center

            window.fill(bg)
            window.blit(scaled_win, rect)
            pg.display.flip()

            for e in pg.event.get():
                if e.type == pg.QUIT or (e.type == pg.KEYUP and e.key == pg.K_ESCAPE):
                    print("Exiting...")
                    running = False
                elif e.type == pg.KEYUP:
                    # zoom in/out with + and -
                    if e.key == pg.K_EQUALS or e.key == pg.K_PLUS:
                        zoom *= 1.1
                    elif e.key == pg.K_MINUS or e.key == pg.K_UNDERSCORE:
                        zoom *= 0.9

                    # panning with arrow keys
                    elif e.key == pg.K_LEFT:
                        rect.x += 20
                    elif e.key == pg.K_RIGHT:
                        rect.x -= 20
                    elif e.key == pg.K_UP:
                        rect.y += 20
                    elif e.key == pg.K_DOWN:
                        rect.y -= 20

            clock.tick(500)

            if not running:
                break

if __name__ == "__main__":
    main()
