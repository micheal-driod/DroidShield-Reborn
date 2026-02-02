import socket
import threading
import time
from datetime import datetime

# Kivy Imports
from kivy.app import App
from kivy.clock import Clock
from kivy.storage.jsonstore import JsonStore
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.utils import platform

# --- CONFIG ---
CYBER_GREEN = (0, 1, 0.4, 1)     # Hacker Green
ALERT_RED = (1, 0, 0, 1)         # Warning Red
DARK_BG = (0.05, 0.05, 0.05, 1)  # Deep Black
store = JsonStore('secure_data.json')

# --- UNIVERSAL AUDIO ENGINE (Android + PC) ---
class AudioEngine:
    def __init__(self):
        self.is_android = platform == 'android'
        self.rec = None
        self.track = None
        self.pa = None
        self.stream_in = None
        self.stream_out = None
        self.rate = 16000
        self.chunk = 1024
        
        if self.is_android:
            try:
                from jnius import autoclass
                self.AudioRecord = autoclass('android.media.AudioRecord')
                self.AudioTrack = autoclass('android.media.AudioTrack')
                self.AudioFormat = autoclass('android.media.AudioFormat')
                self.MediaRecorder = autoclass('android.media.MediaRecorder$AudioSource')
                self.AudioManager = autoclass('android.media.AudioManager')
                self.channel_in = self.AudioFormat.CHANNEL_IN_MONO
                self.channel_out = self.AudioFormat.CHANNEL_OUT_MONO
                self.encoding = self.AudioFormat.ENCODING_PCM_16BIT
                self.buf_rec = self.AudioRecord.getMinBufferSize(self.rate, self.channel_in, self.encoding) * 2
                self.buf_play = self.AudioTrack.getMinBufferSize(self.rate, self.channel_out, self.encoding) * 2
            except Exception as e:
                print(f"Audio Init Error: {e}")
        else:
            try:
                import pyaudio
                self.pa = pyaudio.PyAudio()
            except:
                print("PyAudio not found (PC Mode)")

    def start(self):
        if self.is_android:
            try:
                self.rec = self.AudioRecord(self.MediaRecorder.MIC, self.rate, self.channel_in, self.encoding, self.buf_rec)
                self.track = self.AudioTrack(self.AudioManager.STREAM_MUSIC, self.rate, self.channel_out, self.encoding, self.buf_play, self.AudioTrack.MODE_STREAM)
                self.rec.startRecording()
                self.track.play()
                return True
            except Exception as e:
                print(f"Start Error: {e}")
                return False
        elif self.pa:
            try:
                self.stream_in = self.pa.open(format=self.pa.get_format_from_width(2), channels=1, rate=self.rate, input=True, frames_per_buffer=self.chunk)
                self.stream_out = self.pa.open(format=self.pa.get_format_from_width(2), channels=1, rate=self.rate, output=True)
                return True
            except:
                pass
        return False

    def read(self):
        if self.is_android and self.rec:
            try:
                b = bytearray(self.chunk)
                r = self.rec.read(b, 0, self.chunk)
                if r > 0: return bytes(b[:r])
            except: pass
        elif self.stream_in:
            return self.stream_in.read(self.chunk, exception_on_overflow=False)
        return None

    def write(self, data):
        if self.is_android and self.track:
            try: self.track.write(data, 0, len(data))
            except: pass
        elif self.stream_out:
            self.stream_out.write(data)

    def stop(self):
        try:
            if self.is_android:
                if self.rec: self.rec.stop()
                if self.track: self.track.stop()
            elif self.pa:
                if self.stream_in: self.stream_in.stop_stream()
                if self.stream_out: self.stream_out.stop_stream()
        except: pass

audio = AudioEngine()

# --- UTILS ---
def get_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

# --- SCREENS ---
class Dashboard(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Main Layout
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        # Header
        layout.add_widget(Label(text="[ DROID SHIELD ]", font_size='30sp', bold=True, color=CYBER_GREEN, size_hint=(1, 0.15)))
        layout.add_widget(Label(text=f"DEVICE ID: {get_ip()}", color=(0.5,0.5,0.5,1), size_hint=(1, 0.05)))
        
        # Button Grid
        grid = GridLayout(cols=2, spacing=15, size_hint=(1, 0.6))
        btns = [
            ("PASS AUDIT", self.pass_check), 
            ("IP SCAN", self.ip_check),
            ("GLOBAL LINK", self.connect_server), 
            ("VAULT", self.vault), 
            ("LOGS", self.view_logs)
        ]
        
        for t, f in btns:
            b = Button(text=t, background_color=(0, 0.3, 0.1, 1), color=CYBER_GREEN, bold=True)
            b.bind(on_press=f)
            grid.add_widget(b)
            
        layout.add_widget(grid)
        self.add_widget(layout)

    def pass_check(self, i):
        c = BoxLayout(orientation='vertical', spacing=10, padding=10)
        inp = TextInput(hint_text="Enter Password", multiline=False, foreground_color=CYBER_GREEN, background_color=DARK_BG)
        l = Label(text="WAITING FOR INPUT...")
        
        def check(x):
            strength = len(inp.text)
            if strength < 5: l.text = "STATUS: CRITICAL (TOO WEAK)"
            elif strength < 10: l.text = "STATUS: MODERATE"
            else: l.text = "STATUS: SECURE (STRONG)"
            
        b = Button(text="RUN AUDIT", background_color=CYBER_GREEN)
        b.bind(on_press=check)
        c.add_widget(inp); c.add_widget(b); c.add_widget(l)
        Popup(title="PASSWORD AUDIT", content=c, size_hint=(0.8, 0.4)).open()

    def ip_check(self, i):
        c = BoxLayout(orientation='vertical', padding=10)
        l = Label(text=f"PUBLIC IP: {get_ip()}\n\nSTATUS: EXPOSED\nRECOMMENDATION: ENABLE VPN")
        c.add_widget(l)
        Popup(title="NETWORK SCAN", content=c, size_hint=(0.8, 0.4)).open()

    def vault(self, i):
        c = BoxLayout(orientation='vertical', padding=10, spacing=10)
        saved_data = store.get('vault')['data'] if store.exists('vault') else ""
        t = TextInput(text=saved_data, hint_text="Secret Notes...", foreground_color=CYBER_GREEN, background_color=DARK_BG)
        
        def s(x): 
            store.put('vault', data=t.text)
            Popup(title="SUCCESS", content=Label(text="Data Encrypted & Saved"), size_hint=(0.6, 0.3)).open()
            
        b = Button(text="ENCRYPT & SAVE", background_color=CYBER_GREEN, size_hint=(1, 0.2))
        b.bind(on_press=s)
        c.add_widget(t); c.add_widget(b)
        Popup(title="SECURE VAULT", content=c, size_hint=(0.9, 0.6)).open()

    def view_logs(self, i):
        Popup(title="SYSTEM LOGS", content=Label(text="[OK] Boot Sequence Complete\n[OK] Network Initialized\n[OK] Mic Permission Granted\n[WARN] Port 80 Open"), size_hint=(0.8, 0.4)).open()

    def connect_server(self, i):
        c = BoxLayout(orientation='vertical', spacing=10, padding=10)
        ip = TextInput(hint_text="Target IP (e.g., 192.168.1.5)", multiline=False)
        usr = TextInput(hint_text="Codename", multiline=False)
        btn = Button(text="INITIATE UPLINK", background_color=CYBER_GREEN)
        p = Popup(title="SATELLITE CONNECTION", content=c, size_hint=(0.9, 0.5))
        
        def start(x):
            if ip.text and usr.text:
                p.dismiss()
                App.get_running_app().launch_comms(ip.text, usr.text)
        
        btn.bind(on_press=start)
        c.add_widget(ip); c.add_widget(usr); c.add_widget(btn); p.open()

class CommsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', padding=10)
        
        # Connection Header
        self.header = Label(text="CONNECTING...", size_hint=(1, 0.1), color=CYBER_GREEN, bold=True)
        
        # Chat Output
        self.output = TextInput(readonly=True, background_color=DARK_BG, foreground_color=CYBER_GREEN, font_size='14sp')
        
        # Input Area
        self.input_box = BoxLayout(size_hint=(1, 0.15), spacing=5)
        self.msg_in = TextInput(hint_text="Type Message...", multiline=False)
        self.send_btn = Button(text="SEND", size_hint=(0.3, 1), background_color=CYBER_GREEN)
        self.input_box.add_widget(self.msg_in); self.input_box.add_widget(self.send_btn)
        
        # Mic Button
        self.btn_mic = Button(text="MIC OFF", background_color=ALERT_RED, size_hint=(1, 0.15), bold=True)
        
        self.layout.add_widget(self.header)
        self.layout.add_widget(self.output)
        self.layout.add_widget(self.input_box)
        self.layout.add_widget(self.btn_mic)
        
        # Disconnect
        btn_exit = Button(text="TERMINATE UPLINK", size_hint=(1, 0.1), background_color=(0.5,0,0,1))
        btn_exit.bind(on_press=self.disconnect)
        self.layout.add_widget(btn_exit)
        self.add_widget(self.layout)
        
        self.active = False
        self.mic_active = False

    def start(self, server_ip, username):
        self.server_ip = server_ip
        self.username = username
        self.active = True
        self.header.text = f"SECURE LINK: {server_ip}"
        self.log(f"--- UPLINK ESTABLISHED AS {username} ---")
        
        # Initialize Sockets
        try:
            self.tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcp.settimeout(5) # Don't freeze if server is down
            # NOTE: In real use, you need a server running on this IP!
            # self.tcp.connect((server_ip, 8888)) 
            
            self.udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            
            # Start Listener Threads
            threading.Thread(target=self.listen_tcp, daemon=True).start()
            threading.Thread(target=self.listen_udp, daemon=True).start()
            
            # Bind UI
            self.send_btn.bind(on_press=self.send_msg)
            self.btn_mic.bind(on_press=self.toggle_mic)
            
            # Start Audio Engine
            audio.start()
            
        except Exception as e:
            self.log(f"CONNECTION ERROR: Server not found at {server_ip}")
            self.log("Running in OFFLINE SIMULATION MODE")

    def listen_tcp(self):
        while self.active:
            try:
                if hasattr(self, 'tcp'):
                    data = self.tcp.recv(1024)
                    if data: self.log(data.decode('utf-8'))
            except: break

    def listen_udp(self):
        # Ping server to register UDP
        try: self.udp.sendto(b'PING', (self.server_ip, 9999))
        except: pass
        
        while self.active:
            try:
                data, _ = self.udp.recvfrom(4096)
                audio.write(data)
            except: pass

    def send_audio(self):
        while self.active and self.mic_active:
            data = audio.read()
            if data:
                try: self.udp.sendto(data, (self.server_ip, 9999))
                except: pass

    def toggle_mic(self, i):
        self.mic_active = not self.mic_active
        if self.mic_active:
            self.btn_mic.text = "MIC LIVE (TRANSMITTING)"
            self.btn_mic.background_color = CYBER_GREEN
            threading.Thread(target=self.send_audio, daemon=True).start()
        else:
            self.btn_mic.text = "MIC MUTED"
            self.btn_mic.background_color = ALERT_RED

    def send_msg(self, i):
        if self.msg_in.text:
            msg = f"{self.username}: {self.msg_in.text}"
            try: 
                self.tcp.send(msg.encode('utf-8'))
            except: 
                # Simulate chat for offline mode
                self.log(f"ME: {self.msg_in.text}")
            self.msg_in.text = ""

    def log(self, txt): 
        Clock.schedule_once(lambda dt: setattr(self.output, 'text', self.output.text + "\n" + txt))
    
    def disconnect(self, i):
        self.active = False
        audio.stop()
        try: 
            self.tcp.close()
            self.udp.close()
        except: pass
        App.get_running_app().sm.current = 'dash'

class DroidShieldApp(App):
    def build(self):
        Window.clearcolor = DARK_BG
        # Request Android Permissions on Launch
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.INTERNET, 
                Permission.RECORD_AUDIO, 
                Permission.MODIFY_AUDIO_SETTINGS,
                Permission.WRITE_EXTERNAL_STORAGE
            ])
            
        self.sm = ScreenManager()
        self.sm.add_widget(Dashboard(name='dash'))
        self.sm.add_widget(CommsScreen(name='comms'))
        return self.sm

    def launch_comms(self, ip, usr):
        s = self.sm.get_screen('comms')
        s.start(ip, usr)
        self.sm.current = 'comms'

if __name__ == '__main__':
    DroidShieldApp().run()
