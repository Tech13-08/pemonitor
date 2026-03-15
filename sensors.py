import os, time, csv, requests, subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, "pc_stats.csv")
CPU_TEMP_ALARM = 82.0 
GPU_TEMP_ALARM = 82.0 
CPU_POWER_ALARM = 150.0
GPU_POWER_ALARM = 350.0
last_log_time = 0

def get_windows_ip():
    try: return subprocess.check_output("ip route show | grep default | awk '{print $3}'", shell=True).decode().strip()
    except: return "127.0.0.1"

def parse_sensors():
    s = {'cpu_w': 0, 'cpu_t': 0, 'gpu_w': 0, 'gpu_t': 0, 'vram_u': 0, 'ram_u': 0, 'disk': 0, 
         'f1': 0, 'f2': 0, 'f3': 0, 'f4': 0, 'f5': 0}
    try:
        url = f"http://{get_windows_ip()}:8085/data.json"
        data = requests.get(url, timeout=1).json()
        
        def walk(node):
            t, sid, v_str = node.get('Text', ''), node.get('SensorId', ''), node.get('Value', '0')
            raw = v_str.split(' ')[0].replace(',', '.')
            try: val = float(raw)
            except: val = 0

            if "/amdcpu/0/power/0" in sid: s['cpu_w'] = val
            if t == "Core (Tctl/Tdie)": s['cpu_t'] = val
            if "/gpu-amd/5/power/3" in sid: s['gpu_w'] = val
            if "/gpu-amd/5/temperature/0" in sid: s['gpu_t'] = val
            if "/gpu-amd/5/smalldata/0" in sid: s['vram_u'] = round(val/1024, 2)
            if "/lpc/it8689e/0/fan/0" in sid: s['f1'] = val
            if "/lpc/it8689e/0/fan/1" in sid: s['f2'] = val
            if "/lpc/it8689e/0/fan/2" in sid: s['f3'] = val
            if "/lpc/it8689e/0/fan/3" in sid: s['f4'] = val
            if "/lpc/it8689e/0/fan/4" in sid: s['f5'] = val
            if "/ram/data/0" in sid: s['ram_u'] = val
            if "/nvme/0/load/30" in sid: s['disk'] = val

            for child in node.get('Children', []): walk(child)
        walk(data)
    except: pass
    return s

def log_alarm(data):
    global last_log_time
    file_exists = os.path.isfile(LOG_FILE)
    fan_summary = f"F1:{data['f1']} F2:{data['f2']} F3:{data['f3']} F4:{data['f4']} F5:{data['f5']}"
    with open(LOG_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['Date', 'Time', 'CPU_W', 'GPU_W', 'CPU_T', 'GPU_T', 'RAM', 'VRAM', 'Disk', 'Fans'])
        writer.writerow([time.strftime("%Y-%m-%d"), time.strftime("%H:%M:%S"), 
                         data['cpu_w'], data['gpu_w'], data['cpu_t'], data['gpu_t'], 
                         data['ram_u'], data['vram_u'], data['disk'], fan_summary])
    last_log_time = time.time()

def check_for_alarms(s):
    global last_log_time
    now = time.time()
    is_spike = (s['cpu_t'] > CPU_TEMP_ALARM or s['gpu_t'] > GPU_TEMP_ALARM or 
                s['cpu_w'] > CPU_POWER_ALARM or s['gpu_w'] > GPU_POWER_ALARM)
    
    if is_spike and (now - last_log_time > 1.0):
        log_alarm(s)