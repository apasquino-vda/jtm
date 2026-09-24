import random
import time
import threading
import math

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle

# --- MUSICAL DATA ---
roots = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B']
qualities = ['maj7', 'm7', '7']
all_jazz_chords = [f"{root}{quality}" for root in roots for quality in qualities]

major_251_sequences = [
    ("C", "D", "G", "C"), ("Db", "Eb", "Ab", "Db"), ("D", "E", "A", "D"),
    ("Eb", "F", "Bb", "Eb"), ("E", "F#", "B", "E"), ("F", "G", "C", "F"),
    ("Gb", "Ab", "Db", "Gb"), ("G", "A", "D", "G"), ("Ab", "Bb", "Eb", "Ab"),
    ("A", "B", "E", "A"), ("Bb", "C", "F", "Bb"), ("B", "C#", "F#", "B")
]

state = {
    "mode": None,
    "is_step_mode": False,
    "bpm": 30,
    "running": True,
    "current_chord": "Ready",
    "progression_queue": [],
    "loop_id": 0
}

# --- AUDIO ---
AUDIO_AVAILABLE = False
try:
    import pygame
    import numpy as np
    pygame.mixer.pre_init(44100, -16, 1, 512)
    pygame.mixer.init()
    
    sample_rate = 44100
    duration = 0.03
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    wave = np.sin(2 * math.pi * 1200 * t) * np.exp(-t * 200)
    audio_data = (wave * 32767).astype(np.int16)
    
    TICK_SOUND = pygame.sndarray.make_sound(audio_data)
    AUDIO_AVAILABLE = True
except Exception:
    AUDIO_AVAILABLE = False

def play_tick_sound():
    if AUDIO_AVAILABLE:
        try:
            TICK_SOUND.play()
        except Exception:
            pass

def get_countdown_dots(step):
    return "[" + "  .  " * (step + 1) + "     " * (3 - step) + "]"

def chord_engine_loop(current_loop_id, update_ui_callback=None):
    while state["running"] and state["mode"] is not None and state["loop_id"] == current_loop_id:
        if not state["is_step_mode"]:
            if state["mode"] == "chords":
                state["current_chord"] = random.choice(all_jazz_chords)
            elif state["mode"] == "251":
                if not state["progression_queue"]:
                    _, root_2, root_5, root_1 = random.choice(major_251_sequences)
                    state["progression_queue"] = [f"{root_2}m7", f"{root_5}7", f"{root_1}maj7"]
                state["current_chord"] = state["progression_queue"].pop(0)

            if update_ui_callback:
                update_ui_callback(state["current_chord"], "[  .       ]")
            
            play_tick_sound()

            beat_duration = 60.0 / state["bpm"]
            step_duration = beat_duration / 4
            
            for step in range(4):
                if state["is_step_mode"] or not state["running"] or state["mode"] is None or state["loop_id"] != current_loop_id:
                    break
                time.sleep(step_duration)
                if not state["is_step_mode"] and state["loop_id"] == current_loop_id:
                    if update_ui_callback:
                        update_ui_callback(state["current_chord"], get_countdown_dots(step))
        else:
            time.sleep(0.1)

Window.fullscreen = True
Window.orientation = 'portrait'

class JazzTrainerApp(App):
    def build(self):
        self.title = "Jazz Trainer"
        
        self.root_box = BoxLayout(orientation='vertical', padding=30, spacing=0, size_hint=(1, 1))
        
        with self.root_box.canvas.before:
            Color(0.07, 0.07, 0.07, 1)
            self.bg_rect = Rectangle(size=self.root_box.size, pos=self.root_box.pos)
        
        self.root_box.bind(size=self._update_bg, pos=self._update_bg)
        
        self.setup_menu()
        return self.root_box

    def _update_bg(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size

    def setup_menu(self):
        self.root_box.clear_widgets()
        state["mode"] = None
        state["progression_queue"] = []
        state["is_step_mode"] = False
        
        layout = BoxLayout(orientation='vertical', padding=30, spacing=15, size_hint=(1, 1))
        
        title = Label(text="Jazz Training Mode", size_hint_y=0.25, font_size='22sp', color=(1, 1, 1, 1), bold=True)
        layout.add_widget(title)
        
        btn_chords = Button(text="Practice Chords", size_hint_y=0.25, font_size='12sp')
        btn_chords.background_color = (0.13, 0.13, 0.13, 1)
        btn_chords.bind(on_press=lambda x: self.start_session("chords"))
        layout.add_widget(btn_chords)
        
        btn_251 = Button(text="Practice 2/5/1", size_hint_y=0.25, font_size='12sp')
        btn_251.background_color = (0.13, 0.13, 0.13, 1)
        btn_251.bind(on_press=lambda x: self.start_session("251"))
        layout.add_widget(btn_251)
        
        btn_exit = Button(text="Exit", size_hint_y=0.25, font_size='12sp')
        btn_exit.background_color = (0.83, 0.19, 0.19, 1)
        btn_exit.bind(on_press=self.stop)
        layout.add_widget(btn_exit)
        
        self.root_box.add_widget(layout)

    def start_session(self, mode):
        state["mode"] = mode
        state["loop_id"] += 1
        
        self.root_box.clear_widgets()
        
        layout = BoxLayout(orientation='vertical', padding=30, spacing=15, size_hint=(1, 1))
        
        self.chord_label = Label(text="Ready", font_size='54sp', color=(1, 0.7, 0, 1), size_hint_y=0.25, bold=True)
        layout.add_widget(self.chord_label)
        
        self.dots_label = Label(text="[  .   .   .   .  ]", font_size='16sp', color=(0.33, 0.33, 0.33, 1), size_hint_y=0.08)
        layout.add_widget(self.dots_label)
        
        self.bpm_label = Label(text="30 BPM", font_size='16sp', color=(1, 1, 1, 1), size_hint_y=0.08)
        layout.add_widget(self.bpm_label)
        
        row1 = GridLayout(cols=2, spacing=8, size_hint_y=0.12)
        
        btn_slower = Button(text="Slower", font_size='12sp')
        btn_slower.background_color = (0.13, 0.13, 0.13, 1)
        btn_slower.bind(on_press=self.slow_down)
        row1.add_widget(btn_slower)
        
        btn_faster = Button(text="Faster", font_size='12sp')
        btn_faster.background_color = (0.13, 0.13, 0.13, 1)
        btn_faster.bind(on_press=self.speed_up)
        row1.add_widget(btn_faster)
        
        layout.add_widget(row1)
        
        row2 = GridLayout(cols=2, spacing=8, size_hint_y=0.12)
        
        self.step_btn = Button(text="Step", font_size='12sp')
        self.step_btn.background_color = (0.13, 0.13, 0.13, 1)
        self.step_btn.bind(on_press=self.advance_step)
        row2.add_widget(self.step_btn)
        
        self.resume_btn = Button(text="Resume", font_size='12sp')
        self.resume_btn.background_color = (0.13, 0.13, 0.13, 1)
        self.resume_btn.bind(on_press=self.resume_beat)
        row2.add_widget(self.resume_btn)
        
        layout.add_widget(row2)
        
        btn_menu = Button(text="Return to Menu", size_hint_y=0.1, font_size='11sp')
        btn_menu.background_color = (0.53, 0.53, 0.53, 1)
        btn_menu.bind(on_press=lambda x: self.setup_menu())
        layout.add_widget(btn_menu)
        
        self.root_box.add_widget(layout)
        
        threading.Thread(target=chord_engine_loop, args=(state["loop_id"], self.update_display,), daemon=True).start()

    def update_display(self, chord, dots):
        self.chord_label.text = chord
        self.dots_label.text = dots
        self.bpm_label.text = f"{state['bpm']} BPM"

    def advance_step(self, instance):
        if state["mode"] is None:
            return
        
        state["is_step_mode"] = True
        self.step_btn.text = "Step ▶"
        self.step_btn.background_color = (1, 0.7, 0, 1)
        self.resume_btn.background_color = (0.13, 0.13, 0.13, 1)
        
        if state["mode"] == "chords":
            state["current_chord"] = random.choice(all_jazz_chords)
        elif state["mode"] == "251":
            if not state["progression_queue"]:
                _, root_2, root_5, root_1 = random.choice(major_251_sequences)
                state["progression_queue"] = [f"{root_2}m7", f"{root_5}7", f"{root_1}maj7"]
            state["current_chord"] = state["progression_queue"].pop(0)
        
        play_tick_sound()
        self.update_display(state["current_chord"], "[  STEP  ]")

    def resume_beat(self, instance):
        if state["mode"] is None:
            return
        
        state["is_step_mode"] = False
        self.step_btn.text = "Step"
        self.step_btn.background_color = (0.13, 0.13, 0.13, 1)
        self.resume_btn.background_color = (0.13, 0.13, 0.13, 1)
        self.dots_label.text = "[  .   .   .   .  ]"

    def speed_up(self, instance):
        if state["mode"] is None:
            return
        state["bpm"] = min(state["bpm"] + 5, 240)
        self.bpm_label.text = f"{state['bpm']} BPM"

    def slow_down(self, instance):
        if state["mode"] is None:
            return
        state["bpm"] = max(state["bpm"] - 5, 10)
        self.bpm_label.text = f"{state['bpm']} BPM"

    def on_stop(self):
        state["running"] = False
        return True
