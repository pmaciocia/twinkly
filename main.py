
import xled
import time
import io
import struct
import signal
from dataclasses import dataclass

ip = '192.168.1.44'
hw = 'e8:31:cd:6d:8e:7d'
layout = list(range(125, 251)) + list(range(125,-1,-1))

on = struct.pack(">BBBB", 255, 255, 255, 255)
red = struct.pack(">BBBB", 0, 255, 0, 0)
green = struct.pack(">BBBB", 0, 0, 255, 0)
blue = struct.pack(">BBBB", 0, 0, 0, 255)
off = struct.pack(">BBBB", 0, 0, 0, 0)

@dataclass
class Point:
    pos: float
    speed: float
    size: float
    r: float
    g: float
    b: float
    w: float

    def update(self):
        self.pos = (self.pos + self.speed) % 250
    
    def dist(self, pos):
        itensity = 255 * max(0, 1 - dist(int(self.pos), pos)/self.size)

        r = int(itensity * self.r) % 255
        g = int(itensity * self.g) % 255
        b = int(itensity * self.b) % 255
        w = int(itensity * self.w) % 255

        return (r,g,b,w)

def main():
    d = xled.ControlInterface(ip, hw)
    d.set_mode("rt")

    signal.signal(signal.SIGINT, lambda s, f: interrupt_handler(s, f, d))
    for frame in gen_frame():
        d.set_rt_frame_socket(version=3,frame=frame)
        time.sleep(0.1)

    d.set_mode("off")

def interrupt_handler(signal, frame, device):
    print("Interrupted")
    device.set_mode("off")
    exit(0)

def random_point():
    import random
    return Point(
        pos=random.uniform(0, 250),
        speed=random.uniform(-5, 5),
        size=random.uniform(2, 20),
        r=random.choice([0,1]),
        g=random.choice([0,1]),
        b=random.choice([0,1]),
        w=random.choice([0,1]),
    )

def gen_frame():
    points = [random_point() for _ in range(8)]
    with io.BytesIO() as output:
        
        while True:
            for point in points:
                point.update()

            for iy, y in enumerate(layout):
                pos = y*4 % (250*4)
                output.seek(pos)

                r,g,b,w = tuple(map(sum, zip(*(p.dist(iy) for p in points))))
                val = struct.pack(">BBBB", w, r, g, b)
                output.write(val)

            yield output

def dist(x, y):
    return abs(x-y)
    
if __name__ == "__main__":
    main()