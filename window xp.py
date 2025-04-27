from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics.texture import Texture
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from datetime import datetime
from threading import Thread
import sounddevice as sd
import cv2
import os

Window.clearcolor = (1, 1, 1, 1)
Window.size = (360, 640)

# Make folder to save photos
if not os.path.exists('Gallery'):
    os.makedirs('Gallery')

class CircularImage(Widget):
    def __init__(self, source, **kwargs):
        super().__init__(**kwargs)
        self.source = source
        with self.canvas:
            self.img = Image(source=self.source, allow_stretch=True, keep_ratio=False, size=self.size, pos=self.pos)
        self.bind(pos=self.update_img, size=self.update_img)

    def update_img(self, *args):
        self.canvas.clear()
        with self.canvas:
            self.img = Image(source=self.source, allow_stretch=True, keep_ratio=False, size=self.size, pos=self.pos)

class ImageButton(ButtonBehavior, BoxLayout):
    def __init__(self, source, text, on_press_action=None, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.spacing = 5
        self.padding = 10
        self.size_hint_y = None
        self.height = 100

        self.image = CircularImage(source=source, size_hint=(None, None), size=(60, 60))
        self.label = Label(text=text, size_hint=(1, None), height=20, color=(0, 0, 0, 1), font_size=14)

        wrapper = BoxLayout(orientation='vertical', size_hint=(None, None), size=(60, 80))
        wrapper.add_widget(self.image)
        wrapper.add_widget(self.label)

        self.add_widget(wrapper)

        if on_press_action:
            self.bind(on_press=on_press_action)

class MicTester(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.bg_image = Image(source='mic.png', allow_stretch=True, keep_ratio=False, size_hint=(1, 1))
        self.add_widget(self.bg_image)

        self.button_layout = BoxLayout(size_hint=(1, 0.2), pos_hint={'top': 1}, spacing=10, padding=10)
        self.start_btn = Button(text='🎤 Start Mic', font_size=20)
        self.stop_btn = Button(text='🛑 Stop Mic', font_size=20, disabled=True)

        self.start_btn.bind(on_press=self.start_mic)
        self.stop_btn.bind(on_press=self.stop_mic)

        self.button_layout.add_widget(self.start_btn)
        self.button_layout.add_widget(self.stop_btn)
        self.add_widget(self.button_layout)

        self.running = False
        self.stream = None
        self.output_stream = None

    def start_mic(self, instance):
        self.running = True
        self.start_btn.disabled = True
        self.stop_btn.disabled = False
        Thread(target=self.run_mic).start()

    def stop_mic(self, instance):
        self.running = False
        self.start_btn.disabled = False
        self.stop_btn.disabled = True
        if self.stream:
            self.stream.stop()
            self.stream.close()
        if self.output_stream:
            self.output_stream.stop()
            self.output_stream.close()

    def callback(self, indata, frames, time, status):
        if self.running and self.output_stream:
            self.output_stream.write(indata)

    def run_mic(self):
        try:
            self.output_stream = sd.OutputStream(samplerate=44100, channels=1)
            self.output_stream.start()
            self.stream = sd.InputStream(callback=self.callback, channels=1, samplerate=44100)
            self.stream.start()
        except Exception as e:
            print(f"Mic error: {e}")

class CalculatorScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        self.result = TextInput(multiline=False, readonly=True, halign="right", font_size=32)
        layout.add_widget(self.result)

        buttons = [["7", "8", "9", "/"], ["4", "5", "6", "*"], ["1", "2", "3", "-"], [".", "0", "C", "+"]]
        grid = GridLayout(cols=4, spacing=10, size_hint=(1, 0.6))
        for row in buttons:
            for label in row:
                btn = Button(text=label, font_size=24)
                btn.bind(on_press=self.on_button_press)
                grid.add_widget(btn)

        layout.add_widget(grid)
        equals_button = Button(text="=", font_size=24, size_hint=(1, 0.2))
        equals_button.bind(on_press=self.on_solution)
        layout.add_widget(equals_button)
        self.add_widget(layout)

    def on_button_press(self, instance):
        if instance.text == "C":
            self.result.text = ""
        else:
            self.result.text += instance.text

    def on_solution(self, instance):
        try:
            self.result.text = str(eval(self.result.text))
        except Exception:
            self.result.text = "Error"

class ClockScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', spacing=10, padding=20)
        self.date_label = Label(text='', font_size=36, color=(0, 0, 0, 1))
        self.time_label = Label(text='', font_size=48, color=(0, 0, 0, 1))
        layout.add_widget(self.date_label)
        layout.add_widget(self.time_label)
        self.add_widget(layout)
        Clock.schedule_interval(self.update_datetime, 1)
        self.update_datetime(0)

    def update_datetime(self, dt):
        now = datetime.now()
        self.date_label.text = now.strftime('%d-%m-%Y')
        self.time_label.text = now.strftime('%I:%M:%S %p')

class MicScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_widget(MicTester())

class CameraScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical')
        self.capture = cv2.VideoCapture(0)
        self.img_widget = Image()
        layout.add_widget(self.img_widget)

        capture_btn = Button(text="📸 Capture Photo", size_hint=(1, 0.2))
        capture_btn.bind(on_press=self.capture_photo)
        layout.add_widget(capture_btn)

        self.add_widget(layout)
        Clock.schedule_interval(self.update, 1.0 / 30.0)

    def update(self, dt):
        ret, frame = self.capture.read()
        if ret:
            buf = cv2.flip(frame, 0).tobytes()
            tex = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
            tex.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
            self.img_widget.texture = tex

    def capture_photo(self, instance):
        ret, frame = self.capture.read()
        if ret:
            filename = f"Gallery/photo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            cv2.imwrite(filename, frame)
            print(f"Photo saved: {filename}")

    def on_leave(self):
        self.capture.release()

class GalleryScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical')
        scroll = ScrollView()
        grid = GridLayout(cols=2, spacing=10, size_hint_y=None)
        grid.bind(minimum_height=grid.setter('height'))

        for img_file in os.listdir('Gallery'):
            if img_file.endswith('.png'):
                img = Image(source=os.path.join('Gallery', img_file), size_hint_y=None, height=150)
                grid.add_widget(img)

        scroll.add_widget(grid)
        layout.add_widget(scroll)
        self.add_widget(layout)

class HomeScreen(Screen):
    def __init__(self, screen_manager, **kwargs):
        super().__init__(**kwargs)
        layout = FloatLayout()
        self.bg = Image(source='background.png', allow_stretch=True, keep_ratio=False)
        layout.add_widget(self.bg)
        box = BoxLayout(orientation='vertical', padding=10, spacing=15, size_hint=(None, 1), width=100, pos_hint={'x': 0, 'top': 1})

        def open_screen(name):
            screen_manager.current = name

        apps = [
            ('calc.png', 'Calculator', lambda i: open_screen('calculator')),
            ('camera.png', 'Camera', lambda i: open_screen('camera')),
            ('files.png', 'Gallery', lambda i: open_screen('gallery')),
            ('gallery.png', 'Gallery', lambda i: open_screen('gallery')),
            ('clock.png', 'Clock', lambda i: open_screen('clock')),
            ('mic.png', 'Mic', lambda i: open_screen('mic'))
        ]

        for icon, label, action in apps:
            box.add_widget(ImageButton(source=icon, text=label, on_press_action=action))

        layout.add_widget(box)
        self.add_widget(layout)

class AppLauncher(App):
    def build(self):
        self.sm = ScreenManager()
        self.sm.add_widget(HomeScreen(screen_manager=self.sm, name='home'))
        self.sm.add_widget(CalculatorScreen(name='calculator'))
        self.sm.add_widget(ClockScreen(name='clock'))
        self.sm.add_widget(MicScreen(name='mic'))
        self.sm.add_widget(CameraScreen(name='camera'))
        self.sm.add_widget(GalleryScreen(name='gallery'))
        Window.bind(on_keyboard=self.on_back_button)
        return self.sm

    def on_back_button(self, window, key, *args):
        if key == 27:
            if self.sm.current != 'home':
                self.sm.transition.direction = 'right'
                self.sm.current = 'home'
                return True
            else:
                App.get_running_app().stop()
                return True
        return False

if __name__ == '__main__':
    AppLauncher().run()
