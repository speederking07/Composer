import os
from datetime import datetime
from enum import Enum
from typing import List, Tuple, Iterator
import json

from mido import MidiFile, MidiTrack, MetaMessage, Message, second2tick, bpm2tempo

from notes import Note, BITS_PER_SECOND, midi_to_notes, load_midi
import numpy as np


class KeyStatus(Enum):
    PRESSED = 0
    HELD = 1
    RELEASED = 2


PianoStatus = List[KeyStatus]
Vector = np.ndarray[np.float32]

HELD_FACTOR_PER_SECOND = 0.4
HELD_FACTOR = HELD_FACTOR_PER_SECOND ** (1 / BITS_PER_SECOND)

RELEASED_FACTOR_PER_SECOND = 0.2
RELEASED_FACTOR = RELEASED_FACTOR_PER_SECOND ** (1 / BITS_PER_SECOND)


def apply_status(prev: Vector, status: PianoStatus) -> Vector:
    add_mat = np.array(list(map(lambda x: x == KeyStatus.PRESSED, status)), dtype=np.float32)
    mul_mat = np.array(list(
        map(lambda x: 0 if x == KeyStatus.PRESSED else (HELD_FACTOR if x == KeyStatus.HELD else RELEASED_FACTOR),
            status)), dtype=np.float32)
    return prev * mul_mat + add_mat


def status_generator(notes_list: List[Note]) -> Iterator[PianoStatus]:
    previous_active = set()
    notes_list = sorted(notes_list, key=lambda x: x.start)
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


def load_folder(folder: str) -> Tuple[List[PianoStatus], List[Vector], List[str]]:
    stats, vectors, names = [], [], []
    for path, _, files in os.walk(folder):
        for name in files:
            if name.endswith(".mid"):
                midi = load_midi(os.path.join(path, name))
                stat, vec = vectorized_notes(midi_to_notes(midi))
                stats += stat
                vectors += vec
                names += [name] * len(vec)
    return stats, vectors, names


def save_data_to_file(filename: str, stats: List[PianoStatus], vec: List[Vector], names: List[str]):
    with open(filename, 'w', encoding='utf-8') as f:
        for i in range(len(stats)):
            f.write(f"{list(map(lambda x: x.value, stats[i]))};{list(vec[i])};{names[i]}\n")


def load_data_from_file(filename: str) -> Tuple[List[PianoStatus], List[Vector], List[str]]:
    stats, vectors, names = [], [], []
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            split = line.split(';')
            stats.append(list(map(lambda x: KeyStatus(x), json.loads(split[0]))))
            vectors.append(np.array(json.loads(split[1]), dtype=np.float32))
            names.append(split[2])
    return stats, vectors, names


def save_stats_as_midi(stats: List[PianoStatus],
                       name: str = f"composer-{datetime.now().strftime('%Y_%m_%d_%H_%M_%S')}", path: str = 'output'):
    mid = MidiFile()
    track = MidiTrack()
    mid.tracks.append(track)

    tempo = bpm2tempo(2400)
    ticks_per_step = second2tick(1 / BITS_PER_SECOND, mid.ticks_per_beat, tempo)
    time_from_prev = 0
    track.append(MetaMessage('track_name', name=name, time=0))
    track.append(MetaMessage('instrument_name', name='python_composer', time=0))
    track.append(MetaMessage('set_tempo', tempo=tempo, time=0))

    prev = [KeyStatus.RELEASED for _ in range(128)]
    for stat in stats:
        for i in range(128):
            if stat[i] == KeyStatus.PRESSED:
                track.append(Message('note_on', note=i, velocity=127, time=int(time_from_prev * ticks_per_step)))
                time_from_prev = 0
            elif stat[i] == KeyStatus.RELEASED and prev[i] == KeyStatus.HELD:
                track.append(Message('note_off', note=i, velocity=0, time=int(time_from_prev * ticks_per_step)))
                time_from_prev = 0
        time_from_prev += 1
        prev = stat
    track.append(MetaMessage('end_of_track', time=int(time_from_prev * ticks_per_step)))

    mid.save(path + '/' + name + '.mid')


if __name__ == '__main__':
    if KeyStatus.PRESSED == KeyStatus(0):
        print(1)
