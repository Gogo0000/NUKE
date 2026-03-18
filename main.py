"""
Shinsoo Prank App - Kivy
Hedef: shinsoo.pythonanywhere.com ile haberleşen şaka uygulaması
"""

import threading
import random
import string
import platform as plat

try:
    import requests
except ImportError:
    requests = None

from kivy.app import App
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, Line
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from kivy.animation import Animation
from kivy.properties import NumericProperty, StringProperty, BooleanProperty


BASE_URL = "https://shinsoo.pythonanywhere.com"
SECRET_CODE = "gokhan"


# ─────────────────────────────────────────────
#  Matrix yağmuru widget'ı
# ─────────────────────────────────────────────
class MatrixRain(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cols = []
        self._event = None
        self.active = False

    def start(self):
        self.active = True
        self.cols = []
        col_count = max(1, int(Window.width / 18))
        for _ in range(col_count):
            self.cols.append({
                "x": random.randint(0, max(1, int(Window.width))),
                "y": random.randint(0, max(1, int(Window.height))),
                "speed": random.uniform(4, 14),
                "chars": [random.choice(string.printable[:62]) for _ in range(random.randint(6, 20))],
            })
        self._event = Clock.schedule_interval(self._update, 1 / 20)

    def stop(self):
        self.active = False
        if self._event:
            self._event.cancel()
            self._event = None
        self.canvas.clear()

    def _update(self, dt):
        self.canvas.clear()
        with self.canvas:
            for col in self.cols:
                col["y"] -= col["speed"]
                if col["y"] < -len(col["chars"]) * 18:
                    col["y"] = Window.height + random.randint(0, 200)
                    col["x"] = random.randint(0, max(1, int(Window.width)))
                    col["chars"] = [
                        random.choice(string.printable[:62])
                        for _ in range(random.randint(6, 20))
                    ]
                for i, ch in enumerate(col["chars"]):
                    alpha = max(0.05, 1.0 - i * 0.06)
                    if i == 0:
                        Color(0.7, 1, 0.7, alpha)
                    else:
                        Color(0, 0.9, 0.1, alpha * 0.7)
                    # Kivy'de canvas'a metin çizmek için Label kullanmak gerekir
                    # Hafif performans için sadece renkli dikdörtgenler çiziyoruz
                    # (gerçek karakter render'ı için CoreLabel gerekir, ama ağır)
                    rect_w = 10
                    rect_h = 16
                    Rectangle(
                        pos=(col["x"], col["y"] + i * 18),
                        size=(rect_w, rect_h),
                    )


# ─────────────────────────────────────────────
#  Ana ekran widget'ı
# ─────────────────────────────────────────────
class ShinsooRoot(FloatLayout):

    progress_val = NumericProperty(0)
    status_text = StringProperty("Sistem Kontrol Ediliyor...")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.phase = "idle"   # idle → loading → chaos
        self.sound = None
        self.device_id = None
        self._progress_event = None
        self._check_event = None
        self._build_ui()

    # ── UI ──────────────────────────────────────
    def _build_ui(self):
        Window.clearcolor = (0, 0, 0, 1)

        # --- Bekleme katmanı ---
        self.idle_layer = BoxLayout(
            orientation="vertical",
            size_hint=(1, 1),
            pos_hint={"x": 0, "y": 0},
        )
        self.idle_label = Label(
            text="Sistem Kontrol Ediliyor...",
            font_size="22sp",
            color=(0.7, 0.7, 0.7, 1),
            bold=True,
        )
        self.idle_layer.add_widget(self.idle_label)
        self.add_widget(self.idle_layer)

        # --- Yükleme katmanı (gizli) ---
        self.loading_layer = BoxLayout(
            orientation="vertical",
            size_hint=(1, 1),
            pos_hint={"x": 0, "y": 0},
            padding=[40, 80, 40, 80],
            spacing=20,
            opacity=0,
        )
        self.update_title = Label(
            text="Kritik Sistem Güncellemesi",
            font_size="26sp",
            color=(0.2, 0.5, 1, 1),
            bold=True,
            size_hint_y=None,
            height=60,
        )
        self.progress_bar = ProgressBar(
            max=100,
            value=0,
            size_hint=(1, None),
            height=30,
        )
        self.progress_label = Label(
            text="%0",
            font_size="18sp",
            color=(0.2, 0.5, 1, 1),
            size_hint_y=None,
            height=40,
        )
        self.loading_layer.add_widget(Widget())  # spacer
        self.loading_layer.add_widget(self.update_title)
        self.loading_layer.add_widget(self.progress_bar)
        self.loading_layer.add_widget(self.progress_label)
        self.loading_layer.add_widget(Widget())  # spacer
        self.add_widget(self.loading_layer)

        # --- Kaos katmanı (gizli) ---
        self.chaos_layer = FloatLayout(
            size_hint=(1, 1),
            pos_hint={"x": 0, "y": 0},
            opacity=0,
        )
        self.matrix = MatrixRain(
            size_hint=(1, 1),
            pos_hint={"x": 0, "y": 0},
        )
        self.chaos_layer.add_widget(self.matrix)

        self.crash_label = Label(
            text="SİSTEM ÇÖKTÜ\nTÜM VERİLER İMHÂ EDİLİYOR",
            font_size="28sp",
            color=(1, 0.05, 0.05, 1),
            bold=True,
            halign="center",
            size_hint=(0.9, None),
            height=160,
            pos_hint={"center_x": 0.5, "top": 0.75},
        )
        self.crash_label.bind(size=self.crash_label.setter("text_size"))
        self.chaos_layer.add_widget(self.crash_label)

        # Şifre alanı ve buton
        bottom_bar = BoxLayout(
            orientation="horizontal",
            size_hint=(0.8, None),
            height=50,
            pos_hint={"center_x": 0.5, "y": 0.04},
            spacing=10,
        )
        self.password_input = TextInput(
            hint_text="Şifre girin...",
            multiline=False,
            size_hint=(0.7, 1),
            foreground_color=(1, 1, 1, 1),
            background_color=(0.15, 0.15, 0.15, 1),
            cursor_color=(1, 1, 1, 1),
            font_size="16sp",
        )
        self.confirm_btn = Button(
            text="ONAYLA",
            size_hint=(0.3, 1),
            background_color=(0.8, 0, 0, 1),
            color=(1, 1, 1, 1),
            bold=True,
            font_size="15sp",
        )
        self.confirm_btn.bind(on_press=self._on_confirm)
        bottom_bar.add_widget(self.password_input)
        bottom_bar.add_widget(self.confirm_btn)
        self.chaos_layer.add_widget(bottom_bar)

        self.add_widget(self.chaos_layer)

    # ── Kayıt ve Check ──────────────────────────
    def register_device(self):
        """Cihazı sunucuya kaydet, device_id al."""
        if requests is None:
            self.device_id = "no_requests"
            self._start_polling()
            return

        def _do():
            try:
                model = plat.node() or "UnknownDevice"
                system = plat.system() or "Unknown"
                resp = requests.post(
                    f"{BASE_URL}/register",
                    json={"device": f"{model} ({system})"},
                    timeout=8,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    self.device_id = data.get("device_id") or data.get("id") or "unknown"
                else:
                    self.device_id = "reg_failed"
            except Exception:
                self.device_id = "offline"
            self._start_polling()

        threading.Thread(target=_do, daemon=True).start()

    def _start_polling(self):
        """Her 3 saniyede sunucudan komut sorgula."""
        self._check_event = Clock.schedule_interval(self._check_command, 3)

    def _check_command(self, dt):
        if not self.device_id:
            return

        def _do():
            try:
                url = f"{BASE_URL}/check/{self.device_id}"
                resp = requests.get(url, timeout=5)
                if resp.status_code == 200:
                    data = resp.json()
                    cmd = data.get("command", "").upper()
                    if cmd == "START" and self.phase == "idle":
                        Clock.schedule_once(lambda _: self._start_loading(), 0)
                    elif cmd == "STOP":
                        Clock.schedule_once(lambda _: self._stop_app(), 0)
            except Exception:
                pass  # İnternet yok veya site kapalı → sessizce devam

        if requests is not None:
            threading.Thread(target=_do, daemon=True).start()

    # ── Faz Geçişleri ───────────────────────────
    def _start_loading(self):
        """AŞAMA 1: Mavi güncelleme ekranı + ProgressBar"""
        if self.phase != "idle":
            return
        self.phase = "loading"
        Window.clearcolor = (0, 0, 0, 1)

        self.idle_layer.opacity = 0
        anim = Animation(opacity=1, duration=0.4)
        anim.start(self.loading_layer)

        self.progress_bar.value = 0
        self._progress_val = 0
        self._progress_event = Clock.schedule_interval(self._tick_progress, 0.06)

    def _tick_progress(self, dt):
        """ProgressBar yavaşça %100'e dolar."""
        increment = random.uniform(0.3, 1.1)
        self._progress_val = min(100, self._progress_val + increment)
        self.progress_bar.value = self._progress_val
        self.progress_label.text = f"%{int(self._progress_val)}"

        if self._progress_val >= 100:
            if self._progress_event:
                self._progress_event.cancel()
                self._progress_event = None
            Clock.schedule_once(lambda _: self._start_chaos(), 0.3)

    def _start_chaos(self):
        """AŞAMA 2: Kırmızı ekran + Matrix + müzik"""
        if self.phase == "chaos":
            return
        self.phase = "chaos"
        Window.clearcolor = (0.55, 0, 0, 1)

        self.loading_layer.opacity = 0

        anim = Animation(opacity=1, duration=0.3)
        anim.start(self.chaos_layer)

        self.matrix.start()
        self._play_music()

        # Çarpıcı titreme animasyonu
        Clock.schedule_interval(self._shake_label, 0.08)

    def _shake_label(self, dt):
        if self.phase != "chaos":
            return False  # otomatik durdur
        offset = random.randint(-4, 4)
        self.crash_label.x = (Window.width - self.crash_label.width) / 2 + offset

    # ── Müzik ───────────────────────────────────
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

    # ── Durdurma ────────────────────────────────
    def _on_confirm(self, instance):
        entered = self.password_input.text.strip().lower()
        if entered == SECRET_CODE:
            self._stop_app()

    def _stop_app(self):
        self._stop_music()
        self.matrix.stop()
        if self._check_event:
            self._check_event.cancel()
        if self._progress_event:
            self._progress_event.cancel()
        App.get_running_app().stop()


# ─────────────────────────────────────────────
#  Kivy App
# ─────────────────────────────────────────────
class ShinsooApp(App):
    def build(self):
        self.title = "Sistem Güncelleme"
        root = ShinsooRoot()
        Clock.schedule_once(lambda dt: root.register_device(), 1)
        return root


if __name__ == "__main__":
    ShinsooApp().run()
