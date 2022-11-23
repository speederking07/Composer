from typing import List, Callable

from metrics import euclidean
from notes import Note, load_midi, midi_to_notes, BITS_PER_SECOND
from vectorization import PianoStatus, KeyStatus, Vector, vectorized_notes, apply_status

import numpy as np

SELECTION_CURVE_PARAM = 0.00005  # less means less noise


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


def compose_bit(current_state: Vector, known_vec: List[Vector],
                metric: Callable[[List[Vector], Vector], np.ndarray[np.float32]] = euclidean) -> int:
    dist = SELECTION_CURVE_PARAM / (metric(known_vec, current_state) + SELECTION_CURVE_PARAM)

    # dist = np.vectorize(lambda x: 0 if x < 0.1 else x)(dist)  # TODO: Remove
    sum_of_dist = np.sum(dist)
    print(np.sum(dist > 0.1))

    selected = np.random.uniform(0.0, sum_of_dist)

    return np.argmax(np.cumsum(dist) > selected)


def force_holding(keys_played: PianoStatus, vector: Vector) -> PianoStatus:
    keys_played = keys_played.copy()
    for i in range(len(vector)):
        if vector[i] > 0.70:
            keys_played[i] = KeyStatus.HELD
    return keys_played


def compose_music(known_vec: List[Vector], known_stats: List[PianoStatus], length=3 * 60 * BITS_PER_SECOND,
                  metric: Callable[[List[Vector], Vector], np.ndarray[np.float32]] = euclidean) -> List[Note]:
    vector = np.zeros(128, dtype=np.float32)
    states = []
    for _ in range(length):
        selected = compose_bit(vector, known_vec, metric)
        keys_played = known_stats[selected]
        keys_played = force_holding(keys_played, vector)
        vector = apply_status(vector, keys_played)
        states.append(keys_played)
    return statuses_to_notes(states)


if __name__ == "__main__":
    midi = load_midi("midi/again.mid")
    notes = midi_to_notes(midi)
    stats, vec = vectorized_notes(notes)
    v = vec[1006]
    print(v)
    print(compose_bit(v, vec))
