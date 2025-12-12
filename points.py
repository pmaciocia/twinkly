from dataclasses import dataclass
import random


@dataclass(kw_only=True)
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

        r = int(itensity * self.r)
        g = int(itensity * self.g)
        b = int(itensity * self.b)
        w = int(itensity * self.w)

        return (r,g,b,w)
    def __str__(self):
        return f"Point(pos={self.pos}, speed={self.speed}, size={self.size}, r={self.r}, g={self.g}, b={self.b}, w={self.w})"



@dataclass(kw_only=True)
class Grower(Point):
    growing: bool = True

    def update(self):
        if self.growing:
            self.size += self.speed
            if self.size > 20:
                self.growing = False
        else:
            self.size -= self.speed
            if self.size < 2:
                self.growing = True


def random_grower():
    return Grower(
        pos=random.uniform(0, 250),
        speed=random.uniform(0.1, 1),
        size=random.uniform(2, 5),
        r=random.choice([0,1]),
        g=random.choice([0,1]),
        b=random.choice([0,1]),
        w=random.choice([0,1]),
    )


def dist(x, y):
    d = min(abs(x-y), abs(x+250-y), abs(x-250-y))
    return d


def random_point():
    return Point(
        pos=random.uniform(0, 250),
        speed=random.uniform(-5, 5),
        size=random.uniform(2, 20),
        r=random.choice([0,1]),
        g=random.choice([0,1]),
        b=random.choice([0,1]),
        w=random.choice([0,1]),
    )