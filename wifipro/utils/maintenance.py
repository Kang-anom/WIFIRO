import os
import subprocess
import time

# SINKRONISASI: Pastikan import REQUIRED_FOLDERS dari config
try:
    from wifipro.core.config import REQUIRED_FOLDERS
    from wifipro.core import config
except ImportError:
    REQUIRED_FOLDERS = []

class SystemMaintenance:
    def __init__(self, colors):
        """
        Menggunakan palet warna dari terminal.py (objek colors)
        """
        self.c = colors

    def reset_network_environment(self):
        """ 
        [TOTAL RESET] Mengembalikan PC ke kondisi normal (Internet Aktif, Port Bersih)
        Fungsi ini mengambil interface otomatis dari Global State (config.py)
        """
        c = self.c
        # SINKRONISASI: Ambil interface aktif terbaru
        iface = getattr(config, 'CURRENT_IFACE', "None")

        print(f"\n  {c.INFO} {c.Y}MEMULAI RESTORASI TOTAL SISTEM...{c.NC}")

        # 1. KILL PROCESSES (Reset Proses Background)
        # Menghapus paksa tools yang mengunci port network
        tools = ["bettercap", "airdump-ng", "aireplay-ng", "hostapd", "dnsmasq", "hashcat", "mitmproxy"]
        for tool in tools:
            subprocess.run(f"sudo pkill -9 {tool}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        
        # 2. RESET NETWORK STACK (Reset IP Forward & Iptables)
        # Sangat krusial agar koneksi internet kembali lancar
        os.system("sudo sysctl -w net.ipv4.ip_forward=0 > /dev/null")
        os.system("sudo iptables -F")
        os.system("sudo iptables -t nat -F")
        os.system("sudo iptables -t mangle -F")
        os.system("sudo iptables -X")

        # 3. RESTORE INTERFACE (Managed Mode)
        if iface and iface != "None":
            clean_iface = iface.replace("mon", "")
            print(f"  {c.INFO} Mengembalikan {c.C}{iface}{c.NC} -> {c.G}{clean_iface}{c.NC} (Managed)")
            
            commands = [
                f"sudo airmon-ng stop {iface} > /dev/null 2>&1",
                f"sudo ip link set {clean_iface} down",
                f"sudo iw dev {clean_iface} set type managed",
                f"sudo ip link set {clean_iface} up",
                f"sudo rfkill unblock wifi"
            ]
            for cmd in commands:
                os.system(cmd)
                time.sleep(0.2)
            
            # Update state global kembali ke interface normal
            config.CURRENT_IFACE = clean_iface

        # 4. RESTART SERVICE (Final Restoration)
        print(f"  {c.OK} {c.G}Memulihkan Network Manager & Internet...{c.NC}")
        os.system("sudo systemctl restart NetworkManager > /dev/null 2>&1")
        
        print(f"  {c.OK} {c.G}SISTEM KEMBALI NORMAL!{c.NC}")

    def clear_all_data(self):
        """ 
        MEMBERSIHKAN FILE DATA (.cap, .txt, .hc22000)
        """
        c = self.c
        print(f"\n  {c.WARN} {c.R}PERINGATAN: Semua hasil capture & password akan dihapus!{c.NC}")
        confirm = input(f"  {c.Q} Konfirmasi penghapusan? (y/N): ").lower()
        
        if confirm == 'y':
            print(f"  {c.INFO} Membersihkan direktori data...{c.NC}")
            try:
                for folder in REQUIRED_FOLDERS:
                    if os.path.exists(folder):
                        for file in os.listdir(folder):
                            file_path = os.path.join(folder, file)
                            if os.path.isfile(file_path):
                                os.remove(file_path)
                print(f"  {c.OK} {c.G}Semua file capture dan log telah dibersihkan.{c.NC}")
            except Exception as e:
                print(f"  {c.ERR} Gagal membersihkan data: {e}")
        else:
            print(f"  {c.INFO} Pembersihan dibatalkan.")

    def run_menu(self):
        """ Interface Menu [09] Maintenance """
        c = self.c
        os.system('clear')
        # Gunakan Branding Line dari config jika ada
        print(f"\n  {c.P}{c.BOLD}[ SYSTEM MAINTENANCE & RECOVERY ]{c.NC}")
        print(f"  {c.DG}──────────────────────────────────────────{c.NC}")
        print(f"  {c.W}[01]{c.NC} Reset Network (Fix Internet/Mode Normal)")
        print(f"  {c.W}[02]{c.NC} Wipe All Saved Data (Clean Logs/Caps)")
        print(f"  {c.W}[03]{c.NC} Full Cleanup (Environment + Data)")
        print(f"  {c.W}[00]{c.NC} Back to Main Menu")
        
        try:
            choice = input(f"\n  {c.Q} Pilih: ").strip()
            if choice == "1":
                self.reset_network_environment()
            elif choice == "2":
                self.clear_all_data()
            elif choice == "3":
                self.reset_network_environment()
                self.clear_all_data()
            elif choice == "0":
                return
        except KeyboardInterrupt:
            return
        
        input(f"\n  {c.OK} Tekan {c.BOLD}Enter{c.NC} untuk kembali...")