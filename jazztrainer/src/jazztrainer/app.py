import random
import time
import threading

# --- PREVENT SCREEN LOCK ---
try:
    from jnius import autoclass
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    activity = PythonActivity.mActivity
    WindowManager = autoclass('android.view.WindowManager')
    activity.getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
except Exception:
    pass

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

def play_tick_sound():
    try:
        from jnius import autoclass
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        activity = PythonActivity.mActivity
        context = activity.getApplicationContext()
        RingtoneManager = autoclass('android.media.RingtoneManager')
        ringtone = RingtoneManager.getRingtone(context, RingtoneManager.getDefaultUri(RingtoneManager.TYPE_NOTIFICATION))
        ringtone.play()
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

# --- MINIMAL ANDROID UI ---
from jnius import autoclass, PythonJavaClass, java_method

PythonActivity = autoclass('org.kivy.android.PythonActivity')
LinearLayout = autoclass('android.widget.LinearLayout')
Button = autoclass('android.widget.Button')
TextView = autoclass('android.widget.TextView')
LayoutParams = autoclass('android.widget.LinearLayout$LayoutParams')

class ClickListener(PythonJavaClass):
    __javainterfaces__ = ['android/view/View$OnClickListener']
    
    def __init__(self, callback):
        super().__init__()
        self.callback = callback
    
    @java_method('(Landroid/view/View;)V')
    def onClick(self, view):
        try:
            self.callback()
        except Exception as e:
            print(f"Error: {e}")

class JazzTrainerUI:
    def __init__(self):
        self.activity = PythonActivity.mActivity
        self.main_layout = None
        self.chord_label = None
        self.dots_label = None
        self.bpm_label = None
        self.step_btn = None
        self.show_menu()
    
    def show_menu(self):
        state["mode"] = None
        state["progression_queue"] = []
        state["is_step_mode"] = False
        
        self.main_layout = LinearLayout(self.activity)
        self.main_layout.setOrientation(LinearLayout.VERTICAL)
        
        title = TextView(self.activity)
        title.setText("Jazz Training Mode")
        title.setTextSize(24)
        title.setPadding(20, 20, 20, 20)
        self.main_layout.addView(title)
        
        btn_chords = Button(self.activity)
        btn_chords.setText("Practice Chords")
        btn_chords.setOnClickListener(ClickListener(lambda: self.start_session("chords")))
        self.main_layout.addView(btn_chords, LayoutParams(LayoutParams.MATCH_PARENT, LayoutParams.WRAP_CONTENT))
        
        btn_251 = Button(self.activity)
        btn_251.setText("Practice 2/5/1")
        btn_251.setOnClickListener(ClickListener(lambda: self.start_session("251")))
        self.main_layout.addView(btn_251, LayoutParams(LayoutParams.MATCH_PARENT, LayoutParams.WRAP_CONTENT))
        
        btn_exit = Button(self.activity)
        btn_exit.setText("Exit")
        btn_exit.setOnClickListener(ClickListener(self.exit_app))
        self.main_layout.addView(btn_exit, LayoutParams(LayoutParams.MATCH_PARENT, LayoutParams.WRAP_CONTENT))
        
        self.activity.setContentView(self.main_layout)
    
    def start_session(self, mode):
        state["mode"] = mode
        state["loop_id"] += 1
        
        self.main_layout = LinearLayout(self.activity)
        self.main_layout.setOrientation(LinearLayout.VERTICAL)
        self.main_layout.setPadding(20, 20, 20, 20)
        
        self.chord_label = TextView(self.activity)
        self.chord_label.setText("Ready")
        self.chord_label.setTextSize(48)
        self.chord_label.setPadding(10, 10, 10, 10)
        self.main_layout.addView(self.chord_label)
        
        self.dots_label = TextView(self.activity)
        self.dots_label.setText("[  .   .   .   .  ]")
        self.dots_label.setTextSize(16)
        self.main_layout.addView(self.dots_label)
        
        self.bpm_label = TextView(self.activity)
        self.bpm_label.setText("30 BPM")
        self.bpm_label.setTextSize(16)
        self.main_layout.addView(self.bpm_label)
        
        btn_slower = Button(self.activity)
        btn_slower.setText("Slower")
        btn_slower.setOnClickListener(ClickListener(self.slow_down))
        self.main_layout.addView(btn_slower, LayoutParams(LayoutParams.MATCH_PARENT, LayoutParams.WRAP_CONTENT))
        
        btn_faster = Button(self.activity)
        btn_faster.setText("Faster")
        btn_faster.setOnClickListener(ClickListener(self.speed_up))
        self.main_layout.addView(btn_faster, LayoutParams(LayoutParams.MATCH_PARENT, LayoutParams.WRAP_CONTENT))
        
        self.step_btn = Button(self.activity)
        self.step_btn.setText("Step")
        self.step_btn.setOnClickListener(ClickListener(self.advance_step))
        self.main_layout.addView(self.step_btn, LayoutParams(LayoutParams.MATCH_PARENT, LayoutParams.WRAP_CONTENT))
        
        btn_resume = Button(self.activity)
        btn_resume.setText("Resume")
        btn_resume.setOnClickListener(ClickListener(self.resume_beat))
        self.main_layout.addView(btn_resume, LayoutParams(LayoutParams.MATCH_PARENT, LayoutParams.WRAP_CONTENT))
        
        btn_menu = Button(self.activity)
        btn_menu.setText("Return to Menu")
        btn_menu.setOnClickListener(ClickListener(self.show_menu))
        self.main_layout.addView(btn_menu, LayoutParams(LayoutParams.MATCH_PARENT, LayoutParams.WRAP_CONTENT))
        
        self.activity.setContentView(self.main_layout)
        
        threading.Thread(target=chord_engine_loop, args=(state["loop_id"], self.update_display), daemon=True).start()
    
    def update_display(self, chord, dots):
        try:
            self.chord_label.setText(chord)
            self.dots_label.setText(dots)
            self.bpm_label.setText(f"{state['bpm']} BPM")
        except:
            pass
    
    def advance_step(self):
        if state["mode"] is None:
            return
        state["is_step_mode"] = True
        self.step_btn.setText("Step ▶")
        if state["mode"] == "chords":
            state["current_chord"] = random.choice(all_jazz_chords)
        elif state["mode"] == "251":
            if not state["progression_queue"]:
                _, root_2, root_5, root_1 = random.choice(major_251_sequences)
                state["progression_queue"] = [f"{root_2}m7", f"{root_5}7", f"{root_1}maj7"]
            state["current_chord"] = state["progression_queue"].pop(0)
        play_tick_sound()
        self.update_display(state["current_chord"], "[  STEP  ]")
    
    def resume_beat(self):
        if state["mode"] is None:
            return
        state["is_step_mode"] = False
        self.step_btn.setText("Step")
        self.dots_label.setText("[  .   .   .   .  ]")
    
    def speed_up(self):
        if state["mode"] is None:
            return
        state["bpm"] = min(state["bpm"] + 5, 240)
        self.bpm_label.setText(f"{state['bpm']} BPM")
    
    def slow_down(self):
        if state["mode"] is None:
            return
        state["bpm"] = max(state["bpm"] - 5, 10)
        self.bpm_label.setText(f"{state['bpm']} BPM")
    
    def exit_app(self):
        state["running"] = False
        import sys
        sys.exit(0)

if __name__ == '__main__':
    ui = JazzTrainerUI()
