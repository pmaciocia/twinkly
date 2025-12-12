
import random
import xled
import time
import io
import struct
import signal
import uuid
import os
import sys
from colorist import ColorRGB
from points import random_point, random_grower
import pygame as pg

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

    with io.BytesIO() as output:
        count = 0
        frame = next(gen)
        while frame is not None and count < frames:
            val = frame.getvalue()
            output.write(val)
            count += 1
            frame = next(gen, None)
        
        output.seek(0)

        d.set_mode("off")
        r = d.set_movies_new(name, uid, "rgbw_raw", 250, count, fps)
        print(r.data)
        r = d.set_movies_full(output)
        print(r)

        movies = d.get_movies().data["movies"]
        new_movie = list((m for m in movies if m["unique_id"] == uid))[0]
        d.set_movies_current(new_movie["id"])
        d.set_mode("movie")

def run_movie(d: xled.ControlInterface, gen):
    d.set_mode("rt")

    for frame in gen:
        d.set_rt_frame_socket(version=3,frame=frame)
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
    with io.BytesIO() as output:
        while loops < max_loops:
            for i, y in enumerate(layout):
                pos = y*4 % (250*4)
                output.seek(pos)
                
                if (count - width) < i < (count+width):
                    r,g,b,w = color
                else:
                    r,g,b,w = (0,0,0,0)
                
                val = struct.pack(">BBBB", w, r, g, b)
                output.write(val)
            
            count = count+dir
            if count >= 250 + (width+5)  or count <= -(width+5):
                dir = -dir
                loops += 1


            yield output
    
    


def gen_frame(layout):
    # points = [random_grower() for _ in range(10)]
    points = [random_point() for _ in range(10)]
    with io.BytesIO() as output:
        while True:
            for point in points:
                point.update()

            for iy, y in enumerate(layout):
                pos = y*4 % (250*4)
                output.seek(pos)

                r,g,b,w = tuple(map(sum, zip(*(p.dist(iy) for p in points))))
                val = struct.pack(">BBBB", w%255, r%255, g%255, b%255)
                output.write(val)

            yield output

def gen_rainbow(layout):
    with io.BytesIO() as output:
        offset = 0 
        while True:
            for x in range(len(layout)):
                pos = layout[x]*4
                output.seek(pos)
                # val = rainbow_colors[(x+offset) % len(rainbow_colors)]
                val = struct.pack(">BBBB", random.randint(0,125), *rainbow_rgb[(x+offset) % len(rainbow_rgb)])

                output.write(val)

            yield output
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
    

    # signal.signal(signal.SIGINT, lambda s, f: interrupt_handler(d))
    # create_movie(d=d, frames=1000, fps=200, name="sweep", layout=l, gen=gen_sweep(l, width=30))
    # run_movie(d, gen=gen_rainbow(l))
    # run_movie(d, gen_frame(default_layout))
    # run_movie(d, gen_frame(default_layout))
    # run_movie(d, gen=gen_sweep(l))

    # for frame in gen_sweep(l):
        # print_tree(frame)
        # time.sleep(0.01)

    # display_tree(led_layout, gen=gen_sweep(l, width=30,max_loops=sys.maxsize))
    display_tree(led_layout, gen=gen_rainbow(default_layout))



def print_tree(frame):
    os.system('clear')
    for y in range(25):
        row = ""
        for x in range(10):
            pos = (y*10 + x)*4
            frame.seek(pos)
            _,r,g,b = struct.unpack(">BBBB", frame.read(4))
            if (r,g,b) == (0,0,0):
                row += ". "
                continue
            else:
                color = ColorRGB(r, g, b)
                row += f"{color}# {color.OFF}"
        print(row)
    print("\n")

def display_tree(led_layout, gen):
    pg.init()
    w,h = 512, 512

    screen = pg.display.set_mode((w, h))
    pg.display.set_caption("pygame Stars Example")
    screen.fill((20,20,40))

    min_x, max_x = min(c['x'] for c in led_layout), max(c['x'] for c in led_layout)
    min_y, max_y = min(c['y'] for c in led_layout), max(c['y'] for c in led_layout)

    for c in led_layout:
        c['x'] = (w-20) * ((c['x'] - min_x) / (max_x - min_x))
        c['y'] = (h-20) * ((c['y'] - min_y) / (max_y - min_y))

    clock = pg.time.Clock()

    running = True
    while running:
        for frame in gen:
            for ix, x in enumerate(range(250)):
                pos = x*4
                c = led_layout[ix]
                frame.seek(pos)
                _,r,g,b = struct.unpack(">BBBB", frame.read(4))

                x,y = c['x'], h-c['y']
                pg.draw.circle(screen, (r,g,b), (x,y), 5)

            pg.display.update()
            for e in pg.event.get():
                if e.type == pg.QUIT or (e.type == pg.KEYUP and e.key == pg.K_ESCAPE):
                    print("Exiting...")
                    running = False
            clock.tick(50)
            time.sleep(0.25)

            if not running:
                break

        
    pg.quit() 

if __name__ == "__main__":
    main()
