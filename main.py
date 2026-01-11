#!/usr/bin/env python3
import os
import sys
import time
import signal
import traceback
import subprocess

# Pastikan folder saat ini masuk ke path agar module wifipro terbaca
sys.path.insert(0, os.path.abspath(os.getcwd()))

# Import modul internal
try:
    # PERBAIKAN: Menu sekarang diimpor dari core.menu
    from wifipro.core.menu import Menu
    from wifipro.utils.terminal import colors
    from wifipro.utils.process import WirelessManager
except Exception as e:
    print(f"\033[91m[!] Error Loading Modules: {e}\033[0m")
    sys.exit(1)


def check_dependencies():
    """Cek apakah tools wifi terinstal di sistem"""
    tools = ["airmon-ng", "airodump-ng", "macchanger"]
    missing = []
    for t in tools:
        if subprocess.run(["which", t], capture_output=True).returncode != 0:
            missing.append(t)

    if missing:
        print(f"\n\033[91m[!] Dependencies Missing: {', '.join(missing)}")
        print(f"\033[93m[*] Please install them using: sudo apt install aircrack-ng macchanger\033[0m")
        sys.exit(1)


def check_root():
    """Memastikan hak akses root"""
    if os.geteuid() != 0:
        print("\033[93m[*] Memerlukan hak akses root. Mencoba eskalasi...\033[0m")
        try:
            os.execvp("sudo", ["sudo", sys.executable] + sys.argv)
        except Exception:
            print("\033[91m[!] Gagal mendapatkan hak akses root!\033[0m")
            sys.exit(1)


def graceful_exit(signum, frame):
    """Cleanup saat user menekan CTRL+C"""
    print(f"\n\n\033[93m[!] Shutdown. Membersihkan background proses...\033[0m")
    # Bersihkan proses zombie
    os.system("pkill -f airodump-ng > /dev/null 2>&1")
    os.system("pkill -f aireplay-ng > /dev/null 2>&1")
    time.sleep(0.5)
    print("\033[92m[*] Bye! Sampai jumpa lagi.\033[0m")
    sys.exit(0)


def main():
    # Tangkap sinyal CTRL+C
    signal.signal(signal.SIGINT, graceful_exit)

    # 1. Validasi Lingkungan
    check_root()
    check_dependencies()

    # 2. Inisialisasi Program
    try:
        # Buat instance Menu
        app = Menu()
        
        # Buat instance Wireless Engine
        wifi_engine = WirelessManager(colors)

        # Injeksi Engine ke Menu
        app.set_wifi_engine(wifi_engine)
        app.processor = wifi_engine

        # 3. Jalankan Program Utama
        os.system("clear")
        app.run()

    except Exception as e:
        print(f"\n\033[91m[!] Fatal Error: {e}\033[0m")
        # Log error ke file untuk debugging
        with open("error_log.txt", "a") as f:
            f.write(f"\n--- {time.ctime()} ---\n{traceback.format_exc()}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()