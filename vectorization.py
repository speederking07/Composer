from enum import Enum
from typing import List, Tuple, Iterator

from notes import Note, BITS_PER_SECOND, midi_to_notes, load_midi
import numpy as np
import matplotlib.pyplot as plt


class KeyStatus(Enum):
    PRESSED = 0
    HELD = 1
    RELEASED = 2


PianoStatus = List[KeyStatus]
Vector = np.ndarray[np.float32]

HELD_FACTOR_PER_SECOND = 0.2
HELD_FACTOR = HELD_FACTOR_PER_SECOND ** (1 / BITS_PER_SECOND)

RELEASED_FACTOR_PER_SECOND = 0.05
RELEASED_FACTOR = RELEASED_FACTOR_PER_SECOND ** (1 / BITS_PER_SECOND)


def apply_status(prev: Vector, status: PianoStatus) -> Vector:
    add_mat = np.array(list(map(lambda x: x == KeyStatus.PRESSED, status)), dtype=np.float32)
    mul_mat = np.array(list(
        map(lambda x: 0 if x == KeyStatus.PRESSED else (HELD_FACTOR if x == KeyStatus.HELD else RELEASED_FACTOR),
            status)), dtype=np.float32)
    return prev * mul_mat + add_mat


def status_generator(notes_list: List[Note]) -> Iterator[PianoStatus]:
    previous_active = set()
    for i in range(max(map(lambda x: x.end, notes_list))):
        notes_played = []
        result = [KeyStatus.RELEASED for _ in range(128)]
        active = set()
        for note in notes_list:
            key = note.note
            start_pos = -note.start + i
            length = note.end - note.start
            if start_pos < 0:
                break
            elif start_pos - length > 0:
                notes_played.append(note)
            else:
                if key in previous_active:
                    result[key] = KeyStatus.HELD
                else:
                    result[key] = KeyStatus.PRESSED
                active.add(key)
        for note in notes_played:
            notes_list.remove(note)
        previous_active = active
        yield result


def vectorized_notes(notes_list: List[Note]) -> Tuple[List[PianoStatus], List[Vector]]:
    current_vector = np.zeros(128, dtype=np.float32)
    vec_res = []
    status_res = []
    for stat in status_generator(notes_list):
        vec_res.append(current_vector)
        status_res.append(stat)
        current_vector = apply_status(current_vector, stat)
    return status_res, vec_res


if __name__ == "__main__":
    midi = load_midi("midi/again.mid")
    notes = midi_to_notes(midi)
    stats, vec = vectorized_notes(notes)
    y = np.array(vec)[:, 51]
    print(y.max())
    x = np.arange(0, len(vec))
    plt.plot(x, y)
    plt.show()

