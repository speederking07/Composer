from datetime import datetime
import math
from enum import IntFlag, IntEnum
from typing import Tuple

from mido import MidiFile, MidiTrack, MetaMessage, Message, second2tick

from notes import Note


class NoteLength(IntEnum):
    """
    Enum of add notes length used in music.
    """

    FULL = 2,
    HALF = 1,
    QUARTER = 0,  # as tempo is expressed in quoter notes unit
    EIGHTH = -1,
    SIXTEENTH = -2,
    THIRTY_SECOND = -3,


class AccordFlag(IntFlag):
    """
    Extra accord flags.
    """
    METRE_CHANGE = 1,
    TEMPO_CHANGE = 2,
    START = 4,
    END = 8,


class Accord:
    """
    Class representing single accord of music piece.
    """
    def __init__(self, metre: Tuple[int, int], tempo: float, notes: list[Tuple[int, NoteLength]], length: float, wait: float | None, flags: int):
        self.metre = metre
        self.tempo = tempo
        self.notes = notes
        self.length = length
        self.wait = wait
        self.flags = flags


def note_to_length(n: Note) -> NoteLength:
    """
    Calculates note length based on duration and tempo.
    """
    l = math.log2(n.length / n.tempo)
    for e in NoteLength:
        if l > float(e) - 0.5:
            return e
    return NoteLength.THIRTY_SECOND


def single_accord(notes: list[Note], next_note: Note | None, prev: float | None) -> Accord:
    """
    Function converting list of simultaneously played notes into single accord.
    """

    flag = AccordFlag(0)
    metre = notes[0].metre
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
        if next_note.metre != notes[0].metre:
            flag |= AccordFlag.METRE_CHANGE

    accord_notes = []
    for n in notes:
        if n.length > 0.01:
            accord_notes.append((n.note, note_to_length(n)))

    return Accord(metre, tempo, accord_notes, length, wait, flag)


def notes_to_accords(notes: list[Note]) -> list[Accord]:
    """
    Converts list of notes into list of accords played.
    """

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
    """
    Function converting list of accords into list of notes.
    """

    res = []
    time = 0.0
    for a in accords:
        for (note, length) in a.notes:
            res.append(Note(note, time, 2 ** length * a.tempo, a.tempo, a.metre, 64))
        time += a.length * a.tempo

    return res


def save_accords(accords: list[Accord], basename: str | None = None, name: str | None = None, path: str = 'output'):
    """
    Procedure saving accords as midi file.

    :param accords: Accords of track to be saved.
    :param basename: Base name of track.
    :param name: Full name of track.
    :param path: Path to folder where track should be saved.
    """
    mid = MidiFile()
    track = MidiTrack()
    mid.tracks.append(track)

    if name is None:
        if basename is None:
            name = f"composer-{datetime.now().strftime('%Y_%m_%d_%H_%M_%S')}"
        else:
            name = f"{basename}-{datetime.now().strftime('%Y_%m_%d_%H_%M_%S')}"

    time = 0.0
    msgs = []
    prev_tempo = None
    prev_metre = None

    track.append(MetaMessage('track_name', name=name, time=0))
    track.append(MetaMessage('instrument_name', name='python_composer', time=0))

    for a in accords:
        if a.tempo != prev_tempo:
            prev_tempo = a.tempo
            msgs.append((time, a.tempo, MetaMessage('set_tempo', tempo=int(a.tempo * 1000000))))
        if a.metre != prev_metre:
            prev_metre = a.metre
            msgs.append((time, a.tempo, MetaMessage('time_signature', numerator=a.metre[0], denominator=a.metre[1])))
        for (note, length) in a.notes:
            msgs.append((time, a.tempo, Message('note_on', note=note, velocity=64)))
            msgs.append((time + 2 ** length * a.tempo, a.tempo, Message('note_off', note=note, velocity=0)))
        time += a.length * a.tempo

    msgs.append((time, prev_tempo, MetaMessage('end_of_track')))

    prev = 0.0
    for (time, tempo, msg) in sorted(msgs, key=lambda x: x[0]):
        msg.time = int(second2tick(time - prev, mid.ticks_per_beat, tempo * 1000000))
        track.append(msg)
        prev = time

    mid.save(path + '/' + name + '.mid')