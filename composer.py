from itertools import islice
from typing import List, Tuple, Iterator

from scipy.spatial.distance import cdist

from convolutions import get_gaussian_convolution, maxvolve
from notes import Note,  BITS_PER_SECOND
from vectorization import PianoStatus, KeyStatus, Vector, apply_status, save_stats_as_midi

import numpy as np

SELECTION_CURVE_PARAM = 50
CONVOLUTION = get_gaussian_convolution(21, 4)
PANIC_THRESHOLD = SELECTION_CURVE_PARAM * np.exp(- 0.25 * SELECTION_CURVE_PARAM)


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


def compose_bit(current_state: Vector, known_vec: List[Vector], metric) -> Tuple[int, float]:
    dist = SELECTION_CURVE_PARAM * np.exp(
        -cdist(np.array(known_vec), np.array([current_state]), metric=metric)[:, 0] * SELECTION_CURVE_PARAM)

    sum_of_dist = np.sum(dist)
    print(f"sum: {sum_of_dist}; max: {np.max(dist)}")

    rand = np.random.uniform(0.0, sum_of_dist)
    selected = np.argmax(np.cumsum(dist) > rand)

    return selected, dist[selected]


def force_holding(keys_played: PianoStatus, vector: Vector) -> PianoStatus:
    keys_played = keys_played.copy()
    for i in range(len(vector)):
        if vector[i] > 0.88:
            keys_played[i] = KeyStatus.HELD
    return keys_played


def convolve(x: Vector) -> Vector:
    return maxvolve(x, CONVOLUTION)


def music_generator(known_vec: List[Vector], known_stats: List[PianoStatus], known_names: List[str])\
        -> Iterator[PianoStatus]:
    vector = np.zeros(128, dtype=np.float32)
    known_vec = list(map(convolve, known_vec))
    print("convoluted")
    prev = 0
    while True:
        selected, confidence = compose_bit(convolve(vector), known_vec, metric='chebyshev')
        if confidence < PANIC_THRESHOLD:
            print('panic')
            selected = (prev + 1) % len(known_vec)
        print(known_names[selected])
        prev = selected
        keys_played = known_stats[selected]
        keys_played = force_holding(keys_played, vector)
        vector = apply_status(vector, keys_played)
        yield keys_played


def compose_music(known_vec: List[Vector], known_stats: List[PianoStatus], known_names: List[str],
                  length=3 * 60 * BITS_PER_SECOND) -> List[Note]:
    mg = music_generator(known_vec, known_stats, known_names)
    states = list(islice(mg, length))
    save_stats_as_midi(states)
    return statuses_to_notes(states)

