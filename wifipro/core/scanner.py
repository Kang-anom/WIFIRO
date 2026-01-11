#!/usr/bin/env python3
import os
import time
import csv
import subprocess
from wifipro.core import config
from wifipro.utils.terminal import colors

class WiFiScanner:
    def __init__(self, wifi_engine=None):
        self.wifi = wifi_engine
        # Gunakan path absolut dari config
        self.output_file = config.SCAN_RESULT_FILE
        # Airodump otomatis nambahin -01 pada file pertama
        self.csv_path = f"{self.output_file}-01.csv"

    def launch_airodump(self, ok_simbol, warn_simbol):
        """Menjalankan scanner eksternal sesuai standar Kali Linux"""
        try:
            iface = config.CURRENT_IFACE
            if not iface or iface == "None":
                print(f"  {warn_simbol} Error: Pilih interface terlebih dahulu.")
                return []

            # Auto-Switch Monitor Mode
            if self.wifi and not self.wifi.get_mode_status(iface):
                print(f"  {ok_simbol} Mengaktifkan Monitor Mode pada {iface}...")
                self.wifi.toggle_mode(iface)
                time.sleep(2)
                iface = config.CURRENT_IFACE 

            # 3. BERSIHKAN SISA SCAN SEBELUMNYA (Penting!)
            # Kita hapus semua file yang berawalan live_scan di folder scanner
            for f in os.listdir(config.SCAN_DIR):
                if f.startswith("live_scan"):
                    try:
                        os.remove(os.path.join(config.SCAN_DIR, f))
                    except: pass

            # 4. Konfigurasi Command - Pastikan output mengarah ke path absolut
            cmd = f"airodump-ng {iface} --wps --manufacturer --beacons -w {self.output_file} --write-interval 1"
            
            # --- LOGIKA TERMINAL SAMA SEPERTI PUNYA LU ---
            title = f"WIFIPRO_SCANNER [{iface}]"
            geometry = "110x35+950+50"

            print(f"  {ok_simbol} Menjalankan Master Scanner pada {iface}...")
            
            # Deteksi terminal dan eksekusi
            if os.system("which gnome-terminal > /dev/null 2>&1") == 0:
                proc = subprocess.Popen(["gnome-terminal", f"--geometry={geometry}", f"--title={title}", "--", "bash", "-c", cmd])
            elif os.system("which xfce4-terminal > /dev/null 2>&1") == 0:
                proc = subprocess.Popen(["xfce4-terminal", f"--geometry={geometry}", f"--title={title}", "-e", f"bash -c '{cmd}'"])
            else:
                proc = subprocess.Popen(["xterm", "-geometry", geometry, "-T", title, "-e", f"bash -c '{cmd}'"])

            # 6. Menunggu jendela ditutup
            while proc.poll() is None:
                time.sleep(0.5)

        except KeyboardInterrupt:
            print(f"\n  {warn_simbol} Scan dihentikan.")
        except Exception as e:
            print(f"  {warn_simbol} Fatal Error Scanner: {e}")

        return self._harvest_data(ok_simbol, warn_simbol)

    def _harvest_data(self, ok_simbol, warn_simbol):
        """Memproses data dan sinkronisasi ke Global State"""
        # Pastikan proses airodump benar-benar mati
        os.system("pkill -f airodump-ng > /dev/null 2>&1")
        time.sleep(0.5)

        found_targets = []
        if not os.path.exists(self.csv_path):
            print(f"  {warn_simbol} Data scan tidak ditemukan di: {self.csv_path}")
            return []

        try:
            # Membaca CSV dengan aman
            with open(self.csv_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                parts = content.split('\n\n')

                # Parsing AP (Logic lu udah mantap)
                if len(parts) > 0:
                    ap_reader = csv.reader(parts[0].splitlines())
                    for row in ap_reader:
                        if len(row) >= 14 and row[0].strip() not in ["BSSID", ""]:
                            found_targets.append({
                                'bssid':   row[0].strip(),
                                'ch':      row[3].strip().zfill(2),
                                'pwr':     row[8].strip(),
                                'data':    row[10].strip(),
                                'enc':     row[5].strip().split()[0] if row[5].strip() else "OPN",
                                'essid':   row[13].strip() if row[13].strip() else "<Hidden>",
                                'clients': "0",
                                'wps':     "YES" if len(row) > 15 and row[15].strip() else "NO"
                            })

                # Parsing Clients (Sinkronisasi BSSID)
                if len(parts) > 1:
                    client_reader = csv.reader(parts[1].splitlines())
                    for row in client_reader:
                        if len(row) >= 6 and row[0].strip() not in ["Station MAC", ""]:
                            target_bssid = row[5].strip()
                            for t in found_targets:
                                if t['bssid'] == target_bssid:
                                    t['clients'] = str(int(t['clients']) + 1)

            # UPDATE GLOBAL STATE: Ini yang bikin Banner otomatis hilang!
            config.LAST_SCAN_DATA = found_targets
            
            print(f"  {ok_simbol} Berhasil sinkronisasi {len(found_targets)} target.")
            return found_targets

        except Exception as e:
            print(f"  {warn_simbol} Gagal memproses data: {e}")
            return []