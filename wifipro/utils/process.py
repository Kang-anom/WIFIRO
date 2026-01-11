#!/usr/bin/env python3
import os
import time
import subprocess
import shutil
from wifipro.core import config # Kunci sinkronisasi

class WirelessManager:
    def __init__(self, colors):
        self.colors = colors
        self.iface = config.CURRENT_IFACE # Ambil dari config
        self.scanner = None # Inisialisasi nanti agar tidak circular import

    def cleanup_system(self):
        """
        Membersihkan semua sampah scan dan serangan dari folder data/
        """
        c = self.colors
        print(f" {c.INFO} Membersihkan semua residu serangan...")
        
        # Daftar folder yang akan dibersihkan isinya
        target_dirs = [config.SCAN_DIR, config.LOG_DIR, config.MITM_LOG_PATH]
        
        count = 0
        for folder in target_dirs:
            if os.path.exists(folder):
                for filename in os.listdir(folder):
                    file_path = os.path.join(folder, filename)
                    try:
                        if os.path.isfile(file_path) or os.path.islink(file_path):
                            os.unlink(file_path)
                            count += 1
                        elif os.path.isdir(file_path):
                            shutil.rmtree(file_path)
                            count += 1
                    except Exception as e:
                        print(f" {c.ERR} Gagal hapus {filename}: {e}")
        
        # Reset IP Forwarding ke default (OFF)
        self.set_ip_forward(False)
        
        print(f" {c.OK} {c.G}Berhasil membersihkan {count} file sementara.{c.NC}")

    def get_interface(self):
        """ Mendapatkan interface wireless aktif saat ini """
        try:
            cmd = "iw dev | awk '/Interface/ {print $2}'"
            res = subprocess.check_output(cmd, shell=True).decode().strip().split('\n')
            return res[0] if res and res[0] != "" else "None"
        except:
            return "None"

    def set_ip_forward(self, status):
        """ Mengatur IP Forwarding (0=Off, 1=On) """
        val = "1" if status else "0"
        os.system(f"echo {val} > /proc/sys/net/ipv4/ip_forward")

    def get_mac(self, iface):
        """ Mendapatkan MAC Address interface """
        if iface == "None" or not iface: return "00:00:00:00:00:00"
        try:
            with open(f"/sys/class/net/{iface}/address", "r") as f:
                return f.read().strip().upper()
        except:
            return "00:00:00:00:00:00"

    def get_mode_status(self, iface):
        """ Cek apakah mode Monitor (True) atau Managed (False) """
        if iface == "None" or not iface: return False
        check = subprocess.run(f"iw dev {iface} info", shell=True, capture_output=True, text=True)
        return "type monitor" in check.stdout

    def set_monitor_mode(self, iface):
        """ Mengaktifkan mode monitor (Pro Standard) """
        c = self.colors
        print(f" {c.INFO} Mencoba mengaktifkan Monitor Mode pada {c.C}{iface}{c.NC}...")
        
        # Standar Kali: Matikan pengganggu
        os.system("sudo airmon-ng check kill > /dev/null 2>&1")
        os.system("sudo rfkill unblock wifi")
        
        # Jalankan urutan switch
        os.system(f"sudo ip link set {iface} down")
        os.system(f"sudo iw dev {iface} set type monitor")
        os.system(f"sudo ip link set {iface} up")
        
        time.sleep(1)
        if self.get_mode_status(iface):
            print(f" {c.OK} {c.G}Monitor Mode: ON{c.NC}")
            return True
        return False

    def set_managed_mode(self, iface):
        """ Mengembalikan network ke kondisi normal """
        c = self.colors
        # Wlan0mon -> wlan0
        clean_iface = iface.replace("mon", "")
        
        print(f" {c.INFO} Merestorasi network {c.C}{clean_iface}{c.NC}...")
        
        commands = [
            f"sudo airmon-ng stop {iface}",
            f"sudo iw dev {clean_iface} set type managed",
            f"sudo ip link set {clean_iface} up",
            f"sudo rfkill unblock wifi",
            f"sudo systemctl restart NetworkManager"
        ]

        for cmd in commands:
            os.system(f"{cmd} > /dev/null 2>&1")
            time.sleep(0.2) 

        config.CURRENT_IFACE = clean_iface
        print(f" {c.OK} {c.G}NetworkManager aktif kembali.{c.NC}")
        return True

    def get_all_interfaces(self):
        """ List semua interface wireless yang tersedia """
        res = subprocess.run("iw dev | grep Interface | awk '{print $2}'", shell=True, capture_output=True, text=True)
        return res.stdout.strip().split('\n')