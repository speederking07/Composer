from datetime import datetime
import math
from enum import IntFlag, auto, IntEnum
from typing import Tuple

from mido import MidiFile, MidiTrack, MetaMessage, Message, second2tick

from notes import Note


class NoteLength(IntEnum):
    FULL = 2,
    HALF = 1,
    QUARTER = 0,
    EIGHTH = -1,
    SIXTEENTH = -2,
    THIRTY_SECOND = -3,


class AccordFlag(IntFlag):
    METRO_CHANGE = 1,
    TEMPO_CHANGE = 2,
    START = 4,
    END = 8,


class Accord:
    def __init__(self, metro: Tuple[int, int], tempo: float, notes: list[Tuple[int, NoteLength]], length: float, wait: float | None, flags: int):
        self.metro = metro
        self.tempo = tempo
        self.notes = notes
        self.length = length
        self.wait = wait
        self.flags = flags


def note_to_length(n: Note) -> NoteLength:
    l = math.log2(n.length / n.tempo)
    for e in NoteLength:
        if l > float(e) - 0.5:
            return e
    return NoteLength.THIRTY_SECOND


def single_accord(notes: list[Note], next_note: Note | None, prev: float | None) -> Accord:
    flag = AccordFlag(0)
    metro = notes[0].metro
    tempo = notes[0].tempo
    wait = None
    length = 1.0

    if next_note is None:
        flag = AccordFlag.END
        wait = (notes[0].start - prev) / notes[0].tempo
    elif prev is None:
        flag = AccordFlag.START
        length = (next_note.start - notes[0].start) / notes[0].tempo
    else:
        length = (next_note.start - notes[0].start) / notes[0].tempo
        wait = (notes[0].start - prev) / notes[0].tempo
        if next_note.tempo != notes[0].tempo:
            flag |= AccordFlag.TEMPO_CHANGE
        if next_note.metro != notes[0].metro:
            flag |= AccordFlag.METRO_CHANGE

    accord_notes = []
    for n in notes:
        if n.length > 0.01:
            accord_notes.append((n.note, note_to_length(n)))

    return Accord(metro, tempo, accord_notes, length, wait, flag)


def notes_to_accords(notes: list[Note]) -> list[Accord]:
    prev = None
    accord_notes = []
    result = []

    for n in sorted(notes, key=lambda x: x.start):
        dist = 0 if len(accord_notes) == 0 else (n.start - accord_notes[0].start) / accord_notes[0].tempo
        if dist < 0.1:
            accord_notes.append(n)
        else:
            result.append(single_accord(accord_notes, n, prev))
            prev = accord_notes[0].start
            accord_notes = [n]

    result.append(single_accord(accord_notes, None, prev))

    return result


def accords_to_notes(accords: list[Accord]) -> list[Note]:
    res = []
    time = 0.0
    for a in accords:
        for (note, length) in a.notes:
            res.append(Note(note, time, 2 ** length * a.tempo, a.tempo, a.metro, 64))
        time += a.length * a.tempo

    return res


def save_accords(accords: list[Accord], name: str | None = None, path: str = 'output'):
    mid = MidiFile()
    track = MidiTrack()
    mid.tracks.append(track)

    if name is None:
        name = f"composer-{datetime.now().strftime('%Y_%m_%d_%H_%M_%S')}"

    time = 0.0
    msgs = []
    prev_tempo = None

    track.append(MetaMessage('track_name', name=name, time=0))
    track.append(MetaMessage('instrument_name', name='python_composer', time=0))

    for a in accords:
        if a.tempo != prev_tempo:
            prev_tempo = a.tempo
            msgs.append((time, a.tempo, MetaMessage('set_tempo', tempo=int(a.tempo * 1000000))))
        for (note, length) in a.notes:
            msgs.append((time, a.tempo, Message('note_on', note=note, velocity=64)))
            msgs.append((time + 2 ** length * a.tempo, a.tempo, Message('note_off', note=note, velocity=0)))
        time += a.length * a.tempo

    msgs.append((time, prev_tempo, MetaMessage('end_of_track')))

    prev = 0.0
    for (time, tempo, msg) in sorted(msgs, key=lambda x: x[0]):
        msg.time = second2tick(time - prev, mid.ticks_per_beat, tempo * 1000000)
        track.append(msg)
        prev = time

    mid.save(path + '/' + name + '.mid')