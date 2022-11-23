import math
from typing import List, Dict, Set

import mido

import pygame as pg

BITS_PER_SECOND = 30


class Note:
    def __init__(self, note, start, end, velocity=128):
        self.note = note
        self.start = math.floor(start)
        self.end = math.floor(end)
        self.velocity = velocity

    def __repr__(self):
        return f"{self.note} - s:{self.start} - e:{self.end}"

    def __str__(self):
        return self.__repr__()


def load_midi(path: str) -> mido.MidiFile:
    return mido.MidiFile(path)


def midi_to_notes(midi: mido.MidiFile) -> List[Note]:
    timing = 0.0
    pressed = {}
    res = []
    for msg in midi:
        timing += msg.time
        if msg.type == 'note_on' and msg.velocity > 0:
            pressed[msg.note] = timing, msg.velocity
        elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
            if msg.note in pressed.keys():
                start, velocity = pressed.pop(msg.note)
                res.append(Note(msg.note, start * BITS_PER_SECOND, timing * BITS_PER_SECOND, velocity))
    return res


def play_notes(notes: List[Note], sounds: Dict[int, pg.mixer.Sound], active: Set[int], frame: int) -> Set[int]:
    current = set()
    notes_played = []
    for note in notes:
        key = note.note
        start_pos = -note.start + frame
        length = note.end - note.start
        if start_pos < 0:
            break
        elif start_pos - length > 0:
            notes_played.append(note)
        else:
            current.add(key)
    for key in current.difference(active):
        sounds[key].play()
    for key in active.difference(current):
        sounds[key].fadeout(800)
    for note in notes_played:
        notes.remove(note)
    return current
