import math
from typing import Set, List

from keyboard import position_of_note, into_blacks_and_whites, black_pos, is_white
from notes import Note, BITS_PER_SECOND
import pygame as pg

__all__ = ['draw_falling_notes', 'draw_piano']


def draw_falling_notes(screen: pg.Surface, notes: List[Note], frame):
    visible_whites = []
    visible_blacks = []
    notes_played = []
    for note in notes:
        key = note.note
        start_pos = math.floor(-note.start * BITS_PER_SECOND + frame)
        length = math.floor(note.length * BITS_PER_SECOND)
        if start_pos < 0:
            break
        if start_pos - length > screen.get_height():
            notes_played.append(note)
        if is_white(key):
            visible_whites.append((key, start_pos, length))
        else:
            visible_blacks.append((key, start_pos, length))
    for (key, start, length) in visible_whites:
        (lx, key_len) = position_of_note(key)
        pg.draw.rect(screen, 'white', [lx, start - length, key_len, length], 0, 2)
    for (key, start, length) in visible_blacks:
        (lx, key_len) = position_of_note(key)
        pg.draw.rect(screen, 'black', [lx, start - length, key_len, length], 0, 2)
    for note in notes_played:
        notes.remove(note)
    notes_played.clear()


def draw_piano(pressed: Set[int], screen: pg.Surface):
    whites, blacks = into_blacks_and_whites(pressed)
    white_rects = []
    for i in range(52):
        rect = pg.draw.rect(screen, 'white', [i * 35, screen.get_height() - 300, 35, 300], 0, 2)
        white_rects.append(rect)
        pg.draw.rect(screen, 'black', [i * 35, screen.get_height() - 300, 35, 300], 2, 2)

    for i in whites:
        pg.draw.rect(screen, 'green', [i * 35 + 2, screen.get_height() - 298, 31, 296], 0, 0)

    for i in black_pos:
        pg.draw.rect(screen, 'black', [23 + (i * 35), screen.get_height() - 300, 24, 200], 0, 2)

    for i in blacks:
        k = black_pos[i]
        pg.draw.rect(screen, 'green', [26 + (k * 35), screen.get_height() - 298, 18, 196], 0, 2)
