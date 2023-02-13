import os
import random
from typing import List, Tuple


from accord import Accord, notes_to_accords
from notes import Note, midi_to_notes, load_midi
import numpy as np

# Each vector is made of 3 "sub-vectors":
# * Long memory - with smaller decreasing factor
# * Short memory - with high decreasing factor
# * Cumulative memory - with increment memory (adding constant every time button is pressed)
Vector = np.ndarray[np.float32]

LONG_HELD_FACTOR = 0.8
LONG_RELEASED_FACTOR = 0.6

SHORT_HELD_FACTOR = 0.45
SHORT_RELEASED_FACTOR = 0.25

CUMULATIVE_INCREMENT = 0.25
CUMULATIVE_HELD_FACTOR = 0.8
CUMULATIVE_RELEASED_FACTOR = 0.6


def empty_vector() -> Vector:
    """
    Creates an empty vector.
    """

    return np.zeros((3, 128), dtype=np.float32)


def copy_vector(v: Vector) -> Vector:
    """
    Copies vector.

    :param v: Vector to be copied
    """

    return v.copy()


def apply_accord(accord: Accord, pressed: np.ndarray, v: Vector) -> Tuple[np.ndarray, Vector]:
    """
    Calculates new vector based on previous one and currently played accord
    :param accord: Accord currently played.
    :param pressed: Vector of holding down keys.
    :param v: Previous vector.
    :return: A Pair of holding down keys and new vector
    """
    new_notes = map(lambda note: (note[0], 2 ** note[1]), accord.notes)
    length = accord.length

    for (n, l) in new_notes:
        v[0][n] = 1
        v[1][n] = 1
        v[2][n] = min(v[2][n] + CUMULATIVE_INCREMENT, 1)
        pressed[n] = l

    held = np.amin(np.array([pressed, length * np.ones(128)]), axis=0)
    released = length - held

    v[0] = v[0] * LONG_HELD_FACTOR ** held * LONG_RELEASED_FACTOR ** released
    v[1] = v[1] * SHORT_HELD_FACTOR ** held * SHORT_RELEASED_FACTOR ** released
    v[2] = v[2] * CUMULATIVE_HELD_FACTOR ** held * CUMULATIVE_RELEASED_FACTOR ** released

    new_pressed = np.amax(np.array([pressed - length, np.zeros(128)]), axis=0)

    return new_pressed, v


def vectorize_notes(notes_list: List[Note]) -> Tuple[List[Accord], List[Vector]]:
    """
    Function converting list of `Notes` of single track into list of corresponding
    accords and vectors for each accord played.

    :param notes_list: Notes to be converted.
    :return: Pair containing list of accords and list of corresponding vectors
    """

    vector = empty_vector()
    vec_res = []
    status_res = []
    pressed = np.zeros(128)
    for accord in notes_to_accords(notes_list):
        vec_res.append(copy_vector(vector))
        status_res.append(accord)
        pressed, vector = apply_accord(accord, pressed, vector)
    return status_res, vec_res


def load_folder(folder: str, fraction: float = 1.0) -> Tuple[List[Accord], List[Vector], List[str]]:
    """
    Procedure loading content of single folder and vectorizing found tracks in it.

    :param folder: Folder containing tracks to be vectorized.
    :param fraction: Fraction of tracks to vectorize (for performance optimization).
    :return: Tuple of accords, vectors and names of tracks found in folder.
    """

    accords, vectors, names = [], [], []
    for path, _, files in os.walk(folder):
        for name in files:
            if name.endswith(".mid") and random.uniform(0.0, 1.0) <= fraction:
                try:
                    midi = load_midi(os.path.join(path, name))
                    accord, vec = vectorize_notes(midi_to_notes(midi))
                    accords += accord
                    vectors += vec
                    names += [name] * len(vec)
                except IOError:
                    print(f"Corrupted {path}/{name}")
                except:
                    print(f"Corrupted {path}/{name}")
    return accords, vectors, names
