import os

# ==========================================================
# KONFIGURASI PATH ABSOLUT (Kunci Agar Tidak Nyampah)
# ==========================================================
# os.path.abspath(__file__) -> wifipro/core/config.py
# .dirname naik 1 level -> wifipro/core/
# .dirname naik 2 level -> wifipro/
# .dirname naik 3 level -> ROOT (Tempat main.py berada)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Folder Utama di ROOT
DATA_DIR = os.path.join(BASE_DIR, "data")

# ==========================================================
# METADATA APLIKASI
# ==========================================================
VERSION     = "3.1"
AUTHOR      = "kang-anom"
ENGINE      = "python"
DESCRIPTION = "Network Security Educational Framework"

# ==========================================================
# GLOBAL STATE (DATA DINAMIS)
# ==========================================================
CURRENT_IFACE = "wlan0"
LAST_SCAN_DATA = []

# ==========================================================
# SUB-FOLDER HASIL SERANGAN (KATEGORISASI)
# ==========================================================
SCAN_DIR      = os.path.join(DATA_DIR, "scanner")
HANDSHAKE_DIR = os.path.join(DATA_DIR, "handshakes")
NETCUT_DIR    = os.path.join(DATA_DIR, "netcut")
EVILTWIN_DIR  = os.path.join(DATA_DIR, "eviltwin")
MITM_DIR      = os.path.join(DATA_DIR, "mitm")
LOG_DIR       = os.path.join(DATA_DIR, "logs")
MITM_LOG_PATH = os.path.join(MITM_DIR, "logs")

# ==========================================================
# FILE OUTPUT SPESIFIK (Gunakan Full Path)
# ==========================================================
# Scanner Result (Airodump akan menambah ekstensi sendiri)
SCAN_RESULT_FILE = os.path.join(SCAN_DIR, "live_scan")

# Handshake Database & Results
HANDSHAKE_DB = os.path.join(HANDSHAKE_DIR, "handshakes.json")
RESULT_FILE  = os.path.join(EVILTWIN_DIR, "passwords.txt")

# ==========================================================
# UI & SETTINGS
# ==========================================================
TIMER_SNIFFING = 30
TABLE_WIDTH    = 78
LINE_SMALL     = 50
DEFAULT_SCAN_TIME = 30 

# ==========================================================
# INISIALISASI OTOMATIS
# ==========================================================
REQUIRED_FOLDERS = [
    DATA_DIR, SCAN_DIR, HANDSHAKE_DIR, NETCUT_DIR, 
    EVILTWIN_DIR, MITM_DIR, MITM_LOG_PATH, LOG_DIR
]

def ensure_paths():
    """Memastikan semua folder ada sebelum tools dijalankan"""
    for folder in REQUIRED_FOLDERS:
        if not os.path.exists(folder):
            try:
                os.makedirs(folder, exist_ok=True)
            except Exception as e:
                print(f"[!] Gagal membuat folder {folder}: {e}")

# Panggil fungsi saat module di-load
ensure_paths()