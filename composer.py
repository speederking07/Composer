from itertools import islice
from typing import List, Tuple, Iterator

from scipy.spatial.distance import cdist

from accord import Accord, accords_to_notes, AccordFlag, save_accords
from convolutions import get_gaussian_convolution, maxvolve
from notes import Note
from vectorization import Vector, apply_accord, empty_vector

import numpy as np

SELECTION_CURVE_PARAM = 50
CONVOLUTION = get_gaussian_convolution(32, 4)
PANIC_THRESHOLD = SELECTION_CURVE_PARAM * np.exp(- 0.2 * SELECTION_CURVE_PARAM)

LONG_IMPORTANCE = 0.5
SHORT_IMPORTANCE = 0.3
CUMULATIVE_IMPORTANCE = 0.2


def select_bit(current_state: Vector, known_vec) -> Tuple[int, float]:
    dist_long = cdist(np.array(known_vec[:, 0]), np.array([current_state[0]]), metric='chebyshev')[:, 0]
    dist_short = cdist(np.array(known_vec[:, 1]), np.array([current_state[1]]), metric='chebyshev')[:, 0]
    dist_cumulative = cdist(np.array(known_vec[:, 2]), np.array([current_state[2]]), metric='chebyshev')[:, 0]

    added_dist = LONG_IMPORTANCE * dist_long + SHORT_IMPORTANCE * dist_short + CUMULATIVE_IMPORTANCE * dist_cumulative

    dist = SELECTION_CURVE_PARAM * np.exp(-added_dist * SELECTION_CURVE_PARAM)

    sum_of_dist = np.sum(dist)
    print(f"sum: {sum_of_dist}; max: {np.max(dist)}")

    rand = np.random.uniform(0.0, sum_of_dist)
    selected = np.argmax(np.cumsum(dist) > rand)

    return selected, dist[selected]


def convolve(x: Vector) -> Vector:
    r0 = maxvolve(x[0], CONVOLUTION)
    r1 = maxvolve(x[1], CONVOLUTION)
    r2 = maxvolve(x[2], CONVOLUTION)
    return np.array([r0, r1, r2])


def music_generator(known_vec: List[Vector], known_accords: List[Accord], known_names: List[str])\
        -> Iterator[Accord]:
    vector = empty_vector()
    known_vec = np.array(list(map(convolve, known_vec)))
    print("convoluted")
    prev = 0
    tempo = None
    pressed = np.zeros(128)
    while True:
        selected, confidence = select_bit(convolve(vector), known_vec)
        if confidence < PANIC_THRESHOLD:
            print('panic')
            selected = (prev + 1) % len(known_vec)
        print(known_names[selected], selected)
        prev = selected
        accord_played = known_accords[selected]
        if tempo is None:
            tempo = np.random.lognormal(accord_played.tempo, 0.1)
        accord_played.tempo = tempo
        if AccordFlag.TEMPO_CHANGE in accord_played.flags or accord_played.length > 12.0:
            tempo = None
        accord_played.length = min(accord_played.length, 12.0)
        pressed, vector = apply_accord(accord_played, pressed, vector)
        yield accord_played


def compose_music(known_vec: List[Vector], known_accords: List[Accord], known_names: List[str],
                  length: float | None = None) -> List[Note]:
    mg = music_generator(known_vec, known_accords, known_names)
    time = 0.0
    res = []
    for accord in mg:
        res.append(accord)
        time += accord.tempo * accord.length
        if length is None and accord.flags in AccordFlag.END:
            break
        if length is not None and time > length:
            break
    save_accords(res)
    return accords_to_notes(res)

