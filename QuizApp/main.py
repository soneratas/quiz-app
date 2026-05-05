from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.core.window import Window
import requests
import random

# ---------------- THEME ----------------
Window.clearcolor = (0.96, 0.96, 0.95, 1)

ACCENT = (0.35, 0.55, 0.95, 1)
CARD = (0.88, 0.90, 0.92, 1)
TEXT = (0.12, 0.12, 0.14, 1)

URL = "https://raw.githubusercontent.com/soneratas/quiz-app/main/questions.json"
APP_DATA = {}

def fetch_data():
    try:
        r = requests.get(URL, timeout=5)
        return r.json()
    except:
        return {}


# ---------------- ENGINE ----------------
class Engine:
    def __init__(self):
        self.data = []
        self.index = 0
        self.current = None
        self.score = 0
        self.wrong = []

    def load(self, data):
        self.data = data[:]
        random.shuffle(self.data)
        self.index = 0
        self.score = 0

    def next(self):
        if not self.data:
            return None

        if self.index >= len(self.data):
            self.index = 0

        self.current = self.data[self.index]
        self.index += 1
        return self.current

    def mark(self, correct):
        if correct:
            self.score += 1
        else:
            if self.current not in self.wrong:
                self.wrong.append(self.current)


engine = Engine()


# ---------------- MENU ----------------
class Menu(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        box = BoxLayout(orientation="vertical", padding=20, spacing=10)

        title = Label(text="Quiz App", font_size=32, color=TEXT)

        self.info = Label(text="", color=TEXT)

        btn_sync = Button(text="Güncelle", background_color=ACCENT)
        btn_geo = Button(text="Coğrafya", background_color=CARD)
        btn_hist = Button(text="Tarih", background_color=CARD)
        btn_eng = Button(text="İngilizce", background_color=CARD)
        btn_wrong = Button(text="Bilemediklerim", background_color=(0.9,0.4,0.4,1))

        btn_sync.bind(on_press=self.sync)
        btn_geo.bind(on_press=lambda x: self.start("cografya"))
        btn_hist.bind(on_press=lambda x: self.start("tarih"))
        btn_eng.bind(on_press=lambda x: self.start("ingilizce"))
        btn_wrong.bind(on_press=self.start_wrong)

        box.add_widget(title)
        box.add_widget(self.info)
        box.add_widget(btn_sync)
        box.add_widget(btn_geo)
        box.add_widget(btn_hist)
        box.add_widget(btn_eng)
        box.add_widget(btn_wrong)

        self.add_widget(box)

    def sync(self, x):
        global APP_DATA
        APP_DATA = fetch_data()
        self.info.text = "✔ Güncellendi"

    def start(self, ders):
        data = APP_DATA.get(ders, {})
        if not data:
            self.info.text = "Veri yok"
            return

        self.manager.get_screen("category").load(data)
        self.manager.current = "category"

    def start_wrong(self, x):
        if not engine.wrong:
            self.info.text = "Yanlış yok"
            return

        engine.load(engine.wrong)
        self.manager.current = "quiz"


# ---------------- CATEGORY ----------------
class Category(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.box = BoxLayout(orientation="vertical", padding=20, spacing=10)
        self.add_widget(self.box)

        # 🔥 SABİT BAŞLIK (asla değişmez)
        self.header = Label(
            text="Konu Seç",
            font_size=28,
            color=TEXT,
            size_hint_y=None,
            height=60
        )

        self.box.add_widget(self.header)

    def load(self, data):
        self.box.clear_widgets()
        self.box.add_widget(self.header)

        for konu, sorular in data.items():
            btn = Button(text=konu, background_color=CARD)

            btn.bind(on_press=lambda x, q=sorular, k=konu: self.start(q, k))
            self.box.add_widget(btn)

        back = Button(text="Geri")
        back.bind(on_press=lambda x: setattr(self.manager, "current", "menu"))
        self.box.add_widget(back)

    def start(self, questions, konu):
        converted = [{"soru": q[0], "cevap": q[1], "konu": konu} for q in questions]

        engine.load(converted)
        self.manager.current = "quiz"


# ---------------- QUIZ ----------------
class Quiz(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        box = BoxLayout(orientation="vertical", padding=20, spacing=10)

        # 🔥 SABİT ALANLAR (layout asla oynamaz)
        self.q = Label(
            font_size=22,
            color=TEXT,
            size_hint_y=0.6,
            text_size=(None, None),
            halign="center",
            valign="middle"
        )

        self.a = Label(
            font_size=20,
            color=(0.9,0.4,0.4,1),
            opacity=0,
            size_hint_y=0.2
        )

        self.info = Label(color=TEXT, size_hint_y=0.1)

        self.btn = Button(text="Cevap Göster", background_color=ACCENT)
        self.btn.bind(on_press=self.action)

        btn_wrong = Button(text="Bilmiyorum")
        btn_wrong.bind(on_press=lambda x: engine.mark(False))

        btn_menu = Button(text="Menü")
        btn_menu.bind(on_press=lambda x: setattr(self.manager, "current", "menu"))

        box.add_widget(self.q)
        box.add_widget(self.a)
        box.add_widget(self.info)
        box.add_widget(self.btn)
        box.add_widget(btn_wrong)
        box.add_widget(btn_menu)

        self.add_widget(box)

        self.state = "q"

    def on_size(self, *args):
        # text wrapping fix
        self.q.text_size = (self.width * 0.9, None)

    def on_enter(self):
        self.next_q()

    def action(self, x):
        if self.state == "q":
            self.a.opacity = 1
            self.btn.text = "Sonraki"
            self.state = "a"
        else:
            self.next_q()

    def next_q(self):
        q = engine.next()
        if not q:
            return

        # ❌ KÖŞELİ PARANTEZ YOK
        self.q.text = f"{q.get('konu','')}\n\n{q['soru']}"
        self.a.text = f"👉 {q['cevap']}"
        self.a.opacity = 0

        self.btn.text = "Cevap Göster"
        self.state = "q"
        self.info.text = f"Skor: {engine.score}"


# ---------------- APP ----------------
class QuizApp(App):
    def build(self):
        sm = ScreenManager()

        global APP_DATA
        APP_DATA = fetch_data()

        sm.add_widget(Menu(name="menu"))
        sm.add_widget(Category(name="category"))
        sm.add_widget(Quiz(name="quiz"))

        return sm


QuizApp().run()