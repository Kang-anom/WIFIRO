# 📡 WIFIRO v1.0 - Automated Wireless Auditing Framework

![License](https://img.shields.io/badge/license-Open%20Source-blue.svg)
![Python](https://img.shields.io/badge/language-Python-blue.svg)
![Version](https://img.shields.io/badge/version-1.0-brightgreen.svg)

**WIFIRO** is an advanced wireless security auditing framework designed to automate network scanning, handshake capturing, and security testing with high efficiency and precision.

---

## 📸 Interface & Results

Below is the visual documentation of the WIFIRO interface and auditing process:

### 1. Main Menu Interface
The main interface for selecting wireless targets and audit modes.
<p align="center">
  <img src="1.png" width="700" alt="Main Menu">
</p>

### 2. Network Scanning & Targeting
Automated scanning process identifying nearby access points and their security status.
<p align="center">
  <img src="2.png" width="700" alt="Scanning Process">
</p>

### 3. Audit Execution & Results
Real-time monitoring of the audit process and successful capture reports.
<p align="center">
  <img src="3.png" width="700" alt="Audit Report">
</p>

---

## 📝 Developer's Note
I am aware that this tool is still under active development and requires further improvements. I have made this project **Open Source** to encourage community collaboration and enhancement. Wireless security is a rapidly changing field, and staying ahead requires constant updates.

If you are interested in collaborating, offering suggestions, or reporting bugs, please reach out to me via Gmail. Your support and donations are greatly appreciated to keep this project moving forward.

***Best regards, KANG ANOM***

---

## 🚀 Main Features

* **Auto-Scanner**: Intelligent identification of vulnerable wireless networks.
* **Handshake Capture**: Automated deauthentication and WPA/WPA2 handshake sniffing.
* **Optimized Workflow**: Simplified command-line interface inspired by professional auditing tools.
* **Live Logging**: Real-time output of all activities for detailed analysis.

---

## 🛠️ Installation

Ensure your wireless adapter supports **Monitor Mode** and **Packet Injection** before starting:

```bash
# Clone repository
git clone [https://github.com/Kang-anom/WIFIRO.git](https://github.com/Kang-anom/WIFIRO.git)

# Enter directory
cd WIFIRO

# Install dependencies (Example for Debian-based systems)
sudo apt update && sudo apt install aircrack-ng airmon-ng python3 -y

# Run framework
sudo python3 wifiro.py
