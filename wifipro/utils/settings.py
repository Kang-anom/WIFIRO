import os
import time
from wifipro.core import config
from wifipro.utils.terminal import colors as c, UIBranding

class SettingsManager:
    def __init__(self, wifi_engine, renderer=None):
        """
        wifi_engine: Objek self.wifi dari main.py (instansi Process)
        renderer: Objek renderer untuk status bar
        """
        self.wifi = wifi_engine
        self.renderer = renderer

    def run_menu(self):
        while True:
            os.system('clear')
            if self.renderer:
                self.renderer.display_system_status()
            
            print(f"\n  {c.Y}{c.BOLD}[ WIFIPRO GLOBAL CONFIGURATION ]{c.NC}")
            UIBranding.draw_line()
            
            # --- Tampilan Grouping ---
            print(f"  {c.P}[ APP METADATA ]{c.NC}")
            print(f"  {c.W}[01]{c.NC} Version    : {config.VERSION}")
            print(f"  {c.W}[02]{c.NC} Engine     : {config.ENGINE}")
            
            print(f"\n  {c.P}[ UI & DISPLAY ]{c.NC}")
            print(f"  {c.W}[03]{c.NC} Table Width: {config.TABLE_WIDTH}")
            print(f"  {c.W}[04]{c.NC} Line Small : {config.LINE_SMALL}")
            
            print(f"\n  {c.P}[ ATTACK SETTINGS ]{c.NC}")
            print(f"  {c.W}[05]{c.NC} Default Scan Time : {config.DEFAULT_SCAN_TIME}s")
            print(f"  {c.W}[06]{c.NC} MITM Sniff Timer  : {config.TIMER_SNIFFING}s")
            
            # Highlight Interface Aktif
            current = getattr(config, 'CURRENT_IFACE', 'None')
            print(f"  {c.W}[07]{c.NC} Current Interface : {c.C}{current}{c.NC}")
            
            UIBranding.draw_line()
            print(f"  {c.W}[00]{c.NC} Kembali ke Menu Utama")
            
            choice = input(f"\n  {c.Q} Pilih nomor: ").strip()

            if choice == '0' or choice == '': break
            
            # KHUSUS OPSI 7: Gunakan fungsi dari process.py
            if choice == '7':
                print(f"\n  {c.INFO} Membuka menu pemilihan adapter...")
                self.wifi.ui_select_interface() # Fungsi dari process.py
                
                # Sinkronisasi hasil pilihan ke config
                new_iface = getattr(self.wifi, 'iface', 'None')
                config.CURRENT_IFACE = new_iface
                print(f"  {c.OK} {c.G}Config updated: {new_iface}{c.NC}")
                time.sleep(1.5)
                continue

            # Logika Update Dinamis untuk nomor lainnya
            mapping = {
                '1': ('VERSION', str),
                '2': ('ENGINE', str),
                '3': ('TABLE_WIDTH', int),
                '4': ('LINE_SMALL', int),
                '5': ('DEFAULT_SCAN_TIME', int),
                '6': ('TIMER_SNIFFING', int),
            }

            if choice in mapping:
                var_name, var_type = mapping[choice]
                new_val = input(f"  {c.INFO} Masukkan nilai baru {var_name}: ")
                try:
                    config_val = var_type(new_val)
                    setattr(config, var_name, config_val)
                    print(f"  {c.OK} {c.G}Berhasil diubah!{c.NC}")
                except:
                    print(f"  {c.ERR} Gagal! Input harus {var_type.__name__}")
            
            time.sleep(1)