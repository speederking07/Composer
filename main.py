from datetime import datetime

import mido
import pygame as pg

from accord import notes_to_accords, accords_to_notes
from composer import compose_music
from keyboard import get_sound_keys
from notes import midi_to_notes, play_notes, BITS_PER_SECOND, load_midi
from vectorization import load_folder
from visualisation import draw_falling_notes, draw_piano

pg.init()
pg.mixer.init()
pg.mixer.set_num_channels(80)
WIDTH = 52 * 35
HEIGHT = 800
screen = pg.display.set_mode((WIDTH, HEIGHT))
timer = pg.time.Clock()

if __name__ == '__main__':
    # midi = load_midi("output/composer-2023_01_11_15_06_35.mid")
    # notes = midi_to_notes(midi)
    # comp_notes = notes
    # accords = notes_to_accords(notes)
    # processed = accords_to_notes(accords)

    accords, vec, names = load_folder('midi/classic')
    print("ripped")
    comp_notes = compose_music(vec, accords, names, length=3 * 60)

    notes_display = sorted(comp_notes, key=lambda x: x.start)
    notes_sound = notes_display.copy()
    run = True
    frame = 400
    active = set()
    while run:
        timer.tick(BITS_PER_SECOND)
        screen.fill('gray')
        active = play_notes(notes_sound, get_sound_keys(), active, frame - 500)
        draw_falling_notes(screen, notes_display, frame)
        draw_piano(active, screen)
        pg.display.flip()
        frame += 1
        for event in pg.event.get():
            if event.type == pg.QUIT:
                run = False
