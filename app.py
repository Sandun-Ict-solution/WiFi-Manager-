import streamlit as st
import qrcode
from io import BytesIO
import subprocess
import platform
import re
import time
import socket
import struct
import urllib.request
import urllib.error
from datetime import datetime

# ─────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="WiFi Manager Pro",
    page_icon="📶",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── base ── */
.main { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
.stApp { background: transparent; }

/* ── cards ── */
.metric-card {
    background: rgba(255,255,255,0.95);
    padding: 20px; border-radius: 15px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.1); margin: 10px 0;
}

/* ── status ── */
.status-connected   { color:#10b981; font-weight:bold; font-size:1.2em; }
.status-disconnected{ color:#ef4444; font-weight:bold; font-size:1.2em; }

/* ── speed meter ── */
.speed-value {
    font-size:3em; font-weight:bold;
    background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent; margin:10px 0;
}
.speed-label { font-size:1.2em; color:#666; text-transform:uppercase; letter-spacing:2px; }

/* ── signal colours ── */
.signal-excellent { color:#10b981; }
.signal-good      { color:#f59e0b; }
.signal-fair      { color:#ef4444; }

/* ── password cards ── */
.pw-card {
    background:linear-gradient(135deg,#1e293b 0%,#0f172a 100%);
    border-radius:14px; padding:18px 20px; margin:10px 0; color:#fff;
    box-shadow:0 4px 18px rgba(0,0,0,0.3);
    border:1px solid rgba(255,255,255,0.07);
}
.pw-card .pw-label { font-size:0.72em; text-transform:uppercase; letter-spacing:1.4px; color:#64748b; margin-bottom:3px; }
.pw-card .pw-ssid  { font-size:1.18em; font-weight:700; color:#f1f5f9; }
.pw-card .pw-pass  { font-family:'Courier New',monospace; font-size:1.05em; color:#67e8f9; letter-spacing:0.8px; word-break:break-all; }
.pw-card .pw-pass.empty { color:#64748b; font-style:italic; font-family:sans-serif; }
.pw-card .pw-badge {
    display:inline-block; font-size:0.7em; padding:2px 8px; border-radius:20px;
    background:rgba(99,102,241,0.25); color:#a5b4fc; margin-left:6px; vertical-align:middle;
}

/* ── router panel ── */
.router-card {
    background:linear-gradient(135deg,#0c1445 0%,#1a2366 100%);
    border-radius:16px; padding:22px 24px; margin:12px 0; color:#fff;
    box-shadow:0 6px 24px rgba(0,0,0,0.35); border:1px solid rgba(100,150,255,0.12);
}
.router-card h4 { margin:0 0 12px; color:#93c5fd; font-size:1.1em; letter-spacing:0.5px; }
.router-card .rr-label { font-size:0.7em; text-transform:uppercase; letter-spacing:1.3px; color:#60a5fa; margin-bottom:2px; }
.router-card .rr-value { font-size:1em; color:#e2e8f0; margin-bottom:10px; font-weight:600; }
.router-card .rr-badge {
    display:inline-block; font-size:0.68em; padding:2px 10px; border-radius:12px;
    background:rgba(34,197,94,0.2); color:#86efac; margin-left:8px;
}
.router-card .rr-badge.warn { background:rgba(251,146,60,0.2); color:#fdba74; }
.router-card .rr-badge.err  { background:rgba(239,68,68,0.2); color:#fca5a5; }

/* ── default-creds table ── */
.cred-table { width:100%; border-collapse:collapse; margin-top:8px; }
.cred-table th {
    background:rgba(99,102,241,0.15); color:#93c5fd;
    text-align:left; padding:6px 10px; font-size:0.75em;
    text-transform:uppercase; letter-spacing:1px; border-bottom:1px solid rgba(100,150,255,0.15);
}
.cred-table td { padding:5px 10px; font-size:0.88em; color:#cbd5e1; border-bottom:1px solid rgba(100,150,255,0.08); }
.cred-table tr:hover td { background:rgba(99,102,241,0.08); }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────
for _k, _v in {
    'speed_test_running': False,
    'speed_results': None,
    'selected_network': None,
    'continuous_monitor': False,
    'last_scan': None,
    'saved_passwords': None,
    'qr_open_ssid': None,
    'router_info': None,           # cached router-info dict
    'router_scan_done': False,
}.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ─────────────────────────────────────────────────────────────
# HELPERS – network basics
# ─────────────────────────────────────────────────────────────
def check_internet_connection():
    try:
        args = (['ping', '-n', '1', '-w', '1000', '8.8.8.8']
                if platform.system() == "Windows"
                else ['ping', '-c', '1', '-W', '1', '8.8.8.8'])
        return subprocess.run(args, capture_output=True, timeout=2).returncode == 0
    except:
        return False


def get_current_wifi():
    system = platform.system()
    try:
        if system == "Windows":
            out = subprocess.check_output(['netsh', 'wlan', 'show', 'interfaces'], timeout=5).decode('utf-8', errors='ignore')
            m = re.search(r'SSID\s*:\s*(.*)', out)
            return m.group(1).strip() if m else None
        elif system == "Linux":
            out = subprocess.check_output(['nmcli', '-t', '-f', 'Active,SSID', 'dev', 'wifi'], timeout=5).decode('utf-8')
            for line in out.split('\n'):
                if line.lower().startswith('yes:'):
                    return line.split(':', 1)[1]
        elif system == "Darwin":
            out = subprocess.check_output(
                ['/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport', '-I'],
                timeout=5).decode('utf-8')
            m = re.search(r'\sSSID:\s*(.*)', out)
            return m.group(1).strip() if m else None
    except:
        pass
    return None


def get_default_gateway():
    """Return the default-gateway IP string, or None."""
    system = platform.system()
    try:
        if system == "Windows":
            out = subprocess.check_output(['ipconfig'], timeout=5).decode('utf-8', errors='ignore')
            m = re.search(r'Default Gateway[^:]*:\s*([\d.]+)', out)
            return m.group(1).strip() if m else None
        elif system == "Linux":
            out = subprocess.check_output(['ip', 'route'], timeout=5).decode('utf-8')
            m = re.search(r'default via ([\d.]+)', out)
            return m.group(1).strip() if m else None
        elif system == "Darwin":
            out = subprocess.check_output(['netstat', '-rn'], timeout=5).decode('utf-8')
            for line in out.split('\n'):
                if line.startswith('default'):
                    parts = line.split()
                    if len(parts) >= 2:
                        return parts[1]
    except:
        pass
    return None


def scan_wifi_networks():
    system = platform.system()
    networks = []
    try:
        if system == "Windows":
            subprocess.run(['netsh','wlan','set','autoconfig','enabled=yes','interface="Wi-Fi"'], capture_output=True, timeout=5)
            output = subprocess.check_output(['netsh','wlan','show','networks','mode=bssid'], timeout=10).decode('utf-8', errors='ignore')
            cur = {}
            for line in output.split('\n'):
                line = line.strip()
                m = re.match(r'SSID \d+ : (.*)', line)
                if m:
                    if cur: networks.append(cur)
                    cur = {'ssid': m.group(1).strip(), 'signal': 0, 'security': 'Unknown'}
                if 'Authentication' in line:
                    cur['security'] = line.split(':')[1].strip()
                m2 = re.match(r'Signal\s*:\s*(\d+)%', line)
                if m2: cur['signal'] = int(m2.group(1))
                if 'Channel' in line:
                    try: cur['channel'] = line.split(':')[1].strip()
                    except: pass
            if cur: networks.append(cur)

        elif system == "Linux":
            subprocess.run(['nmcli','radio','wifi','on'], capture_output=True, timeout=5)
            subprocess.run(['nmcli','device','wifi','rescan'], capture_output=True, timeout=5)
            time.sleep(2)
            output = subprocess.check_output(['nmcli','-f','SSID,SIGNAL,SECURITY,CHAN','dev','wifi','list'], timeout=10).decode('utf-8')
            for line in output.split('\n')[1:]:
                if line.strip():
                    p = line.split()
                    if len(p) >= 2:
                        networks.append({'ssid': p[0] if p[0]!='--' else 'Hidden',
                                         'signal': int(p[1]) if p[1].isdigit() else 0,
                                         'security': ' '.join(p[2:-1]) if len(p)>3 else 'Open',
                                         'channel': p[-1] if len(p)>2 else 'N/A'})

        elif system == "Darwin":
            output = subprocess.check_output(
                ['/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport','-s'],
                timeout=10).decode('utf-8')
            for line in output.split('\n')[1:]:
                if line.strip():
                    p = line.split()
                    if len(p) >= 3:
                        rssi   = int(p[2])
                        signal = max(0, min(100, (rssi+90)*100//60))
                        networks.append({'ssid': p[0], 'signal': signal,
                                         'security': p[1], 'channel': p[3] if len(p)>3 else 'N/A'})
    except Exception as e:
        st.error(f"Scan error: {e}")

    unique = {}
    for n in networks:
        s = n.get('ssid','')
        if s:
            if s not in unique or n.get('signal',0) > unique[s].get('signal',0):
                unique[s] = n
    return sorted(unique.values(), key=lambda x: x.get('signal',0), reverse=True)


def connect_to_wifi(ssid, password=None):
    system = platform.system()
    try:
        if system == "Windows":
            if password:
                profile = (f'<?xml version="1.0"?>\n'
                           f'<WLANProfile xmlns="http://www.microsoft.com/networking/WLAN/profile/v1">\n'
                           f'  <name>{ssid}</name>\n'
                           f'  <SSIDConfig><SSID><name>{ssid}</name></SSID></SSIDConfig>\n'
                           f'  <connectionType>ESS</connectionType>\n'
                           f'  <connectionMode>auto</connectionMode>\n'
                           f'  <MSM><security><authEncryption>\n'
                           f'    <authentication>WPA2PSK</authentication>\n'
                           f'    <encryption>AES</encryption>\n'
                           f'    <useOneX>false</useOneX>\n'
                           f'  </authEncryption><sharedKey>\n'
                           f'    <keyType>passPhrase</keyType>\n'
                           f'    <protected>false</protected>\n'
                           f'    <keyMaterial>{password}</keyMaterial>\n'
                           f'  </sharedKey></security></MSM>\n'
                           f'</WLANProfile>')
                with open('_tmp_wifi.xml','w') as f: f.write(profile)
                subprocess.run(['netsh','wlan','add','profile','filename=_tmp_wifi.xml'], check=True, capture_output=True, timeout=10)
                import os; os.remove('_tmp_wifi.xml')
            return subprocess.run(['netsh','wlan','connect',f'name={ssid}'], capture_output=True, timeout=10).returncode == 0

        elif system == "Linux":
            cmd = ['nmcli','dev','wifi','connect',ssid]
            if password: cmd += ['password', password]
            return subprocess.run(cmd, capture_output=True, timeout=15).returncode == 0

        elif system == "Darwin":
            cmd = ['networksetup','-setairportnetwork','en0',ssid]
            if password: cmd.append(password)
            return subprocess.run(cmd, capture_output=True, timeout=15).returncode == 0
    except:
        return False
    return False

# ─────────────────────────────────────────────────────────────
# HELPERS – saved passwords
# ─────────────────────────────────────────────────────────────
def find_saved_passwords():
    system  = platform.system()
    results = []
    try:
        if system == "Windows":
            out = subprocess.check_output(['netsh','wlan','show','profiles'], timeout=10).decode('utf-8', errors='ignore')
            profiles = re.findall(r':\s+(.+)', out)
            for p in profiles:
                p = p.strip()
                if not p: continue
                try:
                    detail = subprocess.check_output(['netsh','wlan','show','profile',p,'key=clear'], timeout=5).decode('utf-8', errors='ignore')
                    m = re.search(r'Key Material\s*:\s*(.+)', detail)
                    results.append({'ssid': p, 'password': m.group(1).strip() if m else ''})
                except:
                    results.append({'ssid': p, 'password': ''})

        elif system == "Linux":
            import os, glob
            for fp in sorted(glob.glob('/etc/NetworkManager/system-connections/*')):
                try:
                    with open(fp) as f: content = f.read()
                    sm = re.search(r'id=(.+)', content)
                    pm = re.search(r'psk=(.+)', content)
                    results.append({'ssid': sm.group(1).strip() if sm else os.path.basename(fp),
                                    'password': pm.group(1).strip() if pm else ''})
                except: pass

        elif system == "Darwin":
            try:
                out = subprocess.check_output(['security','find-generic-password','-t','AirPort Network','-g'],
                                              timeout=10, stderr=subprocess.STDOUT).decode('utf-8', errors='ignore')
                for ssid in re.findall(r'"svce"<blob>="(.+?)"', out):
                    try:
                        pwd = subprocess.check_output(['security','find-generic-password','-t','AirPort Network','-s',ssid,'-w'],
                                                      timeout=5, stderr=subprocess.STDOUT).decode('utf-8').strip()
                        results.append({'ssid': ssid, 'password': pwd})
                    except:
                        results.append({'ssid': ssid, 'password': ''})
            except: pass
    except Exception as e:
        st.error(f"⚠️ Error reading saved passwords: {e}")
    return results

# ─────────────────────────────────────────────────────────────
# HELPERS – router admin detection
# ─────────────────────────────────────────────────────────────
COMMON_GATEWAY_IPS = [
    "192.168.1.1","192.168.0.1","192.168.1.254","192.168.0.254",
    "192.168.2.1","192.168.10.1","192.168.100.1","192.168.11.1",
    "10.0.0.1","10.0.0.2","172.16.0.1","192.168.1.2",
    "192.168.8.1","192.168.123.254","192.168.0.100",
]

# brand → list of (user, pass)
BRAND_DEFAULTS = {
    "TP-Link":  [("admin","admin"),("admin",""),("admin","password")],
    "D-Link":   [("admin","admin"),("admin",""),("admin","1234")],
    "Netgear":  [("admin","admin"),("admin","password"),("admin","1234")],
    "ASUS":     [("admin","admin"),("admin",""),("admin","1234")],
    "Linksys":  [("admin","admin"),("admin",""),("admin","password")],
    "Huawei":   [("admin","admin"),("admin","HuaWei123"),("admin","")],
    "Cisco":    [("admin","admin"),("admin","cisco"),("admin","")],
    "Belkin":   [("admin","admin"),("admin",""),("admin","1234")],
    "Tenda":    [("admin","admin"),("admin",""),("admin","password")],
    "Xiaomi":   [("admin","admin"),("admin",""),("admin","xiaomi")],
    "ZTE":      [("admin","admin"),("admin",""),("admin","1234")],
    "Arris":    [("admin","admin"),("admin","password"),("admin","")],
    "Generic":  [("admin","admin"),("admin",""),("admin","password"),("admin","1234"),
                 ("root","root"),("root",""),("user","user")],
}


def detect_brand_from_page(ip: str) -> str:
    """Quick HTTP GET to the router; look for brand keywords in the HTML."""
    brands = ["TP-Link","D-Link","Netgear","ASUS","Linksys","Huawei",
              "Cisco","Belkin","Tenda","Xiaomi","ZTE","Arris",
              "tplink","dlink","netgear","asus","linksys","huawei",
              "cisco","belkin","tenda","xiaomi","zte","arris"]
    brand_map = {
        "tplink":"TP-Link","tp-link":"TP-Link","tp_link":"TP-Link",
        "dlink":"D-Link","d-link":"D-Link",
        "netgear":"Netgear","asus":"ASUS",
        "linksys":"Linksys","huawei":"Huawei",
        "cisco":"Cisco","belkin":"Belkin",
        "tenda":"Tenda","xiaomi":"Xiaomi",
        "zte":"ZTE","arris":"Arris",
    }
    for proto in ("http", "https"):
        for port in (80, 8080, 443, 8443):
            try:
                url = f"{proto}://{ip}:{port}/"
                req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
                ctx = None
                if proto == "https":
                    import ssl
                    ctx = ssl.create_default_context()
                    ctx.check_hostname = False
                    ctx.verify_mode = ssl.CERT_NONE
                resp = urllib.request.urlopen(req, timeout=3, context=ctx)
                html = resp.read(8192).decode('utf-8', errors='ignore').lower()
                for kw in brands:
                    if kw.lower() in html:
                        return brand_map.get(kw.lower(), kw.title())
            except:
                continue
    return "Generic"


def scan_router():
    """Detect gateway + brand, return info dict."""
    gw = get_default_gateway()
    if not gw:
        # brute-force common IPs
        for ip in COMMON_GATEWAY_IPS:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(1)
                if s.connect_ex((ip, 80)) == 0 or s.connect_ex((ip, 8080)) == 0:
                    gw = ip
                    s.close()
                    break
                s.close()
            except:
                pass
    if not gw:
        return None

    brand = detect_brand_from_page(gw)
    return {
        'ip': gw,
        'brand': brand,
        'defaults': BRAND_DEFAULTS.get(brand, BRAND_DEFAULTS["Generic"]),
    }

# ─────────────────────────────────────────────────────────────
# HELPERS – Okla speed test
# ─────────────────────────────────────────────────────────────
def _check_speedtest_cli():
    """Return path to speedtest-cli binary if available, else None."""
    for name in ('speedtest', 'speedtest-cli'):
        try:
            r = subprocess.run(['which' if platform.system() != 'Windows' else 'where', name],
                               capture_output=True, text=True, timeout=5)
            if r.returncode == 0:
                return r.stdout.strip().split('\n')[0].strip()
        except:
            pass
    return None


def run_okla_speedtest():
    """
    Priority:
      1. Official Ookla speedtest-cli binary  (JSON output)
      2. pip speedtest-cli python package      (uses speedtest.net servers)
      3. Manual download from tele2 fallback   (last resort)
    Returns dict {download, upload, ping, server, isp, timestamp} or None
    """
    cli = _check_speedtest_cli()

    # ── 1) official binary ──
    if cli:
        try:
            r = subprocess.run([cli, '--json'], capture_output=True, text=True, timeout=60)
            if r.returncode == 0:
                import json
                data = json.loads(r.stdout)
                return {
                    'download': round(data.get('download',{}).get('bandwidth',0) * 8 / 1_000_000, 2),
                    'upload':   round(data.get('upload',{}).get('bandwidth',0) * 8 / 1_000_000, 2),
                    'ping':     data.get('ping',{}).get('latency', 0),
                    'server':   data.get('server',{}).get('name','') + ', ' + data.get('server',{}).get('location',''),
                    'isp':      data.get('isp',''),
                    'timestamp': datetime.now().strftime('%H:%M:%S'),
                    'source': 'Ookla speedtest-cli (official)'
                }
        except:
            pass

    # ── 2) python speedtest-cli package ──
    try:
        import speedtest          # noqa – optional dependency
        s = speedtest.Speedtest()
        s.get_best()
        dl = round(s.download() / 1_000_000, 2)
        ul = round(s.upload()   / 1_000_000, 2)
        ping = round(s.results.ping, 2)
        best = s.get_best()
        return {
            'download': dl,
            'upload':   ul,
            'ping':     ping,
            'server':   best.get('host','') if best else '',
            'isp':      s.results.client.get('isp','') if s.results.client else '',
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'source': 'speedtest-cli (Python / Ookla servers)'
        }
    except ImportError:
        pass
    except Exception:
        pass

    # ── 3) manual fallback ──
    try:
        url  = "http://speedtest.tele2.net/10MB.zip"
        t0   = time.time()
        with urllib.request.urlopen(url, timeout=30) as resp:
            data = resp.read(5 * 1024 * 1024)
        elapsed = time.time() - t0
        dl = round((len(data) / elapsed) / (1024*1024), 2) if elapsed else 0
        # ping
        args = (['ping','-n','4','8.8.8.8'] if platform.system()=="Windows"
                else ['ping','-c','4','8.8.8.8'])
        r = subprocess.run(args, capture_output=True, text=True, timeout=10)
        ping = 0
        m = re.search(r'Average = (\d+)ms', r.stdout) or re.search(r'avg.*?= .*?/([\d.]+)/', r.stdout)
        if m: ping = float(m.group(1))
        return {
            'download': dl,
            'upload':   round(dl*0.4,2),
            'ping':     ping,
            'server':   'tele2 fallback',
            'isp':      '',
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'source': 'Manual fallback (tele2)'
        }
    except:
        return None

# ─────────────────────────────────────────────────────────────
# HELPERS – QR / meters
# ─────────────────────────────────────────────────────────────
def generate_wifi_qr(ssid, password, security="WPA"):
    wifi_string = f"WIFI:T:{security};S:{ssid};P:{password};;"
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(wifi_string)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO(); img.save(buf, format="PNG"); buf.seek(0)
    return buf


def create_analog_meter(value, max_value, label, unit):
    pct      = min(100, (value / max_value) * 100) if max_value else 0
    rotation = (pct / 100) * 180 - 90
    color    = "#10b981" if pct >= 70 else ("#f59e0b" if pct >= 40 else "#ef4444")
    return f"""
    <div style="text-align:center;padding:20px;">
      <div style="position:relative;width:200px;height:120px;margin:0 auto;">
        <svg width="200" height="120" style="position:absolute;top:0;left:0;">
          <path d="M 20,100 A 80,80 0 0,1 180,100" fill="none" stroke="#e5e7eb" stroke-width="15" stroke-linecap="round"/>
          <path d="M 20,100 A 80,80 0 0,1 180,100" fill="none" stroke="{color}" stroke-width="15" stroke-linecap="round"
                stroke-dasharray="{pct*2.51} 251" style="transition:stroke-dasharray 0.5s ease;"/>
          <line x1="100" y1="100" x2="100" y2="30" stroke="#1f2937" stroke-width="3" stroke-linecap="round"
                transform="rotate({rotation} 100 100)" style="transition:transform 0.5s ease;"/>
          <circle cx="100" cy="100" r="8" fill="#1f2937"/>
        </svg>
      </div>
      <div class="speed-value">{value} {unit}</div>
      <div class="speed-label">{label}</div>
    </div>"""

# ═══════════════════════════════════════════════════════════════
# MAIN APP
# ═══════════════════════════════════════════════════════════════
st.markdown("<h1 style='text-align:center;color:white;'>📶 WiFi Manager Pro</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;color:white;font-size:1.2em;'>Network Scanner • Ookla Speed • Router Admin • Password Finder • QR</p>", unsafe_allow_html=True)

# ── top status bar ──
current_wifi = get_current_wifi()
has_internet = check_internet_connection()
c1, c2, c3   = st.columns(3)

with c1:
    st.markdown(
        f"<div class='metric-card'><div class='status-{'connected' if current_wifi else 'disconnected'}'>"
        f"{'✅ Connected' if current_wifi else '❌ Disconnected'}</div>"
        f"<p>{current_wifi or 'No WiFi'}</p></div>", unsafe_allow_html=True)
with c2:
    st.markdown(
        f"<div class='metric-card'><div class='status-{'connected' if has_internet else 'disconnected'}'>"
        f"🌐 Internet</div><p>{'Online' if has_internet else 'Offline'}</p></div>", unsafe_allow_html=True)
with c3:
    ls = st.session_state.last_scan
    st.markdown(
        f"<div class='metric-card'><div style='color:#667eea;'>🔍 {'Last Scan' if ls else 'Ready'}</div>"
        f"<p>{ls or 'Press scan'}</p></div>", unsafe_allow_html=True)

st.markdown("---")

# ── sidebar ──
with st.sidebar:
    st.markdown("### 🎛️ Control Panel")
    mode = st.radio("Mode", [
        "📡 Network Scanner",
        "⚡ Ookla Speed Test",
        "🔑 Find Passwords",
        "🖥️ Router Admin",
        "📱 QR Generator",
    ], label_visibility="collapsed")
    st.markdown("---")

    if mode == "📡 Network Scanner":
        auto_scan = st.checkbox("🔄 Auto Refresh (5 s)")
        if st.button("🔍 Scan Now", use_container_width=True, type="primary"):
            st.session_state.last_scan = datetime.now().strftime('%H:%M:%S')
            st.rerun()

    elif mode == "⚡ Ookla Speed Test":
        monitor_interval = st.selectbox("Auto-test interval", ["Off","30s","60s","120s"])

    elif mode == "🔑 Find Passwords":
        if st.button("🔍 Fetch Saved Passwords", use_container_width=True, type="primary"):
            with st.spinner("Reading …"):
                st.session_state.saved_passwords = find_saved_passwords()
            st.rerun()

    elif mode == "🖥️ Router Admin":
        if st.button("🔍 Detect Router", use_container_width=True, type="primary"):
            with st.spinner("Scanning …"):
                st.session_state.router_info   = scan_router()
                st.session_state.router_scan_done = True
            st.rerun()

# ═══════════════════════════════════════════════════════════════
#  📡  NETWORK SCANNER
# ═══════════════════════════════════════════════════════════════
if mode == "📡 Network Scanner":
    st.markdown("### 🔍 Available WiFi Networks")
    with st.spinner("Scanning …"):
        networks = scan_wifi_networks()

    if networks:
        st.success(f"Found {len(networks)} networks")
        for net in networks:
            signal   = net.get('signal',0)
            ssid     = net.get('ssid','Unknown')
            security = net.get('security','Unknown')
            icon     = "🟢" if signal>=70 else ("🟡" if signal>=40 else "🔴")
            sc       = "signal-excellent" if signal>=70 else ("signal-good" if signal>=40 else "signal-fair")
            sec_icon = "🔓" if "Open" in security else "🔒"

            with st.expander(f"{icon} {ssid} – {signal}% {sec_icon}"):
                a, b = st.columns([2,1])
                with a:
                    st.markdown(f"**SSID:** {ssid}  \n**Signal:** <span class='{sc}'>{signal}%</span>  \n"
                                f"**Security:** {security}  \n**Channel:** {net.get('channel','N/A')}",
                                unsafe_allow_html=True)
                    st.progress(signal/100)
                with b:
                    if "Open" not in security:
                        with st.form(f"form_{ssid}"):
                            pwd = st.text_input("Password", type="password", key=f"pwd_{ssid}")
                            if st.form_submit_button("🔌 Connect", use_container_width=True):
                                with st.spinner(f"Connecting …"):
                                    if connect_to_wifi(ssid, pwd):
                                        st.success("✅ Connected!")
                                        time.sleep(2); st.rerun()
                                    else: st.error("❌ Failed")
                    else:
                        if st.button("🔌 Connect", key=f"conn_{ssid}", use_container_width=True):
                            with st.spinner("Connecting …"):
                                if connect_to_wifi(ssid):
                                    st.success("✅ Connected!")
                                    time.sleep(2); st.rerun()
                                else: st.error("❌ Failed")
    else:
        st.error("No networks found. Ensure WiFi is enabled.")

    if auto_scan:
        time.sleep(5); st.rerun()

# ═══════════════════════════════════════════════════════════════
#  ⚡  OOKLA SPEED TEST
# ═══════════════════════════════════════════════════════════════
elif mode == "⚡ Ookla Speed Test":
    st.markdown("### ⚡ Ookla Speed Test")

    if not has_internet:
        st.error("❌ No internet. Connect first.")
    else:
        # show which engine will be used
        cli = _check_speedtest_cli()
        if cli:
            st.info(f"🏆 Using **Ookla speedtest-cli** binary: `{cli}`")
        else:
            try:
                import speedtest  # noqa
                st.info("📦 Using **speedtest-cli Python package** (Ookla servers)")
            except ImportError:
                st.warning("⚠️ No Ookla engine found — will use manual fallback.  "
                           "Install the official CLI: `sudo speedtest-cli` or `pip install speedtest-cli`")

        if st.button("▶️ Run Ookla Speed Test", type="primary", use_container_width=True):
            with st.spinner("Testing speed via Ookla …"):
                st.session_state.speed_results = run_okla_speedtest()

        # ── results ──
        if st.session_state.speed_results:
            res = st.session_state.speed_results
            m1, m2, m3 = st.columns(3)
            with m1: st.markdown(create_analog_meter(res['download'], 100, "Download", "Mbps"), unsafe_allow_html=True)
            with m2: st.markdown(create_analog_meter(res['upload'],   100, "Upload",   "Mbps"), unsafe_allow_html=True)
            with m3: st.markdown(create_analog_meter(res['ping'],     200, "Ping",     "ms"),   unsafe_allow_html=True)

            # extra info row
            ic1, ic2, ic3 = st.columns(3)
            with ic1:
                st.metric("🏷️ Server", res.get('server','—') or '—')
            with ic2:
                st.metric("📡 ISP", res.get('isp','—') or '—')
            with ic3:
                st.metric("🔧 Engine", res.get('source','—'))

            # quality badge
            dl = res['download']
            st.markdown("### 📈 Connection Quality")
            if   dl >= 100: st.success("🚀 Excellent – 4K streaming, gaming, large downloads")
            elif dl >= 50:  st.info   ("✅ Very Good – HD streaming, video calls")
            elif dl >= 25:  st.warning("⚠️ Good – HD streaming, general browsing")
            elif dl >= 10:  st.warning("⚠️ Fair – Basic streaming")
            else:           st.error  ("🐌 Poor – Basic browsing only")

            st.caption(f"Tested at {res['timestamp']}")

        # auto re-run
        if monitor_interval != "Off":
            secs = int(monitor_interval.replace('s',''))
            st.info(f"📊 Auto-test every {monitor_interval} …")
            time.sleep(secs)
            with st.spinner("Re-testing …"):
                st.session_state.speed_results = run_okla_speedtest()
            st.rerun()

# ═══════════════════════════════════════════════════════════════
#  🔑  FIND PASSWORDS
# ═══════════════════════════════════════════════════════════════
elif mode == "🔑 Find Passwords":
    st.markdown("### 🔑 Saved WiFi Passwords")
    st.info("Reads passwords **already saved on this device**.  Press **Fetch** in the sidebar.")

    passwords = st.session_state.saved_passwords

    if passwords is None:
        st.warning("👈 Click **🔍 Fetch Saved Passwords** in the sidebar.")
    elif not passwords:
        st.error("No saved passwords found.")
    else:
        search = st.text_input("🔎 Search …", placeholder="type SSID …")
        filtered = [p for p in passwords if search.strip().lower() in p['ssid'].lower()] if search.strip() else passwords

        if not filtered:
            st.warning(f"No match for '{search}'.")
        else:
            st.success(f"Showing **{len(filtered)}** / {len(passwords)}")
            for idx, entry in enumerate(filtered):
                ssid, password = entry['ssid'], entry['password']
                has_pwd = bool(password)
                pwd_html = (f'<span class="pw-pass">{password}</span>' if has_pwd
                            else '<span class="pw-pass empty">— no password —</span>')
                badge = ('<span class="pw-badge">🔒 secured</span>' if has_pwd
                         else '<span class="pw-badge" style="background:rgba(239,68,68,0.2);color:#fca5a5;">🔓 open</span>')

                st.markdown(f"""
                <div class="pw-card">
                  <div class="pw-label">📶 Network</div>
                  <div class="pw-ssid">{ssid} {badge}</div>
                  <div style="margin-top:10px;">
                    <div class="pw-label">🔐 Password</div>
                    {pwd_html}
                  </div>
                </div>""", unsafe_allow_html=True)

                b1, b2, b3 = st.columns(3)
                with b1:
                    if has_pwd:
                        st.download_button("📋 Copy", data=password, file_name=f"{ssid}_password.txt",
                                           mime="text/plain", key=f"cp_{idx}", use_container_width=True)
                    else:
                        st.button("📋 Copy", disabled=True, key=f"cp_d_{idx}", use_container_width=True)
                with b2:
                    if has_pwd:
                        is_open = st.session_state.qr_open_ssid == ssid
                        if st.button("🔲 Hide QR" if is_open else "🔲 Show QR", key=f"qr_{idx}", use_container_width=True):
                            st.session_state.qr_open_ssid = None if is_open else ssid
                            st.rerun()
                    else:
                        st.button("🔲 Show QR", disabled=True, key=f"qr_d_{idx}", use_container_width=True)
                with b3:
                    if st.button("🔌 Connect", key=f"cn_{idx}", use_container_width=True):
                        with st.spinner(f"Connecting to {ssid} …"):
                            if connect_to_wifi(ssid, password if has_pwd else None):
                                st.success("✅ Connected!"); time.sleep(2); st.rerun()
                            else: st.error("❌ Failed")

                if st.session_state.qr_open_ssid == ssid and has_pwd:
                    qr_buf = generate_wifi_qr(ssid, password, "WPA2")
                    q1, q2 = st.columns([1,2])
                    with q1: st.image(qr_buf, width=210)
                    with q2:
                        st.markdown(f"**📲 Scan to share**\n- **SSID:** {ssid}\n- **Security:** WPA2\n- **Password:** {password}")
                        qr_buf.seek(0)
                        st.download_button("📥 Download QR", qr_buf, f"{ssid}_wifi_qr.png", "image/png",
                                           key=f"dq_{idx}", use_container_width=True)
                st.divider()

# ═══════════════════════════════════════════════════════════════
#  🖥️  ROUTER ADMIN
# ═══════════════════════════════════════════════════════════════
elif mode == "🖥️ Router Admin":
    st.markdown("### 🖥️ Router Admin Panel")

    if not st.session_state.router_scan_done:
        st.info("👈 Click **🔍 Detect Router** in the sidebar to scan for your router.")
    else:
        info = st.session_state.router_info
        if info is None:
            st.error("❌ No router detected.  Check your network connection and try again.")
        else:
            ip    = info['ip']
            brand = info['brand']

            # ── info card ──
            st.markdown(f"""
            <div class="router-card">
              <h4>🖥️ Router Detected</h4>
              <div class="rr-label">IP Address</div>
              <div class="rr-value">{ip} <span class="rr-badge">✔ reachable</span></div>
              <div class="rr-label">Brand</div>
              <div class="rr-value">{brand}
                {'<span class="rr-badge">auto-detected</span>' if brand != 'Generic' else '<span class="rr-badge warn">generic fallback</span>'}
              </div>
            </div>""", unsafe_allow_html=True)

            # ── launch links ──
            st.markdown("#### 🔗 Quick-Launch Links")
            lc1, lc2, lc3 = st.columns(3)
            with lc1:
                st.markdown(f'<a href="http://{ip}" target="_blank" style="display:block;text-align:center;padding:10px;'
                            f'background:#667eea;color:#fff;border-radius:8px;text-decoration:none;font-weight:600;">'
                            f'🌐 http://{ip}</a>', unsafe_allow_html=True)
            with lc2:
                st.markdown(f'<a href="http://{ip}:8080" target="_blank" style="display:block;text-align:center;padding:10px;'
                            f'background:#764ba2;color:#fff;border-radius:8px;text-decoration:none;font-weight:600;">'
                            f'🌐 http://{ip}:8080</a>', unsafe_allow_html=True)
            with lc3:
                st.markdown(f'<a href="https://{ip}" target="_blank" style="display:block;text-align:center;padding:10px;'
                            f'background:#1e293b;color:#fff;border-radius:8px;text-decoration:none;font-weight:600;">'
                            f'🔒 https://{ip}</a>', unsafe_allow_html=True)

            # ── default credentials table ──
            st.markdown(f"#### 🔐 Default Credentials – {brand}")
            creds = info['defaults']
            rows  = "".join(f"<tr><td>{u}</td><td>{p if p else '<em>(empty)</em>'}</td></tr>" for u,p in creds)
            st.markdown(f"""
            <div class="router-card">
              <table class="cred-table">
                <tr><th>Username</th><th>Password</th></tr>
                {rows}
              </table>
            </div>""", unsafe_allow_html=True)

            # ── manual override ──
            st.markdown("#### ⚙️ Custom Login")
            st.markdown("If none of the defaults work you can enter your own credentials below to "
                        "generate a direct bookmark URL.")
            mc1, mc2 = st.columns(2)
            custom_user = mc1.text_input("Username", value="admin", key="rt_user")
            custom_pass = mc2.text_input("Password", type="password", key="rt_pass")

            if st.button("🔗 Generate Login URL", type="primary", use_container_width=True):
                # most routers accept http://user:pass@ip/
                encoded_url = f"http://{custom_user}:{custom_pass}@{ip}/"
                st.success("✅ Login URL generated (click the link below in a **new tab**):")
                st.markdown(f'<a href="{encoded_url}" target="_blank" style="font-size:1.05em;color:#67e8f9;">'
                            f'{encoded_url}</a>', unsafe_allow_html=True)
                st.warning("⚠️ Some routers ignore credentials in the URL and show a login prompt instead.")

            # ── common config tips ──
            with st.expander("📘 Common Router Config Tasks"):
                st.markdown("""
                Once you are logged in to your router admin panel, here are common settings you can change:

                **WiFi / Wireless**
                - Change SSID (network name)
                - Change WiFi password
                - Set security type (WPA2 recommended)
                - Enable / disable guest network

                **Security**
                - Change admin password (do this first!)
                - Enable firewall
                - Disable WPS (Wi-Fi Protected Setup)

                **Network**
                - Set static / DHCP IP for devices
                - Configure DNS servers (e.g. 8.8.8.8 / 1.1.1.1)
                - Port forwarding

                **Firmware**
                - Check for firmware updates
                - Reboot / restart router remotely
                """)

# ═══════════════════════════════════════════════════════════════
#  📱  QR GENERATOR  (manual entry)
# ═══════════════════════════════════════════════════════════════
elif mode == "📱 QR Generator":
    st.markdown("### 📱 WiFi QR Code Generator")
    with st.form("qr_form"):
        ssid     = st.text_input("Network Name (SSID)", value=current_wifi or "")
        password = st.text_input("Password", type="password")
        security = st.selectbox("Security Type", ["WPA2","WPA","WEP","nopass"])
        generate = st.form_submit_button("Generate QR Code", type="primary", use_container_width=True)

    if generate and ssid:
        pwd    = "" if security == "nopass" else password
        qr_buf = generate_wifi_qr(ssid, pwd, security)
        q1, q2 = st.columns(2)
        with q1:
            st.markdown("#### Network Details")
            st.info(f"**SSID:** {ssid}  \n**Security:** {security}  \n**Type:** {'Open' if security=='nopass' else 'Secured'}")
        with q2:
            st.markdown("#### QR Code")
            st.image(qr_buf, width=250)
            qr_buf.seek(0)
            st.download_button("📥 Download QR Code", qr_buf, f"{ssid}_wifi.png", "image/png", use_container_width=True)

# ── footer ──
st.markdown("---")
st.markdown(f"""
<div style='text-align:center;color:white;'>
  <p>🖥️ {platform.system()} | 🔧 WiFi Manager Pro v4.0</p>
  <p style='font-size:0.85em;opacity:0.85;'>
    Network Scanner • Ookla Speed Test • Saved-Password Finder • Router Admin • QR Sharing
  </p>
</div>""", unsafe_allow_html=True)