from typing import List, Callable

from metrics import euclidean
from notes import Note
from vectorization import PianoStatus, KeyStatus, Vector

import numpy as np


def statuses_to_notes(status_list: List[PianoStatus]) -> List[Note]:
    pressed = [-1 for _ in range(128)]
    res = []
    for i in range(len(status_list)):
        for key in range(128):
            if status_list[i][key] == KeyStatus.PRESSED:
                if pressed[key] != -1:
                    res.append(Note(key, pressed[key], i))
                pressed[key] = i
            elif status_list[i][key] == KeyStatus.RELEASED:
                if pressed[key] != -1:
                    res.append(Note(key, pressed[key], i))
                    pressed[key] = -1
    return res


def compose_bit(current_state: Vector, known_vec: List[Vector], known_plays: List[PianoStatus],
                 metric: Callable[[List[Vector], Vector], np.ndarray[np.float32]] = euclidean) -> PianoStatus:
    dist = metric(known_vec, current_state)
    return known_plays[np.argmin(dist)]
