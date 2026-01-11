import os
import time
from wifipro.core import config     
from wifipro.utils.terminal import colors as c, UIBranding 

class AdapterManager:
    def __init__(self, renderer=None):
        """
        renderer: Diambil dari InterfaceRenderer di main.py
        """
        self.c = c
        self.renderer = renderer 

    def get_current_iface(self):
        return getattr(config, 'CURRENT_IFACE', "None")

    def set_tx_power(self):
        iface = self.get_current_iface()
        if iface == "None":
            print(f"  {c.ERR} Interface tidak ditemukan di config!")
            return

        print(f"\n  {c.INFO} Mengatur TX Power {c.C}{iface}{c.NC} ke 30dBm (1 Watt)...")
        cmds = [
            f"sudo iw reg set BO",
            f"sudo ip link set {iface} down",
            f"sudo iw dev {iface} set txpower fixed 3000",
            f"sudo ip link set {iface} up"
        ]
        for cmd in cmds:
            os.system(cmd)
            time.sleep(0.2)
        print(f"  {c.OK} {c.G}Success: TX Power ditingkatkan ke level maksimal!{c.NC}")

    def soft_restart(self):
        iface = self.get_current_iface()
        if iface == "None":
            print(f"  {c.ERR} Tidak ada interface untuk di-restart!")
            return

        print(f"  {c.INFO} Restarting {c.C}{iface}{c.NC}...")
        os.system(f"sudo ip link set {iface} down")
        time.sleep(0.5)
        os.system(f"sudo ip link set {iface} up")
        print(f"  {c.OK} Interface {iface} kembali online.")

    def run_menu(self):
        # Ambil lebar tabel dari config untuk konsistensi garis
        width = getattr(config, 'TABLE_WIDTH', 50)
        line = f"  {c.DG}{'─' * width}{c.NC}"

        while True:
            os.system('clear')
            
            # 1. Tampilkan Banner (Force display)
            old_scan_data = config.LAST_SCAN_DATA
            config.LAST_SCAN_DATA = [] 
            print(UIBranding.get_banner())
            config.LAST_SCAN_DATA = old_scan_data

            # 2. Tampilkan Status Bar (Monitor Mode, Iface, MAC, Ver)
            # Bagian ini akan memanggil InterfaceRenderer.display_system_status()
            if self.renderer:
                self.renderer.display_system_status()
            else:
                # Fallback jika renderer tidak terkirim
                print(f"  {c.WARN} System Status Renderer not found.")
                print(line)
            
            iface = self.get_current_iface()
            
            # 3. Menu Body
            print(f"\n  {c.P}{c.BOLD}[ ADAPTER SETTINGS & OPTIMIZATION ]{c.NC}")
            print(f"  {c.DG}Active Interface : {c.C}{iface}{c.NC}")
            print(line)
            
            if iface == "None":
                print(f"  {c.ERR} {c.R}WARNING: Interface belum dipilih!{c.NC}")
                print(f"  {c.INFO} Silahkan pilih interface di menu [01].")
                print(line)
            
            print(f"  {c.W}[01]{c.NC} Boost TX Power (30dBm/1W)")
            print(f"  {c.W}[02]{c.NC} Set Region to BO (Unlock Channels)")
            print(f"  {c.W}[03]{c.NC} Soft Restart Device (rfkill fix)")
            print(f"  {c.W}[00]{c.NC} Kembali ke Menu Utama")
            
            try:
                choice = input(f"\n  {c.Q} Pilih opsi: ").strip()
                
                if choice == '1':
                    self.set_tx_power()
                    input(f"\n  {c.OK} Tekan {c.BOLD}Enter{c.NC}...")
                elif choice == '2':
                    print(f"  {c.INFO} Mengatur regulasi wilayah ke Bolivia...")
                    os.system("sudo iw reg set BO")
                    print(f"  {c.OK} {c.G}Region set to BO (Success).{c.NC}")
                    time.sleep(1.5)
                elif choice == '3':
                    os.system("sudo rfkill unblock wifi")
                    self.soft_restart()
                    time.sleep(1.5)
                elif choice == '0' or choice == '':
                    break
            except KeyboardInterrupt:
                break