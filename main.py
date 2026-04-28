from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.graphics import Color, Line, Rectangle, Ellipse
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.popup import Popup
from audio import AudioAnalyzer
from chords import CHORDS
from strokes import STROKES


Window.size = (500, 750)
Window.minimum_width = 400
Window.minimum_height = 600


class TunerScale(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.deviation = 0.0
        self.color = (1, 0, 0, 1)
        self.bind(pos=self.update_canvas, size=self.update_canvas)

    def update_canvas(self, *args):
        self.canvas.clear()
        w, h = self.size
        with self.canvas:
            Color(0.15, 0.15, 0.15, 1)
            Rectangle(pos=self.pos, size=self.size) #фон
            Color(0.5, 0.5, 0.5, 1)
            Line(points=[self.x + w * 0.1, self.y + h * 0.5,
                         self.x + w * 0.9, self.y + h * 0.5], width=2) #шкала тюнера
            Color(0.7, 0.7, 0.7, 1)
            Line(points=[self.x + w * 0.5, self.y + h * 0.3,
                         self.x + w * 0.5, self.y + h * 0.7], width=2) #метка точной ноты
            Color(*self.color)
            indicator_x = self.x + w * 0.5 + (self.deviation * w * 0.35)
            Line(points=[indicator_x, self.y + h * 0.3,
                         indicator_x, self.y + h * 0.7], width=4) #где находится наша нота

    def set_deviation(self, value, note="E", string=1): #при отклонении от правильной ноты в зависимости от дальности отклонения цвет зелёный-жёлтый-красный
        self.deviation = max(-1.0, min(1.0, value))
        if abs(self.deviation) < 0.1:
            self.color = (0, 1, 0, 1)
        elif abs(self.deviation) < 0.3:
            self.color = (1, 1, 0, 1)
        else:
            self.color = (1, 0, 0, 1)
        self.update_canvas()


class StringSelector(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='horizontal', size_hint_y=0.08, **kwargs)
        self.strings = ["E2 (6)", "A2 (5)", "D3 (4)", "G3 (3)", "B3 (2)", "E4 (1)"]
        self.current = 5
        self.btn_prev = Button(text="<", size_hint_x=0.15) #стрелки, чтоб можно было выбрать ноту, потом сделаю их красивее
        self.btn_prev.bind(on_press=self.prev_string)
        self.label = Label(text=self.strings[self.current], font_size=18, size_hint_x=0.7)
        self.btn_next = Button(text=">", size_hint_x=0.15)
        self.btn_next.bind(on_press=self.next_string)
        self.add_widget(self.btn_prev)
        self.add_widget(self.label)
        self.add_widget(self.btn_next)

    def prev_string(self, instance):
        self.current = (self.current - 1) % 6 #чтоб был циклический сдвиг
        self.label.text = self.strings[self.current]

    def next_string(self, instance):
        self.current = (self.current + 1) % 6
        self.label.text = self.strings[self.current]

    def get_selected(self):
        return self.current + 1 #возвращает номер струны при ручном выборе


class GuitarView(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.active_string = 1 #какая струна подсвечена
        self.tuned_strings = [False] * 6
        self.bind(pos=self.update_canvas, size=self.update_canvas)

    def update_canvas(self, *args):
        self.canvas.clear()
        w, h = self.size
        cy = self.y + h * 0.48

        with self.canvas:
            Color(0.10, 0.10, 0.16, 1)
            Rectangle(pos=self.pos, size=self.size)

            lower_w = w * 0.20 #левый эллипс
            lower_h = h * 0.54
            lower_x = self.x + w * 0.02
            lower_y = cy - lower_h / 2

            upper_w = w * 0.17 #правый эллипс
            upper_h = h * 0.42
            upper_x = self.x + w * 0.14
            upper_y = cy - upper_h / 2

            Color(0.72, 0.40, 0.20, 1)
            Ellipse(pos=(lower_x, lower_y), size=(lower_w, lower_h))
            Ellipse(pos=(upper_x, upper_y), size=(upper_w, upper_h))
            Rectangle(pos=(upper_x + upper_w * 0.15, cy - h * 0.05),
                      size=(upper_w * 0.70, h * 0.10)) #соединительная перемычка

            rose_radius = h * 0.09 #отверстие
            rose_x = self.x + w * 0.22
            rose_y = cy
            Color(0.85, 0.75, 0.55, 1)
            Line(circle=(rose_x, rose_y, rose_radius + 3), width=3)
            Color(0.05, 0.03, 0.02, 1)
            Ellipse(pos=(rose_x - rose_radius, rose_y - rose_radius),
                    size=(rose_radius * 2, rose_radius * 2))

            bridge_x = self.x + w * 0.06 #бридж, к которому крепятся струны
            Color(0.12, 0.06, 0.03, 1)
            Rectangle(pos=(bridge_x - 3, cy - h * 0.12),
                      size=(6, h * 0.24))
            Color(0.95, 0.90, 0.78, 1)
            Rectangle(pos=(bridge_x - 1, cy - h * 0.10),
                      size=(2, h * 0.20))

        neck_left = self.x + w * 0.30 #гриф
        neck_right = self.x + w * 0.85
        neck_width = h * 0.20
        half_neck = neck_width / 2

        with self.canvas:
            Color(0.50, 0.30, 0.15, 1)
            Rectangle(pos=(neck_left, cy - half_neck),
                      size=(neck_right - neck_left, neck_width)) #дерево грифа

            Color(0.18, 0.11, 0.05, 1)
            Rectangle(pos=(neck_left, cy - half_neck * 0.65),
                      size=(neck_right - neck_left, half_neck * 1.3)) #накладка грифа

            fret_count = 9 #лады
            for f in range(fret_count + 1):
                t = f / fret_count
                x = neck_right - (neck_right - neck_left) * (t ** 0.65)
                Color(0.80, 0.80, 0.80, 1)
                Line(points=[x, cy - half_neck * 0.65,
                             x, cy + half_neck * 0.65], width=2)

            for f in [3, 5, 7]:
                t = (f - 0.5) / fret_count
                x = neck_right - (neck_right - neck_left) * (t ** 0.65)
                Color(0.85, 0.85, 0.85, 0.6)
                Ellipse(pos=(x - 5, cy - 5), size=(10, 10))

            Color(0.95, 0.90, 0.78, 1)
            Rectangle(pos=(neck_right - 3, cy - half_neck * 0.65),
                      size=(3, half_neck * 1.3))

        head_left = neck_right #основание грифа
        head_right = self.x + w * 0.97
        with self.canvas:
            Color(0.44, 0.26, 0.12, 1)
            Rectangle(pos=(head_left, cy - half_neck * 0.8),
                      size=(head_right - head_left, half_neck * 1.6))

            for side in [-1, 1]: #колки
                for i in range(3):
                    px = head_left + (head_right - head_left) * (0.3 + i * 0.22)
                    py = cy + side * (half_neck * 1.0)
                    Color(0.30, 0.30, 0.30, 1)
                    Ellipse(pos=(px - 6, py - 6), size=(12, 12))
                    Color(0.80, 0.80, 0.80, 1)
                    Ellipse(pos=(px - 4, py - 4), size=(8, 8))

            for i in range(6): #струны на грифе
                y_pos = cy - half_neck * 0.52 + (half_neck * 1.04) * (i / 5)
                if i + 1 == self.active_string:
                    if self.tuned_strings[i]:
                        Color(0.1, 1, 0.3, 1) #настроена - зелёный
                    else:
                        Color(1, 0.15, 0.15, 1) #не настроена - красный
                else:
                    Color(0.95, 0.95, 0.95, 1) #не активна - белый

                thickness = 3.2 - i * 0.45
                Line(
                    points=[bridge_x, y_pos, neck_right, y_pos],
                    width=thickness,
                    cap='round'
                )

    def set_active_string(self, string_num):
        self.active_string = string_num
        self.update_canvas()

    def set_string_tuned(self, string_num, is_tuned):
        self.tuned_strings[string_num - 1] = is_tuned
        self.update_canvas()


class ChordCard(Button):
    def __init__(self, chord_name, **kwargs):
        super().__init__(**kwargs)
        self.chord_name = chord_name
        self.text = chord_name
        self.font_size = 24
        self.size_hint_y = None
        self.height = 80
        self.background_color = (0.3, 0.2, 0.1, 1)
        self.color = (1, 1, 1, 1)


class StrumCard(Button):
    def __init__(self, strum_name, **kwargs):
        super().__init__(**kwargs)
        self.strum_name = strum_name
        self.text = strum_name
        self.font_size = 20
        self.size_hint_y = None
        self.height = 80
        self.background_color = (0.2, 0.3, 0.4, 1)
        self.color = (1, 1, 1, 1)


class ChordFretboard(BoxLayout): #отображение аккорда на грифе
    def __init__(self, chord_name="", notes=None, **kwargs):
        super().__init__(orientation='vertical', spacing=0, **kwargs)
        self.chord_name = chord_name
        self.notes = notes or []
        self.size_hint_y = 0.6
        self.labels_row = BoxLayout(orientation='horizontal', size_hint_y=0.1, spacing=0, padding=[0, 0, 0, 0])
        self.labels_row.add_widget(Widget(size_hint_x=0.16))
        for f in range(1, 5):
            lbl = Label(
                text=str(f),
                font_size=16,
                color=(0.8, 0.8, 0.8, 1),
                bold=True,
                halign='center',
                valign='middle',
                size_hint_x=0.18
            )
            self.labels_row.add_widget(lbl)
        self.labels_row.add_widget(Widget(size_hint_x=0.14))
        self.add_widget(self.labels_row)

        self.fretboard = FretboardCanvas(chord_name=chord_name, notes=notes)
        self.add_widget(self.fretboard)


class FretboardCanvas(Widget): #отрисовка грифа
    def __init__(self, chord_name="", notes=None, **kwargs):
        super().__init__(**kwargs)
        self.chord_name = chord_name
        self.notes = notes or []
        self.bind(pos=self.update_canvas, size=self.update_canvas)

    def update_canvas(self, *args):
        self.canvas.clear()
        w, h = self.size
        with self.canvas:
            Color(0.1, 0.1, 0.05, 1) #фон
            Rectangle(pos=self.pos, size=self.size)

            Color(0.25, 0.15, 0.05, 1)
            Rectangle(pos=(self.x + w * 0.05, self.y + h * 0.05),
                      size=(w * 0.9, h * 0.95)) #гриф

            Color(0.8, 0.8, 0.8, 1)
            for i in range(6): #струны
                y_pos = self.y + h * 0.95 - (h * 0.85) * (i / 5)
                thickness = 5.0 - i * 0.7
                Line(
                    points=[self.x + w * 0.1, y_pos, self.x + w * 0.9, y_pos],
                    width=thickness
                )

            for f in range(5): #лады
                x = self.x + w * 0.15 + w * 0.18 * f
                Line(
                    points=[x, self.y + h * 0.05, x, self.y + h],
                    width=1.5
                )

            Color(0.3, 0.8, 0.3, 1)
            chord_positions = { #точки, где надо зажимать
                "C":  [(5, 1), (3, 2), (2, 3)],
                "Dm": [(6, 1), (5, 3), (4, 2)],
                "Em": [(3, 2), (2, 2)],
                "F":  [(6, 1), (5, 1), (4, 2), (3, 3)],
                "G":  [(6, 3), (2, 2), (1, 3)],
                "Am": [(5, 1), (4, 2), (3, 2)],
                "D":  [(6, 2), (5, 3), (4, 2)],
                "E":  [(4, 1), (3, 2), (2, 2)],
                "A":  [(5, 2), (4, 2), (3, 2)],
                "Bm": [(6, 2), (5, 3), (4, 4)],
            }

            positions = chord_positions.get(self.chord_name, [])
            for string, fret in positions:
                y_pos = self.y + h * 0.95 - (h * 0.85) * ((string - 1) / 5)
                x_pos = self.x + w * 0.15 + w * 0.18 * (fret - 0.5)
                Ellipse(pos=(x_pos - 8, y_pos - 8), size=(16, 16))


class StrumView(Widget): #Схема боя
    def __init__(self, pattern=None, **kwargs):
        super().__init__(**kwargs)
        self.pattern = pattern or []
        self.bind(pos=self.update_canvas, size=self.update_canvas)

    def update_canvas(self, *args):
        self.canvas.clear()
        w, h = self.size
        count = len(self.pattern) #рассчитываем позицию
        spacing = w / (count + 1)
        with self.canvas:
            for i, symbol in enumerate(self.pattern):
                x = self.x + spacing * (i + 1)
                cy = self.y + h / 2
                size = min(spacing * 0.35, h * 0.35)

                if symbol in ("v", "↓"): #отрисовка символов
                    Color(0.3, 0.8, 0.3, 1)
                    Line(points=[x, cy + size, x, cy - size], width=3)
                    Line(points=[x - size * 0.4, cy - size * 0.4, x, cy - size, x + size * 0.4, cy - size * 0.4], width=3)

                elif symbol in ("^", "↑"):
                    Color(0.3, 0.5, 1, 1)
                    Line(points=[x, cy - size, x, cy + size], width=3)
                    Line(points=[x - size * 0.4, cy + size * 0.4, x, cy + size, x + size * 0.4, cy + size * 0.4], width=3)

                elif symbol in ("x", "X", "✗"):
                    Color(1, 0.3, 0.3, 1)
                    Line(points=[x - size * 0.5, cy - size * 0.5, x + size * 0.5, cy + size * 0.5], width=3)
                    Line(points=[x + size * 0.5, cy - size * 0.5, x - size * 0.5, cy + size * 0.5], width=3)

                elif symbol == "P":
                    Color(1, 0.7, 0.1, 1)
                    Line(circle=(x, cy, size * 0.6), width=2)

                elif symbol == "i":
                    Color(0.7, 0.3, 1, 1)
                    Line(circle=(x, cy, size * 0.6), width=2)

                elif symbol == "_":
                    Color(0.5, 0.5, 0.5, 1)
                    Line(points=[x - size * 0.3, cy, x + size * 0.3, cy], width=3)

                elif symbol == "Б":
                    Color(1, 0.5, 0, 1)
                    Line(circle=(x, cy, size * 0.5), width=2)


class LegendRow(BoxLayout): #расшифровка обозначений (легенда), символ-пояснение
    def __init__(self, symbol="", text="", **kwargs):
        super().__init__(orientation='horizontal', size_hint_y=0.25, spacing=8, **kwargs)
        self.symbol_widget = LegendSymbol(symbol=symbol, size_hint_x=0.35)
        self.add_widget(self.symbol_widget)
        self.add_widget(Label(
            text=text,
            font_size=16,
            color=(0.9, 0.9, 0.9, 1),
            size_hint_x=0.65,
            halign='left',
            valign='middle',
            bold=True
        ))


class LegendSymbol(Widget): #отрисовка символа
    def __init__(self, symbol="", **kwargs):
        super().__init__(**kwargs)
        self.symbol = symbol
        self.bind(pos=self.update_canvas, size=self.update_canvas)

    def update_canvas(self, *args):
        self.canvas.clear()
        w, h = self.size
        cx = self.x + w / 2
        cy = self.y + h / 2
        s = min(w, h) * 2
        with self.canvas:
            if self.symbol == "down":
                Color(0.3, 0.8, 0.3, 1)
                Line(points=[cx, cy + s, cx, cy - s], width=4)
                Line(points=[cx - s*0.4, cy - s*0.4, cx, cy - s, cx + s*0.4, cy - s*0.4], width=4)

            elif self.symbol == "up":
                Color(0.3, 0.5, 1, 1)
                Line(points=[cx, cy - s, cx, cy + s], width=4)
                Line(points=[cx - s*0.4, cy + s*0.4, cx, cy + s, cx + s*0.4, cy + s*0.4], width=4)

            elif self.symbol == "mute":
                Color(1, 0.3, 0.3, 1)
                Line(points=[cx - s*0.5, cy - s*0.5, cx + s*0.5, cy + s*0.5], width=4)
                Line(points=[cx + s*0.5, cy - s*0.5, cx - s*0.5, cy + s*0.5], width=4)

            elif self.symbol == "thumb":
                Color(1, 0.7, 0.1, 1)
                Line(circle=(cx, cy, s*0.6), width=3)

            elif self.symbol == "index":
                Color(0.7, 0.3, 1, 1)
                Line(circle=(cx, cy, s*0.6), width=3)

            elif self.symbol == "bass":
                Color(1, 0.5, 0, 1)
                Line(circle=(cx, cy, s*0.5), width=3)

            elif self.symbol == "pause":
                Color(0.6, 0.6, 0.6, 1)
                Line(points=[cx - s*0.3, cy, cx + s*0.3, cy], width=3)


class LegendView(BoxLayout): # 3 колонки легенды
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', spacing=10, padding=[10, 5], **kwargs)
        self.add_widget(Label(
            text="Обозначения:",
            font_size=20,
            color=(0.9, 0.7, 0.2, 1),
            size_hint_y=0.08,
            bold=True
        ))
        row1 = BoxLayout(orientation='horizontal', size_hint_y=0.30, spacing=15)
        row1.add_widget(LegendRow(symbol="down", text="удар вниз"))
        row1.add_widget(LegendRow(symbol="up", text="удар вверх"))
        row1.add_widget(LegendRow(symbol="mute", text="глушение"))
        row2 = BoxLayout(orientation='horizontal', size_hint_y=0.30, spacing=15)
        row2.add_widget(LegendRow(symbol="thumb", text="большой"))
        row2.add_widget(LegendRow(symbol="index", text="указательный"))
        row2.add_widget(LegendRow(symbol="bass", text="бас"))
        row3 = BoxLayout(orientation='horizontal', size_hint_y=0.30, spacing=15)
        row3.add_widget(LegendRow(symbol="pause", text="пауза"))
        row3.add_widget(Widget())
        row3.add_widget(Widget())
        self.add_widget(row1)
        self.add_widget(row2)
        self.add_widget(row3)

class LearnScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)

        self.chords = CHORDS
        self.strums = STROKES #словари аккордов и боя, импортированы из соотв файлов

        title = Label(
            text="ОБУЧЕНИЕ",
            font_size=24,
            size_hint_y=0.08,
            color=(0.9, 0.7, 0.2, 1)
        )
        self.add_widget(title)

        self.tabs = TabbedPanel(do_default_tab=False)
        self.tabs.size_hint_y = 0.85

        tab_chords = TabbedPanelItem(text="Аккорды")
        tab_chords.add_widget(self._build_chords_grid())

        tab_strums = TabbedPanelItem(text="Бой")
        tab_strums.add_widget(self._build_strums_grid())

        self.tabs.add_widget(tab_chords)
        self.tabs.add_widget(tab_strums)
        self.tabs.default_tab = tab_chords
        self.add_widget(self.tabs)

        btn_back = Button(
            text="НАЗАД К ТЮНЕРУ",
            size_hint_y=0.07,
            background_color=(0.5, 0.3, 0.1, 1)
        )
        btn_back.bind(on_press=self.go_back)
        self.add_widget(btn_back)

        self.parent_app = None

    def go_back(self, instance):
        if self.parent_app:
            self.parent_app.show_tuner()

    def _build_chords_grid(self): # сетка аккордов
        layout = GridLayout(cols=3, spacing=10, padding=10)
        layout.bind(minimum_height=layout.setter('height'))
        for name in self.chords:
            card = ChordCard(chord_name=name)
            card.bind(on_press=self.show_chord)
            layout.add_widget(card)
        scroll = ScrollView()
        scroll.add_widget(layout)
        return scroll

    def _build_strums_grid(self): #сетка боя
        layout = GridLayout(cols=2, spacing=10, padding=10)
        layout.bind(minimum_height=layout.setter('height'))
        for name in self.strums:
            card = StrumCard(strum_name=name)
            card.bind(on_press=self.show_strum)
            layout.add_widget(card)
        scroll = ScrollView()
        scroll.add_widget(layout)
        return scroll

    def show_chord(self, instance): #показ аккорда
        chord = self.chords.get(instance.chord_name, {})
        notes = chord.get("notes", [])
        content = BoxLayout(orientation='vertical', padding=20, spacing=10) #складывание карточек
        content.add_widget(Label(
            text=f"{chord.get('name', instance.chord_name)}",
            font_size=28,
            color=(0.9, 0.7, 0.2, 1),
            size_hint_y=0.15
        ))

        content.add_widget(Label(
            text=f"Ноты: {', '.join(notes)}",
            font_size=18,
            color=(0.9, 0.9, 0.9, 1),
            size_hint_y=0.10
        ))

        fretboard = ChordFretboard(chord_name=instance.chord_name, notes=notes) #гриф с аккордом
        content.add_widget(fretboard)
        btn_close = Button(
            text="ЗАКРЫТЬ",
            size_hint_y=0.12,
            background_color=(0.5, 0.3, 0.1, 1)
        )
        content.add_widget(btn_close)
        popup = Popup( #всплывающее окно
            title=chord.get('name', instance.chord_name),
            content=content,
            size_hint=(0.9, 0.85)
        )
        btn_close.bind(on_press=popup.dismiss)
        popup.open()

    def show_strum(self, instance): #аналогично для боя
        strum = self.strums.get(instance.strum_name, {})
        pattern = strum.get("pattern", [])
        description = strum.get("description", "")
        tempo = strum.get("tempo", "")
        content = BoxLayout(orientation='vertical', padding=10, spacing=5)
        content.add_widget(Label(
            text=instance.strum_name,
            font_size=26,
            color=(0.5, 0.8, 1, 1),
            size_hint_y=0.10
        ))

        content.add_widget(Label(
            text=f"Темп: {tempo}",
            font_size=18,
            color=(0.7, 0.7, 0.7, 1),
            size_hint_y=0.06
        ))

        strum_view = StrumView(pattern=pattern)
        strum_view.size_hint_y = 0.30
        content.add_widget(strum_view)
        content.add_widget(Label(
            text=description,
            font_size=16,
            color=(0.6, 0.6, 0.6, 1),
            size_hint_y=0.08
        ))
        legend = LegendView(size_hint_y=0.36)
        content.add_widget(legend)
        btn_close = Button(
            text="ЗАКРЫТЬ",
            size_hint_y=0.10,
            background_color=(0.3, 0.4, 0.5, 1)
        )
        content.add_widget(btn_close)

        popup = Popup(
            title=instance.strum_name,
            content=content,
            size_hint=(0.95, 0.85)
        )
        btn_close.bind(on_press=popup.dismiss)
        popup.open()


class MainWindow(BoxLayout): #главное окно тюнера
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.padding = [10, 5, 10, 5]
        self.spacing = 5

        btn_learn = Button(
            text="ОБУЧЕНИЕ",
            size_hint_y=0.05,
            background_color=(0.3, 0.6, 0.3, 1)
        )
        btn_learn.bind(on_press=self.show_learn)
        self.add_widget(btn_learn)

        self.add_widget(Label(
            text="ГИТАРНЫЙ ТЮНЕР",
            font_size=22,
            size_hint_y=0.06,
            color=(0.9, 0.7, 0.2, 1)
        ))

        self.selector = StringSelector()
        self.add_widget(self.selector)
        self.tuner = TunerScale()
        self.tuner.size_hint_y = 0.15
        self.add_widget(self.tuner)
        self.status = Label(
            text="Играйте ноту...",
            font_size=14,
            size_hint_y=0.04,
            color=(0.8, 0.8, 0.8, 1)
        )
        self.add_widget(self.status)
        self.guitar = GuitarView()
        self.guitar.size_hint_y = 0.70
        self.add_widget(self.guitar)
        self.parent_app = None

    def show_learn(self, instance):
        if self.parent_app:
            self.parent_app.show_learn()


class GuitarTunerApp(App):
    def build(self): #создаёт и запускает захват звука
        Window.size = (500, 750)
        Window.minimum_width = 400
        Window.minimum_height = 600
        self.title = "Гитарный тюнер"
        self.audio = AudioAnalyzer()
        self.audio.start()
        self.tuner_screen = MainWindow()
        self.tuner_screen.parent_app = self
        self.learn_screen = LearnScreen()
        self.learn_screen.parent_app = self
        self.current_screen = self.tuner_screen
        Clock.schedule_interval(self.update_tuner, 0.05) #проверяет звук 20 раз в секунду
        return self.current_screen

    def show_learn(self):
        self.root.clear_widgets() #очищает текущий экран
        self.root.add_widget(self.learn_screen) #переходит на экран обучения
        self.current_screen = self.learn_screen

    def show_tuner(self):
        self.root.clear_widgets()
        self.root.add_widget(self.tuner_screen)
        self.current_screen = self.tuner_screen

    def update_tuner(self, dt):
        if self.current_screen != self.tuner_screen:
            return

        freq = self.audio.get_frequency() #определение частоты
        if freq <= 0:
            self.tuner_screen.status.text = "Играйте ноту..."
            return

        string, note, deviation = self.audio.find_closest_string(freq) #нахождение ближайшей к звуку струны
        
        if string is None: #далеко от всех струн
            self.tuner_screen.status.text = f"Частота: {freq:.1f} Гц"
            return
        
        self.tuner_screen.tuner.set_deviation(deviation, note, string) #обновление линейки
        self.tuner_screen.guitar.set_active_string(string)

        if abs(deviation) < 0.02:
            self.tuner_screen.guitar.set_string_tuned(string, True)
            self.tuner_screen.status.text = f"{note} ✓"
        else:
            self.tuner_screen.guitar.set_string_tuned(string, False)
            direction = "выше" if deviation < 0 else "ниже"
            self.tuner_screen.status.text = f"{note} — {direction}"


if __name__ == "__main__":
    GuitarTunerApp().run()