
import xled
import time
import uuid
import numpy as np
import random
from io import BytesIO

from display import display_tree, print_tree
from gen import gen_frame, gen_sweep, gen_rainbow, gen_sweep_2, gen_perlin_rainbow, random_xmas_tree

ip = '192.168.1.44'
hw = 'e8:31:cd:6d:8e:7d'
default_layout = list(range(125, 250)) + list(range(124,-1,-1))

def create_movie(frames: int, gen = None):
    if gen is None:
        gen = gen_frame(default_layout)

    frames_list = []

    count = 0
    frame = next(gen, None)
    while frame is not None and count < frames:
        frames_list.append(frame.copy())
        count += 1
        frame = next(gen, None)

    if count == 0:
        return

    return np.stack(frames_list)  # shape (count, 250, 4)

def upload_movie(d: xled.ControlInterface, name: str, movie_array: np.ndarray, fps: int):
    uid = str(uuid.uuid4()).upper()

    frames = movie_array.shape[0]
    leds = movie_array.shape[1]
    r = d.set_mode("off")
    print(r.data)
    r = d.set_movies_new(name, uid, "rgbw_raw", leds, frames, fps)
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

    c = 0 
    for frame in gen:
        b = BytesIO(frame.tobytes())
        d.set_rt_frame_socket(version=3,frame=b)
        time.sleep(0.02)
        c += 1
        print(c)

    d.set_mode("off")


def interrupt_handler(device):
    device.set_mode("off")
    exit(0)

def get_client():
    d = xled.ControlInterface(ip, hw)
    return d

def find_client():
    dis = xled.discover.discover()
    return xled.ControlInterface(host=dis.ip_address, hw_address=dis.hw_address)

def sort_layout(led_layout, axis='x'):
    """Sort LED layout by specified axis (x, y, or z)"""
    el = list(enumerate(led_layout))
    el.sort(key=lambda x: x[1].get(axis, 0))
    return [x[0] for x in el]

def sort_by_plane(led_layout, normal=(0, 0, 1), point=(0, 0, 0)):
    """Sort LED layout by distance along a plane defined by normal vector and point"""
    el = list(enumerate(led_layout))
    normal = np.array(normal)
    point = np.array(point)
    
    def distance_to_plane(coord):
        coord_vec = np.array([coord.get('x', 0), coord.get('y', 0), coord.get('z', 0)])
        return np.dot(coord_vec - point, normal)
    
    el.sort(key=lambda x: distance_to_plane(x[1]))
    return [x[0] for x in el]

def main():
    uid = "CA3BB670-E598-4F67-A328-F271C25626AC"
    
    # d = find_client()
    # led_layout = d.get_led_layout().data['coordinates']

    led_layout = random_xmas_tree()
        

    
    # normal = (random.uniform(-1,1), random.uniform(-1,1), random.uniform(-1,1))
    l = sort_by_plane(led_layout, normal=(0, 1, 0), point=(0, 0, 0))
    # l = sort_layout(led_layout, axis='x')
    # l = default_layout[:]
    # random.shuffle(l)
    # l = random.shuffle(default_layout[:])
    
    # gen = gen_sweep_2(led_layout, width=50, max_loops=sys.maxsize, axis=0)
    # gen = gen_perlin_rainbow(l, scale=0.05)

    gen = gen_sweep(sort_by_plane(led_layout, normal=(0,1,0), point=(0,0,0)), width=30, max_loops=2)
    movie_a = create_movie(frames=632, gen=gen)

    gen = gen_sweep(sort_by_plane(led_layout, normal=(1,0,0), point=(0,0,0)), width=30, max_loops=2)
    movie_b = create_movie(frames=632, gen=gen)

    # movie = np.concatenate((movie_a, movie_b), axis=0)
    movie = np.maximum(movie_a, movie_b)

    # upload_movie(d=d, name="sweep", movie_array=movie, fps=100)

    # signal.signal(signal.SIGINT, lambda s, f: interrupt_handler(d))
    # upload_movie(d=d, name="sweep", movie_array=create_movie(frames=1000, gen=gen), fps=250)
    # run_movie(d, gen=movie)
    display_tree(led_layout[:], gen=movie, fps=250)
    # display_tree(led_layout[:], gen=limit_gen(movie, 1264), fps=250)


def limit_gen(gen, max_frames):
    count = 0
    for frame in gen:
        if count >= max_frames:
            break
        yield frame
        count += 1

if __name__ == "__main__":
    main()
