import psutil
import socket
import datetime
import subprocess
import win32com.client
import os
import re
import traceback
import checkIP

# ------------------------- Signature Checking -------------------------

def check_signature_sigcheck(exe_path):
    cmd = [r'Sigcheck\sigcheck.exe', '-nobanner', '-q', exe_path]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW  # Ẩn console
        )
        if result.returncode != 0:
            return f"[Sigcheck lỗi] {result.stderr.strip() or 'Không rõ nguyên nhân'}"
        
        output = result.stdout.strip()
        return output if output else "[!] Không có chữ ký"
    except Exception as e:
        return f"[Error] {e}"

def check_signature_wintrust(exe_path):
    try:
        trust = win32com.client.Dispatch("CAPICOM.Signer")
        trust.Load(exe_path)
        return trust.Certificate.IssuerName
    except Exception:
        return "[!] Không có chữ ký hoặc không xác minh được"

# ------------------------- USB / Suspicious Folder Check -------------------------
def is_fromusb_or_suspicious(path):
    suspicious_dirs = ['\\usb', 'removable', 'temp', 'downloads']
    path = path.lower()
    matches = [s for s in suspicious_dirs if s in path]
    if matches:
        return f"Beyond control: {', '.join(matches)}"
    else:
        return "Safe zone"


# ------------------------- DLL Injection Detection -------------------------
SAFE_BASE_DIRS = [
    r'c:\windows\system32',
    r'c:\windows\syswow64',
    r'c:\program files',
    r'c:\program files (x86)',
    r'C:\Windows\WinSxS',
]


def is_signed(filepath):
    try:
        #  '-v', '-vt'
        result = subprocess.run(
            ['Sigcheck/sigcheck.exe', '-i', f'{filepath}'],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW  # Ẩn console
        )
        output = result.stdout.lower()
        verified = False
        company = None

        for line in output.splitlines():
            if line.strip().lower().startswith("verified:") and "signed" in line.lower():
                verified = True
            # elif line.strip().lower().startswith("vt detection:") and re.match(r'vt detection:\s*0/\d+', line.strip().lower()):
            #     vt_clean = True
            elif line.strip().lower().startswith("company:"):
                company = line.split(":", 1)[1].strip()
        if verified:
            return company
        print("output", output)
        return False
    except:
        return "[Error]"


def detect_dll_injection(proc):
    results = []
    try:
        dlls = [
            m.path for m in proc.memory_maps()
            if m.path and m.path.lower().endswith('.dll')
        ]

        for dll in dlls:
            dll_lower = dll.lower()
            # Nếu không nằm trong thư mục hệ thống an toàn
            if not any(dll_lower.startswith(base) for base in SAFE_BASE_DIRS):
                # Kiểm tra chữ ký số
                signed = is_signed(dll)
                if not signed:
                    results.append(f'Nguy hiểm : {dll}')
                    log_dll_injected(dll)
                else:
                    results.append(f'- {signed.capitalize()} : {dll}')
        return results

    except psutil.AccessDenied:
        return "[AccessDenied]"
    except Exception as e:
        return f"[Error] {e}"


# ------------------------- Suspicious IP Detection -------------------------
def is_suspicious_ip(ip):
    if ip.startswith("192.") or ip.startswith("10.") or ip.startswith("172."):
        return False
    return True

def log_suspicious_connection(proc_name, remote_ip, port):
    if "127.0.0.1" in remote_ip:
        return
    if is_suspicious_ip(remote_ip):
        with open("suspicious_log.txt", "a", encoding="utf-8") as f:
            f.write(f"[!] {proc_name} : {remote_ip}:{port}\n")

def log_dll_injected(line):
    if not line: return
    with open("dll_jected.log", "a", encoding="utf-8") as f:
        f.write(line+"\n")

# ------------------------- Full Inspector Class -------------------------
class ProcessInspector:
    def __init__(self, proc: psutil.Process):
        self.proc = proc

    def scan(self):
        try:
            user = "RPYON" if "DESKTOP" in self.proc.username() else self.proc.username()
        except psutil.AccessDenied:
            user = "[AccessDenied]"
        except Exception:
            user = "[Error]"

        try:
            info = {
                'pid': self.proc.pid,
                'exe': self.proc.exe(),
                'name': self.proc.name(),
                'user': user,
                'created': datetime.datetime.fromtimestamp(self.proc.create_time()).strftime("%Y-%m-%d %H:%M:%S"),
            }

            warnings = []  # Danh sách cảnh báo không an toàn


            # ✅ Kiểm tra nguồn gốc USB
            info['from'] = is_fromusb_or_suspicious(info['exe'])
            if info['from'] != "Safe zone":
                warnings.append("Chạy từ Beyond control")

            # ✅ Kiểm tra chữ ký số
            info['signed'] = check_signature_sigcheck(info['exe'])
            if any(s in info['signed'] for s in ("[!]", "Không có", "Error", "Denied")):
                warnings.append("Chữ ký không hợp lệ")

            # ✅ Phát hiện DLL injection
            dll_results = detect_dll_injection(self.proc)
            info['dll_injected'] = dll_results
            if isinstance(dll_results, str):
                # Trường hợp lỗi hoặc AccessDenied
                if dll_results == "[Error]" or dll_results == "[AccessDenied]":
                    warnings.append(dll_results)

            elif isinstance(dll_results, list):
                for rs in dll_results:
                    if "Nguy hiểm" in rs:
                        warnings.append("DLL bị inject")
                        break
            # ✅ Kiểm tra kết nối mạng
            try:
                connections = []
                for conn in self.proc.net_connections(kind='inet'):
                    if conn.raddr:
                        remote_ip = conn.raddr.ip
                        port = conn.raddr.port
                        is_safe = remote_ip.startswith("127.") or remote_ip.startswith("::1")

                        rating = "An toàn" if is_safe else "Cẩn thận"
                        rate = None
                        if not is_safe:
                            rate = checkIP.get_ipinfo(f"{remote_ip}:{port}")
                    
                        conn_line = f"- {'TCP' if conn.type == socket.SOCK_STREAM else 'UDP':<4} | {remote_ip}:{port:<5} -> {rate or rating}"
                        connections.append(conn_line)
                        # log_suspicious_connection(info['name'], remote_ip, port)

                info['connections'] = connections
            except Exception as e:
                info['connections'] = f"[Error] retrieving connections {e}"

            # ✅ Tổng hợp kết quả
            info['Kết quả'] = "\n".join(map(str, warnings)) if warnings else None
            return info

        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
            print(e)
            return None


def analyze_process_by_name(name):
    matched = [p for p in psutil.process_iter(['name']) if name.lower() in p.info['name'].lower()]
    if not matched:
        return None

    all_dll_injected = []
    all_connections = set()
    final_result = None

    for proc in matched:
        inspector = ProcessInspector(proc)
        if isinstance is None:
            print(f'Không đủ quyền truy cập {proc}')
            return None
        else:
            result = inspector.scan()
            if result is None: 
                return None

        # ===== Thu DLL bị inject =====
        dlls = result.get("dll_injected", None)
        if dlls and dlls != "Không xâm nhiễm":
            if isinstance(dlls, list):
                all_dll_injected.extend(dlls)
            else:
                all_dll_injected.append(str(dlls))

        # ===== Thu các IP đang connect =====
        connects = result.get("connections", None)
        if connects:
            for line in connects:
                all_connections.add(line)

        # ===== Nếu process này bị cảnh báo thì dừng sớm
        if result.get("Kết quả", None):
            final_result = result
            break

        # Nếu chưa có kết quả nào, thì lưu tạm bản đầu
        if final_result is None:
            final_result = result

    # ===== In kết quả chính =====
    output = [f"===== {len(matched)} PROCESS MATCHED ====="]
    for k, v in final_result.items():
        if k == "Kết quả" and v is None: continue
        if k == "dll_injected": continue
        if k == "connections": continue
        if isinstance(v, list):
            output.append(f"{k}:")
            output.extend([f"\t{item}" for item in v])
        else:
            output.append(f"{k}\t:\t{v}")

    # ===== Thêm tổng hợp DLL Inject nếu có =====
    if all_dll_injected:
        output.append("\nDll check:")
        for dll in sorted(set(all_dll_injected)):
            output.append(f"\t{dll}")

    # ===== Thêm tổng hợp kết nối IP nếu có =====
    if all_connections:
        output.append("\nConnections:")
        for ip in sorted(set(all_connections)):
            output.append(f"\t{ip}")

    return "\n".join(output)



if __name__ == "__main__":
    a = analyze_process_by_name("edge")
    print(a)

# # ------------------------- Demo Run -------------------------
# if __name__ == "__main__":
#     name = input("Nhập tên tiến trình: ").strip()
#     os.system('cls')
#     matched = [p for p in psutil.process_iter(['name']) if name.lower() in p.info['name'].lower()]

#     best_proc = None
#     max_conn = -1
#     best_result = None

#     for proc in matched:
#         inspector = ProcessInspector(proc)
#         result = inspector.scan()

#         conn_lines = result.get('connections', '')
#         conn_count = conn_lines.count('\n') + 1 if isinstance(conn_lines, str) and conn_lines else 0

#         if conn_count > max_conn:
#             max_conn = conn_count
#             best_proc = proc
#             best_result = result

#     if best_proc and best_result:
#         for k, v in best_result.items():
#             if "\n" in str(v):
#                 v = "\n"+v
#             print(f"{k}\t:\t{v}")
#     else:
#         print("Không tìm thấy tiến trình hoặc không có kết nối nào.")
