import random
import time
import sys
import threading
import math
import os

os.environ['SDL_AUDIODRIVER'] = 'android'

# --- PREVENT SCREEN LOCK ON ANDROID ---
try:
    from jnius import autoclass
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    activity = PythonActivity.mActivity
    WindowManager = autoclass('android.view.WindowManager')
    activity.getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
except Exception:
    pass

# --- MUSICAL DATA STORES ---
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

# --- AUDIO (Pure Python - no pygame/numpy) ---
def play_tick_sound():
    """Play a simple beep sound using Android audio."""
    try:
        from jnius import autoclass
        
        # Get Android audio context
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        activity = PythonActivity.mActivity
        context = activity.getApplicationContext()
        
        # Use Android's built-in Ringtone for a beep
        RingtoneManager = autoclass('android.media.RingtoneManager')
        ringtone = RingtoneManager.getRingtone(context, RingtoneManager.getDefaultUri(RingtoneManager.TYPE_NOTIFICATION))
        ringtone.play()
    except Exception:
        # Fallback: silent if audio not available
        pass

def get_countdown_dots(step):
    return "[" + "  .  " * (step + 1) + "     " * (3 - step) + "]"

# --- BACKGROUND ENGINE ---
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

# --- TOGA GUI ---
import toga
from toga.style import Pack
from toga.constants import ROW, COLUMN

class JazzTrainerApp(toga.App):
    def startup(self):
        """Build and show the Toga UI."""
        self.show_menu()

    def show_menu(self):
        """Display the main menu."""
        state["mode"] = None
        state["progression_queue"] = []
        state["is_step_mode"] = False
        
        # Main container
        main_box = toga.Box(style=Pack(direction=COLUMN, padding=20, flex=1))
        
        # Title
        title = toga.Label(
            'Jazz Training Mode',
            style=Pack(padding=10, font_size=22, text_align='center', flex=0)
        )
        main_box.add(title)
        
        # Spacer
        spacer1 = toga.Box(style=Pack(flex=1))
        main_box.add(spacer1)
        
        # Practice Chords button
        btn_chords = toga.Button(
            'Practice Chords',
            on_press=lambda w: self.start_session('chords'),
            style=Pack(padding=10, flex=0, width=300)
        )
        main_box.add(btn_chords)
        
        # Practice 2/5/1 button
        btn_251 = toga.Button(
            'Practice 2/5/1',
            on_press=lambda w: self.start_session('251'),
            style=Pack(padding=10, flex=0, width=300)
        )
        main_box.add(btn_251)
        
        # Spacer
        spacer2 = toga.Box(style=Pack(flex=1))
        main_box.add(spacer2)
        
        # Exit button
        btn_exit = toga.Button(
            'Exit',
            on_press=self.exit_app,
            style=Pack(padding=10, flex=0, width=300)
        )
        main_box.add(btn_exit)
        
        self.main_window.content = main_box

    def start_session(self, mode):
        """Start a training session."""
        state["mode"] = mode
        state["loop_id"] += 1
        
        # Main container
        main_box = toga.Box(style=Pack(direction=COLUMN, padding=20, flex=1))
        
        # Chord display (large)
        self.chord_label = toga.Label(
            'Ready',
            style=Pack(padding=10, font_size=48, text_align='center', flex=0)
        )
        main_box.add(self.chord_label)
        
        # Dots display
        self.dots_label = toga.Label(
            '[  .   .   .   .  ]',
            style=Pack(padding=5, font_size=14, text_align='center', flex=0)
        )
        main_box.add(self.dots_label)
        
        # BPM display
        self.bpm_label = toga.Label(
            '30 BPM',
            style=Pack(padding=5, font_size=14, text_align='center', flex=0)
        )
        main_box.add(self.bpm_label)
        
        # Spacer
        spacer1 = toga.Box(style=Pack(flex=1))
        main_box.add(spacer1)
        
        # Row 1: Slower / Faster
        row1 = toga.Box(style=Pack(direction=ROW, padding=5, flex=0))
        
        btn_slower = toga.Button(
            'Slower',
            on_press=self.slow_down,
            style=Pack(padding=5, flex=1)
        )
        row1.add(btn_slower)
        
        btn_faster = toga.Button(
            'Faster',
            on_press=self.speed_up,
            style=Pack(padding=5, flex=1)
        )
        row1.add(btn_faster)
        
        main_box.add(row1)
        
        # Row 2: Step / Resume
        row2 = toga.Box(style=Pack(direction=ROW, padding=5, flex=0))
        
        self.step_btn = toga.Button(
            'Step',
            on_press=self.advance_step,
            style=Pack(padding=5, flex=1)
        )
        row2.add(self.step_btn)
        
        self.resume_btn = toga.Button(
            'Resume',
            on_press=self.resume_beat,
            style=Pack(padding=5, flex=1)
        )
        row2.add(self.resume_btn)
        
        main_box.add(row2)
        
        # Spacer
        spacer2 = toga.Box(style=Pack(flex=1))
        main_box.add(spacer2)
        
        # Return to Menu button
        btn_menu = toga.Button(
            'Return to Menu',
            on_press=lambda w: self.show_menu(),
            style=Pack(padding=10, flex=0, width=300)
        )
        main_box.add(btn_menu)
        
        self.main_window.content = main_box
        
        # Start the chord engine in background
        threading.Thread(
            target=chord_engine_loop,
            args=(state["loop_id"], self.update_display),
            daemon=True
        ).start()

    def update_display(self, chord, dots):
        """Update the UI labels from the background thread."""
        self.chord_label.text = chord
        self.dots_label.text = dots
        self.bpm_label.text = f"{state['bpm']} BPM"

    def advance_step(self, widget):
        """Advance to the next chord (step mode)."""
        if state["mode"] is None:
            return
        
        state["is_step_mode"] = True
        self.step_btn.text = "Step ▶"
        
        if state["mode"] == "chords":
            state["current_chord"] = random.choice(all_jazz_chords)
        elif state["mode"] == "251":
            if not state["progression_queue"]:
                _, root_2, root_5, root_1 = random.choice(major_251_sequences)
                state["progression_queue"] = [f"{root_2}m7", f"{root_5}7", f"{root_1}maj7"]
            state["current_chord"] = state["progression_queue"].pop(0)
        
        play_tick_sound()
        self.update_display(state["current_chord"], "[  STEP  ]")

    def resume_beat(self, widget):
        """Resume automatic chord progression."""
        if state["mode"] is None:
            return
        
        state["is_step_mode"] = False
        self.step_btn.text = "Step"
        self.dots_label.text = "[  .   .   .   .  ]"

    def speed_up(self, widget):
        """Increase BPM."""
        if state["mode"] is None:
            return
        state["bpm"] = min(state["bpm"] + 5, 240)
        self.bpm_label.text = f"{state['bpm']} BPM"

    def slow_down(self, widget):
        """Decrease BPM."""
        if state["mode"] is None:
            return
        state["bpm"] = max(state["bpm"] - 5, 10)
        self.bpm_label.text = f"{state['bpm']} BPM"

    def exit_app(self, widget):
        """Exit the application."""
        state["running"] = False
        self.exit()


if __name__ == '__main__':
    app = JazzTrainerApp('Jazz Trainer', 'com.example.jazztrainer')
    app.main_loop()
