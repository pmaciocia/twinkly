
import random
import xled
import time
import signal
import uuid
import sys
import numpy as np

from display import display_tree, print_tree
from points import random_grower, random_point
from gen import gen_frame, gen_sweep, gen_rainbow

ip = '192.168.1.44'
hw = 'e8:31:cd:6d:8e:7d'
default_layout = list(range(125, 250)) + list(range(124,-1,-1))

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

def get_client():
    d = xled.ControlInterface(ip, hw)
    return d

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
    d = get_client()


    led_layout = d.get_led_layout().data['coordinates']
    
    # normal = (random.uniform(-1,1), random.uniform(-1,1), random.uniform(-1,1))
    # l = sort_by_plane(led_layout, normal=normal, point=(0, 0, 0))
    l = sort_layout(led_layout, axis='x')
    
    gen = gen_sweep(l, width=100, max_loops=sys.maxsize)

    # signal.signal(signal.SIGINT, lambda s, f: interrupt_handler(d))
    # create_movie(d=d, frames=1000, fps=250, name="sweep", gen=gen)
    # run_movie(d, gen=gen)
    display_tree(led_layout[:], gen=gen)


if __name__ == "__main__":
    main()
