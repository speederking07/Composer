from typing import Callable
from vectorization import Vector


def music_pseudo(silence_preference: float) -> Callable[[Vector, Vector], float]:
    return lambda x, y: music_pseudo_func(x, y, silence_preference)


def music_pseudo_func(x: Vector, y: Vector, silence_preference: float) -> float:
    dist = 0
    for i in range(len(x)):
        d = x[i] - y[i]
        if d > 0:
            dist += d * silence_preference
        else:
            dist += -d * (1 - silence_preference)
    return dist
