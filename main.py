import mido
import pygame as pg
from keyboard import get_sound_keys
from notes import midi_to_notes, play_notes, BITS_PER_SECOND
from visualisation import draw_falling_notes, draw_piano

pg.init()
pg.mixer.init()
pg.mixer.set_num_channels(80)
WIDTH = 52 * 35
HEIGHT = 800
screen = pg.display.set_mode((WIDTH, HEIGHT))
timer = pg.time.Clock()

if __name__ == '__main__':
    # notes = [Note(i + 21, 0.5 * i, 0.5 * i + 0.5) for i in range(0, len(keys_color))]
    notes = midi_to_notes(mido.MidiFile('midi/again.mid'))
    notes_display = sorted(notes, key=lambda x: x.start)
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
