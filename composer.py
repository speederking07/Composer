from typing import List, Tuple, Iterator

from scipy.spatial.distance import cdist

from accord import Accord, accords_to_notes, AccordFlag, save_accords
from convolutions import get_gaussian_curve, maxvolve
from notes import Note
from vectorization import Vector, apply_accord, empty_vector

import numpy as np

SELECTION_CURVE_PARAM = 40
CONVOLUTION = get_gaussian_curve(32, 5)
PANIC_THRESHOLD = SELECTION_CURVE_PARAM * np.exp(- 0.2 * SELECTION_CURVE_PARAM)

LONG_IMPORTANCE = 0.2
SHORT_IMPORTANCE = 0.6
CUMULATIVE_IMPORTANCE = 0.2


def select_bit(current_state: Vector, known_vec) -> Tuple[int, float]:
    """
    Based on current state of composed track and provided data set of known accords, selects
    randomly accord to be played with probability depending on similarity to current state.
    """

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
    """
    Calculates maxvolve on state vector.
    """

    r0 = maxvolve(x[0], CONVOLUTION)
    r1 = maxvolve(x[1], CONVOLUTION)
    r2 = maxvolve(x[2], CONVOLUTION)
    return np.array([r0, r1, r2])


def music_generator(known_vec: List[Vector], known_accords: List[Accord], known_names: List[str])\
        -> Iterator[Accord]:
    """
    Based on provided data set composes consecutive accords.
    """

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
            tempo = np.random.lognormal(np.log(accord_played.tempo), 0.05)
        accord_played.tempo = tempo
        if AccordFlag.TEMPO_CHANGE in accord_played.flags or accord_played.length > 8.0:
            tempo = None
        accord_played.length = min(accord_played.length, 8.0)
        pressed, vector = apply_accord(accord_played, pressed, vector)
        yield accord_played


def compose_music(known_vec: List[Vector], known_accords: List[Accord], known_names: List[str],
                  length: float | None = None, base_name: str = "composer") -> List[Note]:
    """
    Function returning list of composed notes of track of specified length. In addition,
    saves copy of composed track as midi file with specified based name.

    :param known_vec: Known vectors from data set.
    :param known_accords: Known accords from data set.
    :param known_names: Known names of tracks from data set.
    :param length: Length in seconds of composed track.
    :param base_name: Base name of tracks used in file naming.
    :return: List of composed notes
    """

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
    save_accords(res, basename=base_name.replace("/", "-"))
    return accords_to_notes(res)

