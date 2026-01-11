#!/usr/bin/env python3
from wifipro.core import config

def format_target_table(colors, line_width=None):
    """
    Me-render tabel WiFi dari config.LAST_SCAN_DATA.
    Menggunakan indikator warna standar audit keamanan.
    """
    # Ambil data terbaru dari global state config
    targets = config.LAST_SCAN_DATA
    width = line_width or config.TABLE_WIDTH
    
    if not targets:
        return f"  {colors.WARN} {colors.R}No scan data available. Run scanner [01] first.{colors.NC}"

    output = []

    # 1. Header Tabel (Warna Kuning Bold standar Kali)
    # Format lebar kolom disesuaikan agar simetris
    header_fmt = f"  {colors.Y}{colors.BOLD}%-3s %-17s %-2s %-4s %-4s %-4s %-5s %-7s %-4s %-20s{colors.NC}"
    output.append(
        header_fmt % (
            "ID", "BSSID", "CH", "PWR", "DATA", "CLNT", "ENC", "AUTH", "WPS", "ESSID"
        )
    )
    output.append(f"  {colors.DG}{'─' * width}{colors.NC}")

    # 2. Baris Data (Membatasi tampilan agar tidak merusak UI jika AP terlalu banyak)
    for idx, t in enumerate(targets[:12]):  # Batasi 12 AP teratas untuk estetika menu
        try:
            # Power (Indikator Sinyal)
            pwr = int(t.get("pwr", 0))
            if pwr >= -60:
                p_col = colors.G  # Sinyal Bagus
            elif pwr >= -75:
                p_col = colors.Y  # Sinyal Sedang
            else:
                p_col = colors.R  # Sinyal Lemah

            # WPS Indicator
            wps_status = t.get("wps", "NO")
            wps_col = colors.G if wps_status == "YES" else colors.NC

            # Encryption Color (Hijau untuk Open, Merah untuk WPA)
            enc = t.get("enc", "OPN")
            enc_col = colors.R if "WPA" in enc else colors.G

            # Build Row String
            row_fmt = (
                f"  {colors.C}%-3s{colors.NC} "       # ID
                f"{colors.W}%-17s{colors.NC} "      # BSSID
                f"{colors.G}%-2s{colors.NC} "       # CH
                f"{p_col}%-4s{colors.NC} "          # PWR
                f"%-4s "                            # DATA
                f"{colors.B}%-4s{colors.NC} "       # CLNT
                f"{enc_col}%-5s{colors.NC} "        # ENC
                f"%-7s "                            # AUTH
                f"{wps_col}%-4s{colors.NC} "        # WPS
                f"{colors.W}%-20s{colors.NC}"       # ESSID
            )

            row = row_fmt % (
                str(idx + 1),
                t.get("bssid", "-"),
                t.get("ch", "-"),
                str(pwr),
                t.get("data", "0"),
                t.get("clients", "0"),
                enc[:5],
                t.get("auth", "-")[:7],
                wps_status,
                t.get("essid", "<Hidden>")[:20]
            )
            output.append(row)
        except Exception:
            continue

    return "\n".join(output)