import socket
import threading
import struct
import math
from kivy.app import App
from kivy.clock import Clock
from kivy.storage.jsonstore import JsonStore
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.utils import platform

# --- CONFIG ---
CYBER_GREEN = (0, 1, 0.4, 1)
ALERT_RED = (1, 0, 0, 1)
DARK_BG = (0.05, 0.05, 0.05, 1)
store = JsonStore('secure_data.json')

# --- ENCRYPTION ---
def encrypt_decrypt(text, key):
    try:
        return ''.join(chr(ord(c) ^ ord(k)) for c, k in zip(text, key * len(text)))
    except: return text

# --- ROBUST AUDIO ENGINE ---
class AudioEngine:
    def __init__(self):
        self.is_android = platform == 'android'
        self.rec = None; self.track = None
        self.pa = None; self.stream = None
        self.rate = 16000  # Standard VOIP Rate
        self.chunk = 2048  # Larger chunk for stability
        
        if self.is_android:
            try:
                from jnius import autoclass
                self.AudioRecord = autoclass('android.media.AudioRecord')
                self.AudioTrack = autoclass('android.media.AudioTrack')
                self.AudioFormat = autoclass('android.media.AudioFormat')
                self.MediaRecorder = autoclass('android.media.MediaRecorder$AudioSource')
                self.AudioManager = autoclass('android.media.AudioManager')
                
                # Config
                self.src = self.MediaRecorder.MIC
                self.stream_type = self.AudioManager.STREAM_VOICE_CALL # Louder
                self.sr = self.rate
                self.chin = self.AudioFormat.CHANNEL_IN_MONO
                self.chout = self.AudioFormat.CHANNEL_OUT_MONO
                self.enc = self.AudioFormat.ENCODING_PCM_16BIT
                
                self.min_buf_rec = self.AudioRecord.getMinBufferSize(self.sr, self.chin, self.enc) * 2
                self.min_buf_play = self.AudioTrack.getMinBufferSize(self.sr, self.chout, self.enc) * 2
            except: pass
        else:
            try:
                import pyaudio
                self.pa = pyaudio.PyAudio()
            except: self.pa = None

    def start(self):
        if self.is_android:
            try:
                self.rec = self.AudioRecord(self.src, self.sr, self.chin, self.enc, self.min_buf_rec)
                self.track = self.AudioTrack(self.stream_type, self.sr, self.chout, self.enc, self.min_buf_play, 1)
                self.rec.startRecording()
                self.track.play()
                return True
            except: return False
        elif self.pa:
            try:
                self.stream = self.pa.open(format=self.pa.get_format_from_width(2),
                                           channels=1, rate=self.rate, input=True, output=True,
                                           frames_per_buffer=self.chunk)
                return True
            except: return False
        return False

    def read(self):
        if self.is_android and self.rec:
            try:
                b = bytearray(self.chunk)
                r = self.rec.read(b, 0, self.chunk)
                if r > 0: return bytes(b[:r])
            except: pass
        elif self.stream:
            try: return self.stream.read(self.chunk, exception_on_overflow=False)
            except: pass
        return None

    def write(self, data):
        if self.is_android and self.track: 
            try: self.track.write(data, 0, len(data))
            except: pass
        elif self.stream:
            try: self.stream.write(data)
            except: pass

    def stop(self):
        if self.is_android:
            try: self.rec.stop(); self.track.stop()
            except: pass
        elif self.stream:
            try: self.stream.stop_stream(); self.stream.close()
            except: pass

audio = AudioEngine()

# --- HELPER: CALCULATE VOLUME LEVEL ---
def get_amplitude(data):
    try:
        # Convert byte data to integers to measure volume
        count = len(data) // 2
        shorts = struct.unpack(f'{count}h', data)
        sum_squares = sum(s**2 for s in shorts)
        return int(math.sqrt(sum_squares / count))
    except: return 0

# --- SAFE NETWORK UTILS ---
def get_local_ip_safe(callback):
    def _scan():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
        except: ip = "127.0.0.1"
        Clock.schedule_once(lambda dt: callback(ip))
    threading.Thread(target=_scan, daemon=True).start()

# --- SCREENS ---
class Dashboard(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="[ DROID SHIELD ]", font_size='28sp', bold=True, color=CYBER_GREEN, size_hint=(1, 0.15)))
        
        self.ip_lbl = Label(text="SCANNING ID...", color=(0.5,0.5,0.5,1), size_hint=(1, 0.05))
        layout.add_widget(self.ip_lbl)
        get_local_ip_safe(lambda ip: setattr(self.ip_lbl, 'text', f"ID: {ip}"))

        grid = GridLayout(cols=2, spacing=15, size_hint=(1, 0.6))
        btns = [("SECURE COMMS", self.goto_comms_setup), ("IP VULN CHECK", self.run_ip_scan),
                ("PASSWORD AUDIT", self.pass_check), ("VAULT", self.vault)]
        for t, f in btns:
            b = Button(text=t, background_color=(0, 0.3, 0.1, 1), color=CYBER_GREEN, bold=True); b.bind(on_press=f); grid.add_widget(b)
        layout.add_widget(grid); self.add_widget(layout)

    def goto_comms_setup(self, i): self.manager.current = 'setup'
    def run_ip_scan(self, i):
        c = BoxLayout(orientation='vertical', padding=10); c.add_widget(Label(text="SCANNING...", color=CYBER_GREEN))
        p = Popup(title="IP CHECK", content=c, size_hint=(0.9, 0.5)); p.open()
        get_local_ip_safe(lambda ip: setattr(c.children[0], 'text', f"IP: {ip}\nSTATUS: ONLINE"))
    def pass_check(self, i):
        c = BoxLayout(orientation='vertical'); t = TextInput(password=True); l = Label(text="...")
        b = Button(text="CHECK", background_color=CYBER_GREEN, on_press=lambda x: setattr(l, 'text', "WEAK" if len(t.text)<8 else "STRONG"))
        c.add_widget(t); c.add_widget(b); c.add_widget(l); Popup(title="AUDIT", content=c, size_hint=(0.8, 0.4)).open()
    def vault(self, i):
        c = BoxLayout(orientation='vertical'); t = TextInput(text=store.get('vault')['data'] if store.exists('vault') else "")
        b = Button(text="SAVE", background_color=CYBER_GREEN, on_press=lambda x: store.put('vault', data=t.text))
        c.add_widget(t); c.add_widget(b); Popup(title="VAULT", content=c, size_hint=(0.9, 0.6)).open()

class SetupScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=30, spacing=20)
        layout.add_widget(Label(text="SELECT ROLE", font_size='24sp', color=CYBER_GREEN))
        
        btn_host = Button(text="HOST", background_color=CYBER_GREEN)
        btn_host.bind(on_press=self.host_dlg)
        layout.add_widget(btn_host)
        
        btn_join = Button(text="JOIN", background_color=(0,0.5,1,1))
        btn_join.bind(on_press=self.join_dlg)
        layout.add_widget(btn_join)
        
        layout.add_widget(Button(text="BACK", background_color=(0.3,0,0,1), on_press=lambda x: setattr(self.manager, 'current', 'dash')))
        self.add_widget(layout)

    def host_dlg(self, i):
        c = BoxLayout(orientation='vertical'); l = Label(text="Fetching IP..."); c.add_widget(l)
        get_local_ip_safe(lambda ip: setattr(l, 'text', f"YOUR IP: {ip}"))
        k = TextInput(hint_text="Key", password=True)
        b = Button(text="START", background_color=CYBER_GREEN, on_press=lambda x: App.get_running_app().start_comms('host', '0.0.0.0', k.text))
        c.add_widget(k); c.add_widget(b); Popup(title="HOST", content=c, size_hint=(0.9, 0.5)).open()

    def join_dlg(self, i):
        c = BoxLayout(orientation='vertical'); ip = TextInput(hint_text="Host IP"); k = TextInput(hint_text="Key", password=True)
        b = Button(text="CONNECT", background_color=(0,0.5,1,1), on_press=lambda x: App.get_running_app().start_comms('client', ip.text, k.text))
        c.add_widget(ip); c.add_widget(k); c.add_widget(b); Popup(title="JOIN", content=c, size_hint=(0.9, 0.5)).open()

class CommsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=5)
        
        # DEBUG INFO FOR AUDIO
        self.audio_stats = Label(text="AUDIO: OFF", size_hint=(1, 0.05), color=(0.5, 0.5, 0.5, 1), font_size='10sp')
        self.layout.add_widget(self.audio_stats)

        self.status = Label(text="INIT", size_hint=(1, 0.1), color=CYBER_GREEN, bold=True)
        self.history = TextInput(readonly=True, background_color=DARK_BG, foreground_color=CYBER_GREEN, size_hint=(1, 0.45))
        
        chat_box = BoxLayout(size_hint=(1, 0.15), spacing=5)
        self.msg_in = TextInput(hint_text="Msg...", multiline=False)
        btn_send = Button(text="SEND", size_hint=(0.3, 1), background_color=CYBER_GREEN, on_press=self.send_text)
        chat_box.add_widget(self.msg_in); chat_box.add_widget(btn_send)
        
        self.btn_mic = Button(text="RADIO OFF", background_color=ALERT_RED, size_hint=(1, 0.15), on_press=self.toggle_mic)
        btn_exit = Button(text="EXIT", size_hint=(1, 0.1), background_color=(0.5,0,0,1), on_press=self.disconnect)
        
        self.layout.add_widget(self.status); self.layout.add_widget(self.history)
        self.layout.add_widget(chat_box); self.layout.add_widget(self.btn_mic); self.layout.add_widget(btn_exit)
        self.add_widget(self.layout)
        
        self.sock = None; self.running = False; self.mic_live = False

    def setup(self, mode, target_ip, key):
        self.mode = mode; self.target_ip = target_ip; self.key = key; self.running = True
        self.history.text = f"--- SECURE LINK ---\nMODE: {mode}\n"
        threading.Thread(target=self.network_loop, daemon=True).start()
        audio.start()

    def network_loop(self):
        TCP = 8000; UDP = 8001
        self.udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp.bind(('0.0.0.0', UDP))
        try:
            if self.mode == 'host':
                self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.server.bind(('0.0.0.0', TCP)); self.server.listen(1)
                Clock.schedule_once(lambda dt: setattr(self.status, 'text', "WAITING..."))
                conn, addr = self.server.accept(); self.sock = conn; self.target_ip = addr[0]
                Clock.schedule_once(lambda dt: setattr(self.status, 'text', f"CONNECTED: {addr[0]}"))
            else:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.settimeout(5); self.sock.connect((self.target_ip, TCP))
                Clock.schedule_once(lambda dt: setattr(self.status, 'text', "CONNECTED"))

            threading.Thread(target=self.listen_tcp, daemon=True).start()
            threading.Thread(target=self.listen_udp, daemon=True).start()
        except Exception as e:
            Clock.schedule_once(lambda dt: setattr(self.status, 'text', f"ERR: {str(e)}"))

    def listen_tcp(self):
        while self.running and self.sock:
            try:
                data = self.sock.recv(1024)
                if data:
                    msg = encrypt_decrypt(data.decode('utf-8'), self.key)
                    Clock.schedule_once(lambda dt, m=msg: self.append_log(f"PEER: {m}"))
            except: break

    def listen_udp(self):
        while self.running:
            try:
                data, addr = self.udp.recvfrom(4096)
                audio.write(data)
                # VISUAL FEEDBACK FOR RECEIVED AUDIO
                amp = get_amplitude(data)
                Clock.schedule_once(lambda dt: setattr(self.audio_stats, 'text', f"RX DATA: {len(data)}b | VOL: {amp}"))
            except: pass

    def send_text(self, i):
        if self.msg_in.text and self.sock:
            try:
                self.sock.send(encrypt_decrypt(self.msg_in.text, self.key).encode('utf-8'))
                self.append_log(f"ME: {self.msg_in.text}"); self.msg_in.text = ""
            except: pass

    def toggle_mic(self, i):
        self.mic_live = not self.mic_live
        if self.mic_live:
            self.btn_mic.text = "RADIO LIVE"; self.btn_mic.background_color = CYBER_GREEN
            threading.Thread(target=self.mic_loop, daemon=True).start()
        else:
            self.btn_mic.text = "RADIO OFF"; self.btn_mic.background_color = ALERT_RED

    def mic_loop(self):
        while self.running and self.mic_live:
            data = audio.read()
            if data and self.target_ip:
                try: 
                    self.udp.sendto(data, (self.target_ip, 8001))
                    # VISUAL FEEDBACK FOR MIC
                    amp = get_amplitude(data)
                    Clock.schedule_once(lambda dt: setattr(self.audio_stats, 'text', f"TX MIC: {amp}"))
                except: pass

    def append_log(self, text): self.history.text += text + "\n"
    def disconnect(self, i):
        self.running = False; self.mic_live = False; audio.stop()
        if self.sock: self.sock.close()
        self.manager.current = 'dash'

class DroidShieldApp(App):
    def build(self):
        Window.clearcolor = DARK_BG
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            request_permissions([Permission.INTERNET, Permission.ACCESS_NETWORK_STATE, Permission.RECORD_AUDIO, Permission.MODIFY_AUDIO_SETTINGS, Permission.WRITE_EXTERNAL_STORAGE])
        self.sm = ScreenManager()
        self.sm.add_widget(Dashboard(name='dash'))
        self.sm.add_widget(SetupScreen(name='setup'))
        self.sm.add_widget(CommsScreen(name='comms'))
        return self.sm
    def start_comms(self, mode, ip, key): self.sm.get_screen('comms').setup(mode, ip, key); self.sm.current = 'comms'

if __name__ == '__main__': DroidShieldApp().run()
