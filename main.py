from kivy.app import App
from kivy.uix.label import Label
from kivy.core.window import Window

class DroidShieldApp(App):
    def build(self):
        # Set a background color (optional, just for visual confirmation)
        Window.clearcolor = (0.1, 0.1, 0.1, 1)
        return Label(
            text="DroidShield Active\n\nBuild Successful!",
            halign="center",
            font_size="24sp",
            color=(0, 1, 0, 1)  # Green text
        )

if __name__ == '__main__':
    DroidShieldApp().run()
