import os
from enum import Enum
from typing import List, Tuple, Dict


from accord import Accord, notes_to_accords
from notes import Note, midi_to_notes, load_midi
import numpy as np

# Long memory, short memory, cumulative memory
Vector = Tuple[np.ndarray[np.float32], np.ndarray[np.float32], np.ndarray[np.float32]]

LONG_HELD_FACTOR = 0.95
LONG_RELEASED_FACTOR = 0.7

SHORT_HELD_FACTOR = 0.5
SHORT_RELEASED_FACTOR = 0.3

CUMULATIVE_INCREMENT = 0.25
CUMULATIVE_HELD_FACTOR = 0.6
CUMULATIVE_RELEASED_FACTOR = 0.4


def empty_vector() -> Vector:
    return np.zeros(128, dtype=np.float32), np.zeros(128, dtype=np.float32), np.zeros(128, dtype=np.float32)


def copy_vector(v: Vector) -> Vector:
    return v[0].copy(), v[1].copy(), v[2].copy()


def apply_accord(accord: Accord, pressed: Dict[int, float], v: Vector) -> Tuple[Dict[int, float], Vector]:
    new_notes = map(lambda note: (note[0], 2 ** note[1]), accord.notes)
    length = accord.length

    for (n, l) in new_notes:
        v[0][n] = 1
        v[1][n] = 1
        v[2][n] = min(v[2][n] + CUMULATIVE_INCREMENT, 1)
        pressed[n] = l

    for i in range(128):
        if i in pressed:
            held = min(length, pressed[i])
            released = length - held
            v[0][i] *= LONG_HELD_FACTOR ** held * LONG_RELEASED_FACTOR ** released
            v[1][i] *= SHORT_HELD_FACTOR ** held * SHORT_RELEASED_FACTOR ** released
            v[2][i] *= CUMULATIVE_HELD_FACTOR ** held * CUMULATIVE_RELEASED_FACTOR ** released
            if released > 0.01:
                pressed[i] -= length
            if pressed[i] <= 0.01:
                pressed.pop(i)
        else:
            v[0][i] *= LONG_RELEASED_FACTOR ** length
            v[1][i] *= SHORT_RELEASED_FACTOR ** length
            v[2][i] *= CUMULATIVE_RELEASED_FACTOR ** length

    return pressed, v


def vectorize_notes(notes_list: List[Note]) -> Tuple[List[Accord], List[Vector]]:
    vector = empty_vector()
    vec_res = []
    status_res = []
    pressed = {}
    for accord in notes_to_accords(notes_list):
        vec_res.append(copy_vector(vector))
        status_res.append(accord)
        pressed, vector = apply_accord(accord, pressed, vector)
    return status_res, vec_res


def load_folder(folder: str) -> Tuple[List[Accord], List[Vector], List[str]]:
    accords, vectors, names = [], [], []
    for path, _, files in os.walk(folder):
        for name in files:
            if name.endswith(".mid"):
                midi = load_midi(os.path.join(path, name))
                accord, vec = vectorize_notes(midi_to_notes(midi))
                accords += accord
                vectors += vec
                names += [name] * len(vec)
    return accords, vectors, names
