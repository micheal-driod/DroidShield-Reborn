from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.core.window import Window

class DroidShieldApp(App):
    def build(self):
        Window.clearcolor = (0.1, 0.1, 0.1, 1) # Dark Grey Background
        
        # Create a layout to hold things
        layout = BoxLayout(orientation='vertical', padding=50, spacing=20)
        
        # Add a Label
        self.label = Label(text="DroidShield Ready", font_size='24sp', color=(0,1,0,1))
        layout.add_widget(self.label)
        
        # Add a Button
        btn = Button(text="Click Me", size_hint=(1, 0.2), background_color=(0,0.5,1,1))
        btn.bind(on_press=self.on_button_click)
        layout.add_widget(btn)
        
        return layout

    def on_button_click(self, instance):
        self.label.text = "System Secure! 🛡️"
        self.label.color = (0.2, 1, 1, 1) # Cyan

if __name__ == '__main__':
    DroidShieldApp().run()
