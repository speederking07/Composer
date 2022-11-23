import mido
import pygame as pg

from composer import compose_music, statuses_to_notes
from keyboard import get_sound_keys
from notes import midi_to_notes, play_notes, BITS_PER_SECOND, load_midi
from vectorization import vectorized_notes
from visualisation import draw_falling_notes, draw_piano

pg.init()
pg.mixer.init()
pg.mixer.set_num_channels(80)
WIDTH = 52 * 35
HEIGHT = 800
screen = pg.display.set_mode((WIDTH, HEIGHT))
timer = pg.time.Clock()

if __name__ == '__main__':
    midi = load_midi("midi/again.mid")
    notes = midi_to_notes(midi)

    stats, vec = vectorized_notes(notes)
    comp_notes = compose_music(vec, stats, length=30*BITS_PER_SECOND)
    # comp_notes = statuses_to_notes(stats)

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
