import psutil
import socket
import traceback
import subprocess
import re
import wmi
import os
# Các PID hệ thống
SYSTEM_PID = {0, 4}


"""
--------------Các cổng hệ thống mặc định---------------------
Port	Giao thức	Mô tả ngắn	Chi tiết
135	    TCP	        RPC Endpoint Mapper	        Dùng để định vị dịch vụ RPC – Windows dùng trong COM/DCOM.
137	    UDP	        NetBIOS Name Service	    Tra cứu tên NetBIOS trong mạng nội bộ (LAN).
138	    UDP	        NetBIOS Datagram Service	Truyền dữ liệu qua NetBIOS (broadcast).
139	    TCP	        NetBIOS Session Service	    Chia sẻ file qua SMB legacy (trước SMBv2).
445	    TCP	        SMB trực tiếp	            Chia sẻ file và máy in qua TCP (dùng bởi Windows File Sharing).
--------------Các cổng dùng cho dịch vụ Windows-------------
500	    UDP	        IKE	                        Giao thức bảo mật (IPSec VPN negotiation).
3702	UDP	        WS-Discovery	            Tìm kiếm thiết bị (camera, máy in) nội mạng – dùng bởi svchost.exe, dasHost.exe.
1900	UDP	        SSDP	                    Tìm thiết bị UPnP (router, TV...) – Universal Plug & Play.
2869	TCP	        UPnP HTTP	                Giao tiếp HTTP API với UPnP devices.
--------------Multicast & DNS-------------------------------
5353	UDP	        mDNS
5355	UDP	        LLMNR


"""

# Port thường được Windows dùng – an toàn
SAFE_SYSTEM_PORTS = {
    135, 137, 138, 139, 445,                                # RPC, NetBIOS, SMB
    500, 3702, 1900, 2869,                                  # IPSec, WS-Discovery, SSDP, HTTP API cục bộ
    5353, 5355, 49664, 49665, 49666, 49667, 49668, 49669    # Ephemeral fixed port (Windows service)
}

# Tên tiến trình an toàn
SAFE_PROCESS_NAMES = {
    "system", "idle", "svchost.exe", "services.exe", "lsass.exe", "wininit.exe", "csrss.exe",
    "winlogon.exe", "smss.exe", "explorer.exe", "taskhostw.exe"
}

# File thực thi hệ thống an toàn (lowercase, full path)
SAFE_SYSTEM_EXECUTABLES = {
    r"C:\Windows\System32\svchost.exe",
    r"C:\Windows\System32\services.exe",
    r"C:\Windows\System32\lsass.exe",
    r"C:\Windows\System32\wininit.exe",
    r"C:\Windows\System32\csrss.exe",
    r"C:\Windows\System32\winlogon.exe",
    r"C:\Windows\System32\smss.exe",
    r"C:\Windows\explorer.exe",
    r"C:\Windows\System32\taskhostw.exe",
}.union({
    r"C:\Program Files (x86)\Microsoft\Edge\Application" # Path cần loại trừ
})


SAFE_SYSTEM_PORTS = {}
SAFE_PROCESS_NAMES = {}
# SAFE_SYSTEM_EXECUTABLES = {}


def is_ephemeral_port(port: int) -> bool:
    return 49152 <= port <= 65535


def get_process_info(pid: int):
    if pid in (0, 4):
        return {"pid": pid, "name": "System", "exe": "AccessDenied", "user": None}

    try:
        proc = psutil.Process(pid)
    except Exception as e:
        return {"pid": pid, "name": f"Error: {e}", "exe": "Error", "user": None}

    proc_str = str(proc)
    # Ví dụ: "psutil.Process(pid=6312, name='svchost.exe', status='running')"

    name_match = re.search(r"name='([^']+)'", proc_str)
    name = name_match.group(1) if name_match else "<unknown>"

    # Tìm exe (thử chính thức trước)
    try:
        exe = proc.exe()
    except Exception:
        exe = "AccessDenied"

    # Tìm user (thử chính thức trước)
    try:
        user = proc.username()
    except Exception:
        user = None

    return {
        "pid": pid,
        "name": name,
        "exe": exe,
        "user": user
    }


def get_exe_by_wmi(pid: int) -> str:
    try:
        f = wmi.WMI()
        for proc in f.Win32_Process(ProcessId=pid):
            return proc.ExecutablePath or "AccessDeniedWMI"
    except Exception:
        return "AccessDenied"


def classify_port(port: int, pid: int, status: str, proto: str, exe: str, name: str) -> (str, str): # type: ignore
    name = (name or "").strip().lower()
    exe = (exe or "").strip().lower()

    if pid in SYSTEM_PID:
        return "🔰 Safe", "PID hệ thống"
    elif name in SAFE_PROCESS_NAMES:
        return "🔰 Safe", "Tiến trình hệ thống"
    elif exe in {p.lower() for p in SAFE_SYSTEM_EXECUTABLES}:
        return "🔰 Safe", "File hệ thống đã xác minh"
    elif port in SAFE_SYSTEM_PORTS:
        return "🔰 Safe", "Port hệ thống phổ biến"
    elif is_ephemeral_port(port):
        return "🔰 Safe", "Ephemeral port – cấp phát tạm thời"
    elif proto == "UDP":
        return "🚩 Suspicious", "UDP – không có trạng thái TCP"
    elif status == "CLOSE_WAIT":
        return "🚩 Suspicious", "Socket chưa đóng đúng cách"
    elif status == "LISTEN":
        return "🆘 Check", "Port đang lắng nghe – cần xác minh tiến trình"
    else:
        return "🆘 Check", "Không rõ – cần kiểm tra thêm"


def scan_ports():
    conns = psutil.net_connections(kind='inet')
    results = []

    for conn in conns:
        if not conn.laddr:
            continue

        port = conn.laddr.port
        pid = conn.pid or 0
        status = conn.status
        proto = "UDP" if conn.type == socket.SOCK_DGRAM else "TCP"

        proc_info = get_process_info(pid)
        exe_path = proc_info['exe']
        name = proc_info['name']

        port_type, explanation = classify_port(port, pid, status, proto, exe_path, name)
        results.append((port, pid, proto, status, exe_path, port_type, explanation))

    return results


UNSAFESET = []
# UNSAFEPATH = "unsafe.txt"
def getglobal_UnsafeSet():  return UNSAFESET


def fixed_width(value, width, ellipsis=True):
    s = str(value)
    if len(s) > width:
        return s[:width - 3] + '...' if ellipsis else s[:width]
    return s.ljust(width)


def format_port_data():
    data = scan_ports()
    lines = []
    header = f"{'Port':<6} {'PID':<6} {'Proto':<6} {'Trạng thái':<12} {'File thực thi':<70} {'Cờ':<20} Giải thích"
    separator = "-" * 120
    lines.append(header)
    lines.append(separator)

    unsafe_lines = []
    new_lines_to_append = []

    for port, pid, proto, status, exe, kind, explanation in data:
        if kind == '🔰 Safe':
            continue
        line = (
            f"{fixed_width(port, 8)} "
            f"{fixed_width(pid, 8)} "
            f"{fixed_width(proto, 8)} "
            f"{fixed_width(status, 15)} "
            f"{fixed_width(exe, 90)}"
            f"{fixed_width(kind, 20)} "
            f"{explanation}"
        )
        unsafe_lines.append(line)

        if line not in UNSAFESET :
            UNSAFESET.append(line)
            new_lines_to_append.append(line)

    # # Ghi các dòng mới vào file
    # if new_lines_to_append:
    #     with open(UNSAFEPATH, "a", encoding="utf-8") as f:
    #         for line in new_lines_to_append:
    #             f.write(line + "\n")
    if new_lines_to_append: return new_lines_to_append



# === In bảng kết quả ===
if __name__ == "__main__":
    data = scan_ports()
    print(f"{'Port':<6} {'PID':<6} {'Proto':<6} {'Trạng thái':<12} {'File thực thi':<60} {'Cờ':<20} 'Giải thích'")
    print("-" * 120)
    for port, pid, proto, status, exe, kind, explanation in data:
        if kind == '🔰 Safe':
            continue
        print(f"{port:<6} {pid:<6} {proto:<6} {status:<12} {exe:<60} {kind:<20} {explanation}")
