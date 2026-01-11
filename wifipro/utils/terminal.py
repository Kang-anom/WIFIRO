#!/usr/bin/env python3
import socket
import os
from colorama import Fore, Back, Style, init
# Import seluruh modul config untuk sinkronisasi Global State
from wifipro.core import config

# Inisialisasi Colorama
init(autoreset=True)

class Color:
    """Standardized Security Palette for Kali Linux Style Tools"""
    def __init__(self):
        # Base Colors
        self.R  = Fore.RED + Style.BRIGHT    
        self.G  = Fore.GREEN + Style.BRIGHT  
        self.Y  = Fore.YELLOW + Style.BRIGHT 
        self.B  = Fore.BLUE + Style.BRIGHT   
        self.P  = Fore.MAGENTA + Style.BRIGHT
        self.C  = Fore.CYAN + Style.BRIGHT   
        self.W  = Fore.WHITE + Style.BRIGHT  
        self.DG = Fore.BLACK + Style.BRIGHT  
        
        # SPECIAL EFFECTS
        self.BOLD = Style.BRIGHT
        self.NC   = Style.RESET_ALL           # No Color / Reset
        self.LR   = "\033[5m" + Fore.RED + Style.BRIGHT # LAVA RED (BLINKING)
        
        # Standardized Status Icons
        self.OK   = f"{self.G}[+]{self.NC}"
        self.ERR  = f"{self.R}[-]{self.NC}"
        self.WARN = f"{self.Y}[!]{self.NC}"
        self.INFO = f"{self.B}[*]{self.NC}"
        self.Q    = f"{self.C}[?]{self.NC}"
        
        # Blink Status Icon for Critical Missing Dependencies
        self.FAIL = f"{self.LR}[✘]{self.NC}"

# Global instance
colors = Color()

class UIBranding:
    """Logic untuk Banner dan Dekorasi Visual"""
    
    @staticmethod
    def get_banner(version=None, author=None):
        """Hanya tampilkan banner jika belum ada hasil scan (LAST_SCAN_DATA kosong)"""
        # SINKRONISASI: Cek apakah tabel data sudah terisi
        if config.LAST_SCAN_DATA:
            # Jika ada data scan, jangan kembalikan banner (agar hemat ruang terminal)
            return ""

        c = colors
        v = version or config.VERSION
        a = author or config.AUTHOR
        
        # Gunakan 'rf' supaya backslash tidak dianggap error oleh Python
        icon = [
            rf"{c.B}          _                     ",
            rf"{c.B}    _   / \         _   _      ",
            rf"{c.W}---{c.B}/{c.W}-{c.B}\{c.W}-{c.B}/{c.W}---{c.B}\{c.W}---{c.B}_{c.W}---{c.B}/{c.W}-{c.B}\{c.W}-{c.B}/{c.W}-{c.B}\{c.W}---",
            rf"{c.B}  V   V      \ / \ /   V   V       ",
            rf"{c.B}              v   v             "
        ]
        info = [
            f"{c.B}{c.BOLD}WiFi-PRO FRAMEWORK{c.NC}",
            f"{c.DG}──────────────────────────{c.NC}",
            f"{c.W}Version  : {c.G}{v}{c.NC}",
            f"{c.W}Engine   : {c.C}{config.ENGINE}{c.NC}",
            f"{c.W}Author   : {c.P}{a}{c.NC}",
        ]

        output = "\n"
        for i in range(len(icon)):
            info_part = info[i] if i < len(info) else ""
            output += f"            {icon[i]}          {info_part}\n"
        
        output += f"{' ' * 24}{c.Y}{config.DESCRIPTION}{c.NC}\n"

        return output

    @staticmethod
    def draw_line():
        c = colors
        # Sinkronisasi dengan TABLE_WIDTH di config
        print(f" {c.DG}{'─' * config.TABLE_WIDTH}{c.NC}")

class InterfaceRenderer:
    def __init__(self, wifi_engine, version=None):
        self.wifi = wifi_engine
        self.version = version or config.VERSION
        self.colors = colors

    def display_system_status(self):
        c = self.colors
        # SINKRONISASI: Mengambil interface terbaru dari config
        iface = config.CURRENT_IFACE
        
        # Cek Monitor Mode status
        is_mon = self.wifi.get_mode_status(iface) if self.wifi and iface != "None" else False
        
        # Warna Monitor Mode
        if is_mon:
            mon_status = f"{c.G}ON{c.NC}"
        else:
            mon_status = f"{c.R}\033[5mOFF{c.NC}"

        # Ambil MAC secara aman
        try:
            mac_addr = self.wifi.get_mac(iface) if self.wifi and iface != "None" else "00:00:00:00:00:00"
        except:
            mac_addr = "00:00:00:00:00:00"

        # Tampilan status bar satu baris
        status_line = (
            f" {c.INFO} {c.W}Mode Monitor: {mon_status} {c.DG}│ "
            f"{c.W}Iface: {c.C}{iface}{c.NC} {c.DG}│ "
            f"{c.W}MAC: {c.Y}{mac_addr}{c.NC} {c.DG}│ "
            f"{c.W}Ver: {c.G}{self.version}{c.NC}"
        )
        
        print(status_line)
        UIBranding.draw_line()