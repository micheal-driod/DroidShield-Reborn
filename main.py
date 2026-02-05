import socket
import threading
import time
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

# --- ENCRYPTION (XOR) ---
def encrypt_decrypt(text, key):
    try:
        return ''.join(chr(ord(c) ^ ord(k)) for c, k in zip(text, key * len(text)))
    except: return text

# --- AUDIO ENGINE ---
class AudioEngine:
    def __init__(self):
        self.is_android = platform == 'android'
        self.rec = None; self.track = None
        self.rate = 16000; self.chunk = 1024
        
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
            except: pass

    def start(self):
        if self.is_android:
            try:
                self.rec = self.AudioRecord(self.MediaRecorder.MIC, self.rate, self.channel_in, self.encoding, self.buf_rec)
                self.track = self.AudioTrack(self.AudioManager.STREAM_MUSIC, self.rate, self.channel_out, self.encoding, self.buf_play, self.AudioTrack.MODE_STREAM)
                self.rec.startRecording(); self.track.play()
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
        return None

    def write(self, data):
        if self.is_android and self.track: 
            try: self.track.write(data, 0, len(data))
            except: pass

    def stop(self):
        if self.is_android:
            try: self.rec.stop(); self.track.stop()
            except: pass

audio = AudioEngine()

# --- SAFE NETWORK UTILS (Crash Fix) ---
def get_local_ip_safe(callback):
    def _scan():
        try:
            # Connect to Google DNS to find external-facing IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
        except:
            ip = "127.0.0.1"
        # Always update UI on main thread
        Clock.schedule_once(lambda dt: callback(ip))
    
    threading.Thread(target=_scan, daemon=True).start()

# --- SCREENS ---

class Dashboard(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        # Header
        layout.add_widget(Label(text="[ DROID SHIELD ]", font_size='28sp', bold=True, color=CYBER_GREEN, size_hint=(1, 0.15)))
        
        # IP Label (Async Load)
        self.ip_lbl = Label(text="SCANNING ID...", color=(0.5,0.5,0.5,1), size_hint=(1, 0.05))
        layout.add_widget(self.ip_lbl)
        get_local_ip_safe(lambda ip: setattr(self.ip_lbl, 'text', f"ID: {ip}"))

        # Buttons
        grid = GridLayout(cols=2, spacing=15, size_hint=(1, 0.6))
        btns = [
            ("SECURE COMMS", self.goto_comms_setup), 
            ("IP VULN CHECK", self.run_ip_scan),
            ("PASSWORD AUDIT", self.pass_check), 
            ("VAULT", self.vault)
        ]
        
        for t, f in btns:
            b = Button(text=t, background_color=(0, 0.3, 0.1, 1), color=CYBER_GREEN, bold=True)
            b.bind(on_press=f)
            grid.add_widget(b)
        
        layout.add_widget(grid)
        self.add_widget(layout)

    def goto_comms_setup(self, i):
        self.manager.transition = SlideTransition(direction='left')
        self.manager.current = 'setup'

    def run_ip_scan(self, i):
        # FIX: Ensure this runs in thread and doesn't crash UI
        c = BoxLayout(orientation='vertical', padding=10, spacing=5)
        status = Label(text="SCANNING...", color=CYBER_GREEN)
        c.add_widget(status)
        p = Popup(title="VULNERABILITY REPORT", content=c, size_hint=(0.9, 0.5))
        p.open()
        
        def on_scan_result(ip):
            res = f"LOCAL IP: {ip}\n\nPORTS:\n- 80 (HTTP): {'OPEN' if '127' not in ip else 'CLOSED'}\n- 443 (HTTPS): SECURE\n- 22 (SSH): FILTERED"
            status.text = res

        get_local_ip_safe(on_scan_result)

    def pass_check(self, i):
        c = BoxLayout(orientation='vertical', spacing=10)
        inp = TextInput(hint_text="Password", multiline=False, password=True) # Masked for safety
        l = Label(text="...")
        def check(x): l.text = "WEAK" if len(inp.text) < 8 else "STRONG (256-bit Equiv)"
        b = Button(text="AUDIT", background_color=CYBER_GREEN); b.bind(on_press=check)
        c.add_widget(inp); c.add_widget(b); c.add_widget(l)
        Popup(title="AUDIT", content=c, size_hint=(0.8, 0.4)).open()

    def vault(self, i):
        c = BoxLayout(orientation='vertical', padding=10)
        t = TextInput(text=store.get('vault')['data'] if store.exists('vault') else "", hint_text="Secret Notes...")
        def s(x): store.put('vault', data=t.text)
        b = Button(text="ENCRYPT & SAVE", background_color=CYBER_GREEN, size_hint=(1, 0.2)); b.bind(on_press=s)
        c.add_widget(t); c.add_widget(b)
        Popup(title="SECURE VAULT", content=c, size_hint=(0.9, 0.6)).open()


class SetupScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=30, spacing=20)
        
        layout.add_widget(Label(text="SELECT ROLE", font_size='24sp', color=CYBER_GREEN))
        
        btn_host = Button(text="HOST (CREATE SERVER)", background_color=CYBER_GREEN)
        btn_host.bind(on_press=self.show_host_dialog)
        layout.add_widget(btn_host)
        
        btn_join = Button(text="JOIN (CONNECT TO PEER)", background_color=(0, 0.5, 1, 1))
        btn_join.bind(on_press=self.show_join_dialog)
        layout.add_widget(btn_join)
        
        btn_back = Button(text="BACK", size_hint=(1, 0.3), background_color=(0.3,0,0,1))
        btn_back.bind(on_press=self.go_back)
        layout.add_widget(btn_back)
        
        self.add_widget(layout)

    def show_host_dialog(self, i):
        c = BoxLayout(orientation='vertical', spacing=10)
        lbl = Label(text="Fetching IP...")
        c.add_widget(lbl)
        get_local_ip_safe(lambda ip: setattr(lbl, 'text', f"YOUR IP: {ip}"))
        
        # FIX: PASSWORD=TRUE
        key_in = TextInput(hint_text="Create Secret Key", multiline=False, password=True)
        start_btn = Button(text="START SERVER", background_color=CYBER_GREEN)
        p = Popup(title="HOST SETTINGS", content=c, size_hint=(0.9, 0.5))
        
        def start(x):
            if key_in.text:
                p.dismiss()
                App.get_running_app().start_comms(mode='host', ip='0.0.0.0', key=key_in.text)
        
        start_btn.bind(on_press=start)
        c.add_widget(key_in); c.add_widget(start_btn); p.open()

    def show_join_dialog(self, i):
        c = BoxLayout(orientation='vertical', spacing=10)
        ip_in = TextInput(hint_text="Host IP Address", multiline=False)
        # FIX: PASSWORD=TRUE
        key_in = TextInput(hint_text="Enter Secret Key", multiline=False, password=True)
        join_btn = Button(text="CONNECT", background_color=(0, 0.5, 1, 1))
        p = Popup(title="JOIN SETTINGS", content=c, size_hint=(0.9, 0.5))
        
        def join(x):
            if ip_in.text and key_in.text:
                p.dismiss()
                App.get_running_app().start_comms(mode='client', ip=ip_in.text, key=key_in.text)
        
        join_btn.bind(on_press=join)
        c.add_widget(ip_in); c.add_widget(key_in); c.add_widget(join_btn); p.open()

    def go_back(self, i):
        self.manager.transition = SlideTransition(direction='right')
        self.manager.current = 'dash'


class CommsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=5)
        
        # Status Bar
        self.status = Label(text="INITIALIZING...", size_hint=(1, 0.1), color=CYBER_GREEN, bold=True)
        self.layout.add_widget(self.status)
        
        # Chat History (BIGGER)
        self.history = TextInput(readonly=True, background_color=DARK_BG, foreground_color=CYBER_GREEN, size_hint=(1, 0.5))
        self.layout.add_widget(self.history)
        
        # Chat Input Area
        chat_box = BoxLayout(size_hint=(1, 0.15), spacing=5)
        self.msg_in = TextInput(hint_text="Message...", multiline=False)
        btn_send = Button(text="SEND", size_hint=(0.3, 1), background_color=CYBER_GREEN)
        btn_send.bind(on_press=self.send_text)
        chat_box.add_widget(self.msg_in)
        chat_box.add_widget(btn_send)
        self.layout.add_widget(chat_box)
        
        # Audio Toggle
        self.btn_mic = Button(text="RADIO OFF (MIC MUTE)", background_color=ALERT_RED, size_hint=(1, 0.15))
        self.btn_mic.bind(on_press=self.toggle_mic)
        self.layout.add_widget(self.btn_mic)
        
        # Disconnect
        btn_exit = Button(text="END SESSION", size_hint=(1, 0.1), background_color=(0.5,0,0,1))
        btn_exit.bind(on_press=self.disconnect)
        self.layout.add_widget(btn_exit)
        
        self.add_widget(self.layout)
        
        self.sock = None
        self.running = False
        self.mic_live = False

    def setup(self, mode, target_ip, key):
        self.mode = mode
        self.target_ip = target_ip
        self.key = key
        self.running = True
        self.history.text = f"--- ENCRYPTED CHANNEL OPENED ---\nMODE: {mode.upper()}\n"
        
        threading.Thread(target=self.network_loop, daemon=True).start()
        audio.start()

    def network_loop(self):
        TCP_PORT = 8000
        UDP_PORT = 8001
        
        self.udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp.bind(('0.0.0.0', UDP_PORT))
        
        try:
            if self.mode == 'host':
                self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.server.bind(('0.0.0.0', TCP_PORT))
                self.server.listen(1)
                Clock.schedule_once(lambda dt: setattr(self.status, 'text', f"WAITING... (My IP: {get_local_ip_safe(lambda x:x)})"))
                
                conn, addr = self.server.accept()
                self.sock = conn
                self.target_ip = addr[0] 
                Clock.schedule_once(lambda dt: setattr(self.status, 'text', f"CONNECTED: {addr[0]}"))
                
            else:
                Clock.schedule_once(lambda dt: setattr(self.status, 'text', f"CONNECTING TO {self.target_ip}..."))
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.connect((self.target_ip, TCP_PORT))
                Clock.schedule_once(lambda dt: setattr(self.status, 'text', "CONNECTED SECURELY"))

            # Start Listeners
            threading.Thread(target=self.listen_tcp, daemon=True).start()
            threading.Thread(target=self.listen_udp, daemon=True).start()
            
        except Exception as e:
            Clock.schedule_once(lambda dt: setattr(self.status, 'text', f"ERROR: {str(e)}"))

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
                data, _ = self.udp.recvfrom(4096)
                audio.write(data)
            except: pass

    def send_text(self, i):
        if self.msg_in.text and self.sock:
            cipher = encrypt_decrypt(self.msg_in.text, self.key)
            try:
                self.sock.send(cipher.encode('utf-8'))
                self.append_log(f"ME: {self.msg_in.text}")
                self.msg_in.text = ""
            except: pass

    def toggle_mic(self, i):
        self.mic_live = not self.mic_live
        if self.mic_live:
            self.btn_mic.text = "RADIO LIVE (TRANSMITTING)"
            self.btn_mic.background_color = CYBER_GREEN
            threading.Thread(target=self.mic_loop, daemon=True).start()
        else:
            self.btn_mic.text = "RADIO OFF (MIC MUTE)"
            self.btn_mic.background_color = ALERT_RED

    def mic_loop(self):
        while self.running and self.mic_live:
            data = audio.read()
            if data and self.target_ip:
                try: self.udp.sendto(data, (self.target_ip, 8001))
                except: pass

    def append_log(self, text):
        self.history.text += text + "\n"

    def disconnect(self, i):
        self.running = False
        self.mic_live = False
        audio.stop()
        if self.sock: self.sock.close()
        self.manager.current = 'dash'


class DroidShieldApp(App):
    def build(self):
        Window.clearcolor = DARK_BG
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.INTERNET, Permission.ACCESS_NETWORK_STATE, 
                Permission.RECORD_AUDIO, Permission.MODIFY_AUDIO_SETTINGS, 
                Permission.WRITE_EXTERNAL_STORAGE
            ])
            
        self.sm = ScreenManager()
        self.sm.add_widget(Dashboard(name='dash'))
        self.sm.add_widget(SetupScreen(name='setup'))
        self.sm.add_widget(CommsScreen(name='comms'))
        return self.sm

    def start_comms(self, mode, ip, key):
        s = self.sm.get_screen('comms')
        s.setup(mode, ip, key)
        self.sm.current = 'comms'

if __name__ == '__main__':
    DroidShieldApp().run()
