from typing import Tuple, Dict, List, Iterable

import pygame as pg

pg.mixer.init()

__all__ = ['piano_notes', 'get_sound_keys', 'is_white', 'position_of_note', 'into_blacks_and_whites', 'black_pos']

piano_notes = ['A0', 'Bb0', 'B0', 'C1', 'Db1', 'D1', 'Eb1', 'E1', 'F1', 'Gb1', 'G1', 'Ab1',
               'A1', 'Bb1', 'B1', 'C2', 'Db2', 'D2', 'Eb2', 'E2', 'F2', 'Gb2', 'G2', 'Ab2',
               'A2', 'Bb2', 'B2', 'C3', 'Db3', 'D3', 'Eb3', 'E3', 'F3', 'Gb3', 'G3', 'Ab3',
               'A3', 'Bb3', 'B3', 'C4', 'Db4', 'D4', 'Eb4', 'E4', 'F4', 'Gb4', 'G4', 'Ab4',
               'A4', 'Bb4', 'B4', 'C5', 'Db5', 'D5', 'Eb5', 'E5', 'F5', 'Gb5', 'G5', 'Ab5',
               'A5', 'Bb5', 'B5', 'C6', 'Db6', 'D6', 'Eb6', 'E6', 'F6', 'Gb6', 'G6', 'Ab6',
               'A6', 'Bb6', 'B6', 'C7', 'Db7', 'D7', 'Eb7', 'E7', 'F7', 'Gb7', 'G7', 'Ab7',
               'A7', 'Bb7', 'B7', 'C8']

white_and_blacks = []
black_pos = []
w = 1
b = -1
for n in piano_notes:
    if 'b' in n:
        white_and_blacks.append(b)
        black_pos.append(w - 2)
        b -= 1
    else:
        white_and_blacks.append(w)
        w += 1

keys_color = {i + 21: white_and_blacks[i] for i in range(len(piano_notes))}
keys = {i + 21: pg.mixer.Sound(f'notes/{piano_notes[i]}.wav') for i in range(len(piano_notes))}


def into_blacks_and_whites(list_of_keys: Iterable[int]) -> Tuple[List[int], List[int]]:
    whites = list(map(lambda x: x - 1, filter(lambda x: x > 0, [keys_color[i] for i in list_of_keys])))
    blacks = list(map(lambda x: -x - 1, filter(lambda x: x < 0, [keys_color[i] for i in list_of_keys])))
    return whites, blacks


def get_sound_keys() -> Dict[int, pg.mixer.Sound]:
    return keys


def is_white(note: int) -> bool:
    return keys_color[note] > 0


def position_of_note(note: int) -> Tuple[int, int]:
    key_pos = keys_color[note]
    if key_pos > 0:
        return (key_pos - 1) * 35 + 2, 31
    else:
        black_p = black_pos[-key_pos - 1]
        return 26 + black_p * 35, 18
