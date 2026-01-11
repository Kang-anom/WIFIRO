#!/usr/bin/env python3
import os
import time
import sys
import subprocess

# 1. IMPORT GLOBAL CONFIG & TOOLS
from wifipro.core import config
from wifipro.attacks.handshake import HandshakeCapture
from wifipro.attacks.eviltwin import EvilTwin
from wifipro.attacks.netcut import NetCut
from wifipro.utils.terminal import colors, UIBranding, InterfaceRenderer
from wifipro.utils.renderer import format_target_table
from wifipro.utils.maintenance import SystemMaintenance

class Menu:
    def __init__(self):
        self.colors = colors
        self.version = "3.1"
        self.author = "kang-anom"
        self.wifi = None
        self.targets = []
        self.renderer = None

    def set_wifi_engine(self, engine):
        """Injeksi engine utama ke dalam menu"""
        self.wifi = engine
        self.renderer = InterfaceRenderer(self.wifi, self.version)

    def _clear_screen(self):
        """Metode standar untuk membersihkan terminal"""
        os.system('clear' if os.name == 'posix' else 'cls')

    def _check_requirement(self, need_target=True):
        """Validasi state sebelum menjalankan serangan"""
        c = self.colors
        iface = getattr(self.wifi, 'iface', "None")
        
        if not iface or iface == "None":
            print(f"\n {c.ERR} {c.R}Required:{c.W} Please select a wireless interface first (Option 01).")
            time.sleep(2)
            return False
            
        if need_target and not self.targets:
            print(f"\n {c.WARN} {c.Y}Target List Empty:{c.W} Perform a network scan first.")
            time.sleep(2)
            return False
        return True

    def _display_saved_passwords(self):
        """Menampilkan archive password dari config.RESULT_FILE"""
        c = self.colors
        result_file = config.RESULT_FILE  # Sinkron dengan folder data/
        self._clear_screen()
        
        if self.renderer:
            self.renderer.display_system_status()
        
        print(f"\n  {c.P}{c.BOLD}[ HARVESTED CREDENTIALS ARCHIVE ]{c.NC}")
        UIBranding.draw_line()

        if not os.path.exists(result_file) or os.path.getsize(result_file) == 0:
            print(f"  {c.R} No passwords captured yet. Try Evil Twin attack.{c.NC}")
        else:
            print(f"  {c.BOLD}{'TIMESTAMP':<22} | {'CREDENTIALS':<20}{c.NC}")
            print(f"  {c.DG}{'-' * 55}{c.NC}")
            
            with open(result_file, "r") as f:
                for line in f:
                    if "Password:" in line:
                        try:
                            parts = line.split(" Password: ")
                            time_str = parts[0].strip("[] ")
                            pwd = parts[1].strip()
                            print(f"  {c.G}{time_str:<22}{c.NC} | {c.Y}{pwd:<20}{c.NC}")
                        except IndexError: continue

        print("")
        UIBranding.draw_line()
        input(f"  {c.OK} Press {c.BOLD}Enter{c.NC} to return to main menu...")

    def run(self):
        c = self.colors
        if not self.wifi:
            print(f"{c.ERR} Critical: WiFi Engine not injected.")
            return

        while True:
            self._clear_screen()
            
            # --- 1. DYNAMIC HEADER SYSTEM ---
            if self.targets:
                # Banner Mini jika ada target (Hemat ruang)
                print(f"  {c.B}{c.BOLD}WiFi-PRO v{self.version}{c.NC} | {c.G}Targets Loaded: {len(self.targets)}{c.NC}")
                UIBranding.draw_line()
                print(format_target_table(self.colors))
                UIBranding.draw_line()
            else:
                # Banner Full jika belum ada target
                print(UIBranding.get_banner(self.version, self.author))
            
            if self.renderer:
                self.renderer.display_system_status()
            
            # --- 2. MENU GRID LAYOUT ---
            col1 = 35 
            print(f"  {c.B}{c.BOLD}[ CORE ATTACKS ]{c.NC}{' ' * 19}{c.R}{c.BOLD}[ DATA & CRACKING ]{c.NC}")
            
            items = [
                (f"{c.W}[01]{c.NC} Scanner (Airodump-ng)", f"{c.W}[04]{c.NC} NetCut (ARP Spoof)"),
                (f"{c.W}[02]{c.NC} Handshake / WPS",       f"{c.W}[05]{c.NC} Saved Passwords"),
                (f"{c.W}[03]{c.NC} Deauth / DoS",          f"{c.W}[06]{c.NC} Evil Twin Attack")
            ]
            for left, right in items:
                print(f"  {left:<{col1+10}} {right}")
            
            header_text = "[ TOOLS, SYSTEM & MAINTENANCE ]"
            side_w = (config.TABLE_WIDTH - len(header_text) - 4) // 2
            side_line = f"{c.DG}{'─' * side_w}{c.NC}"
            
            print(f"\n  {side_line} {c.P}{c.BOLD}{header_text}{c.NC} {side_line}")
            print(f"  {f'{c.W}[07]{c.NC} MITM Sniffing':<{col1+10}} {c.W}[09]{c.NC} {c.G}System Cleanup{c.NC}")
            print(f"  {f'{c.W}[08]{c.NC} Interface Utils':<{col1+10}} {c.W}[10]{c.NC} {c.Y}Global Settings{c.NC}")
            print(f"  {c.W}[00]{c.NC} {c.R}Exit Framework{c.NC}\n")
            UIBranding.draw_line()

            # --- 3. INPUT HANDLING ---
            try:
                raw_input = input(f"  {c.Q} {c.BOLD}wifipro{c.NC} > ").strip()
                cmd = raw_input.lstrip('0') or '0'

                if cmd == '0':
                    print(f"\n  {c.INFO} {c.Y}Exiting... Restoring network services.{c.NC}")
                    cleaner = SystemMaintenance(c)
                    cleaner.reset_network_environment() 
                    break

                elif cmd == '1':
                    self.wifi.ui_select_interface()
                    iface = getattr(self.wifi, 'iface', "None")
                    config.CURRENT_IFACE = iface
                    if iface != "None":
                        # Scan dan simpan ke state menu & config
                        self.targets = self.wifi.scanner.launch_airodump(c.OK, c.WARN)
                        config.LAST_SCAN_DATA = self.targets

                elif cmd == '2':
                    if self._check_requirement():
                        HandshakeCapture(self.wifi, c).start_capture(self.targets)

                elif cmd == '3':
                    if self._check_requirement():
                        self.wifi.deauth.start_dos(self.targets)

                elif cmd == '4':
                    if self._check_requirement(need_target=False):
                        NetCut(self.wifi, c).start_attack()

                elif cmd == '5':
                    self._display_saved_passwords()

                elif cmd == '6':
                    if self._check_requirement():
                        EvilTwin(self.wifi, c).start(self.targets)

                elif cmd == '7':
                    try:
                        from wifipro.attacks.mitm import PhantomMitmUltimate
                        attack = PhantomMitmUltimate()
                        attack.run()
                    except ImportError:
                        print(f"\n {c.ERR} File mitm.py tidak ditemukan.")
                        time.sleep(2)

                elif cmd == '8':
                    try:
                        from wifipro.utils.adapter import AdapterManager
                        tool = AdapterManager(renderer=self.renderer) 
                        tool.run_menu()
                    except ImportError:
                        print(f"\n {c.ERR} File adapter.py tidak ditemukan!")
                        time.sleep(2)

                elif cmd == '9':
                    cleaner = SystemMaintenance(c) 
                    cleaner.run_menu()
                    # Reset targets setelah cleanup agar banner full muncul kembali
                    self.targets = []
                    config.LAST_SCAN_DATA = []

                elif cmd == '10':
                    try:
                        from wifipro.utils.settings import SettingsManager
                        sm = SettingsManager(wifi_engine=self.wifi, renderer=self.renderer)
                        sm.run_menu()
                    except Exception as e:
                        print(f"\n {c.ERR} Settings Error: {e}")
                        time.sleep(2)

            except KeyboardInterrupt:
                print(f"\n  {c.WARN} Interrupted. Returning to menu...")
                time.sleep(1)
            except Exception as e:
                print(f"\n  {c.ERR} Unexpected Error: {e}")
                time.sleep(2)

if __name__ == "__main__":
    # Ini hanya jika main.py dijalankan langsung (biasanya dipanggil launcher)
    print("Please run the framework via the main launcher.")