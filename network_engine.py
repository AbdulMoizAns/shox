"""
network_engine.py
SHOX — Native Windows Network & Internet Activity Engine.
Zero-dependency Win32 IP Helper API (iphlpapi.dll) integration.
Monitors active TCP/UDP connections, remote IPs, ports, process owners, and live network bandwidth.
"""

import ctypes
from ctypes import wintypes
import socket
import struct
import time
from typing import Dict, List, Tuple

iphlpapi = ctypes.windll.iphlpapi
kernel32 = ctypes.windll.kernel32

# Constants
AF_INET = 2
TCP_TABLE_OWNER_PID_ALL = 5
UDP_TABLE_OWNER_PID = 1

# TCP States mapping
TCP_STATES = {
    1: "CLOSED",
    2: "LISTENING",
    3: "SYN_SENT",
    4: "SYN_RCVD",
    5: "ESTABLISHED",
    6: "FIN_WAIT1",
    7: "FIN_WAIT2",
    8: "CLOSE_WAIT",
    9: "CLOSING",
    10: "LAST_ACK",
    11: "TIME_WAIT",
    12: "DELETE_TCB",
}

# Common port service directory for immediate human context
COMMON_SERVICES = {
    20: "FTP-Data",
    21: "FTP-Control",
    22: "SSH",
    23: "Telnet",
    25: "SMTP",
    53: "DNS",
    80: "HTTP (Web)",
    110: "POP3",
    123: "NTP (Time)",
    135: "RPC",
    137: "NetBIOS",
    139: "NetBIOS",
    143: "IMAP",
    443: "HTTPS (Secure Web)",
    445: "SMB (File Share)",
    993: "IMAPS",
    995: "POP3S",
    1433: "MS-SQL",
    1521: "Oracle",
    3306: "MySQL",
    3389: "RDP (Remote Desktop)",
    5000: "UPnP",
    5040: "Windows Devices",
    5353: "mDNS",
    5432: "PostgreSQL",
    5900: "VNC",
    7680: "Windows Update P2P",
    8000: "HTTP-Dev",
    8080: "HTTP-Proxy",
    8443: "HTTPS-Alt",
    9000: "Dev-Service",
    27017: "MongoDB",
}

# Structs for Bandwidth Monitoring (GetIfTable2)
class MIB_IF_ROW2(ctypes.Structure):
    _fields_ = [
        ("InterfaceLuid", ctypes.c_uint64),
        ("InterfaceIndex", ctypes.c_uint32),
        ("InterfaceGuid", ctypes.c_byte * 16),
        ("Alias", ctypes.c_wchar * 257),
        ("Description", ctypes.c_wchar * 257),
        ("PhysicalAddressLength", ctypes.c_uint32),
        ("PhysicalAddress", ctypes.c_byte * 32),
        ("PermanentPhysicalAddress", ctypes.c_byte * 32),
        ("Mtu", ctypes.c_uint32),
        ("Type", ctypes.c_uint32),
        ("TunnelType", ctypes.c_uint32),
        ("MediaType", ctypes.c_uint32),
        ("PhysicalMediumType", ctypes.c_uint32),
        ("AccessType", ctypes.c_uint32),
        ("DirectionType", ctypes.c_uint32),
        ("InterfaceAndOperStatusFlags", ctypes.c_byte),
        ("OperStatus", ctypes.c_uint32),
        ("AdminStatus", ctypes.c_uint32),
        ("MediaConnectState", ctypes.c_uint32),
        ("NetworkGuid", ctypes.c_byte * 16),
        ("ConnectionType", ctypes.c_uint32),
        ("padding1", ctypes.c_byte * 4),
        ("TransmitLinkSpeed", ctypes.c_uint64),
        ("ReceiveLinkSpeed", ctypes.c_uint64),
        ("InOctets", ctypes.c_uint64),
        ("InUcastPkts", ctypes.c_uint64),
        ("InNUcastPkts", ctypes.c_uint64),
        ("InDiscards", ctypes.c_uint64),
        ("InErrors", ctypes.c_uint64),
        ("InUnknownProtos", ctypes.c_uint64),
        ("InUcastOctets", ctypes.c_uint64),
        ("InMulticastOctets", ctypes.c_uint64),
        ("InBroadcastOctets", ctypes.c_uint64),
        ("OutOctets", ctypes.c_uint64),
        ("OutUcastPkts", ctypes.c_uint64),
        ("OutNUcastPkts", ctypes.c_uint64),
        ("OutDiscards", ctypes.c_uint64),
        ("OutErrors", ctypes.c_uint64),
        ("OutUcastOctets", ctypes.c_uint64),
        ("OutMulticastOctets", ctypes.c_uint64),
        ("OutBroadcastOctets", ctypes.c_uint64),
        ("OutQLen", ctypes.c_uint64),
    ]


class MIB_IF_TABLE2(ctypes.Structure):
    _fields_ = [
        ("NumEntries", ctypes.c_ulong),
        ("padding", ctypes.c_ulong),
        ("Table", MIB_IF_ROW2 * 1)
    ]


class NetworkMonitorEngine:
    """
    Native Win32 Network Monitoring Engine.
    Queries extended TCP and UDP tables and calculates interface throughput deltas.
    """
    def __init__(self):
        self.last_sample_time = time.time()
        self.last_in_octets, self.last_out_octets = self._get_total_octets()
        self.pid_name_cache: Dict[int, str] = {}
        self.last_cache_time = 0.0

    def _refresh_pid_cache(self):
        """Scans current processes to cache PID -> Executable name mapping."""
        now = time.time()
        if now - self.last_cache_time < 2.0 and self.pid_name_cache:
            return

        TH32CS_SNAPPROCESS = 0x00000002
        class PROCESSENTRY32W(ctypes.Structure):
            _fields_ = [
                ("dwSize", wintypes.DWORD),
                ("cntUsage", wintypes.DWORD),
                ("th32ProcessID", wintypes.DWORD),
                ("th32DefaultHeapID", ctypes.POINTER(wintypes.ULONG)),
                ("th32ModuleID", wintypes.DWORD),
                ("cntThreads", wintypes.DWORD),
                ("th32ParentProcessID", wintypes.DWORD),
                ("pcPriClassBase", wintypes.LONG),
                ("dwFlags", wintypes.DWORD),
                ("szExeFile", wintypes.WCHAR * 260),
            ]

        hSnap = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
        if hSnap == -1:
            return

        entry = PROCESSENTRY32W()
        entry.dwSize = ctypes.sizeof(PROCESSENTRY32W)

        cache = {}
        if kernel32.Process32FirstW(hSnap, ctypes.byref(entry)):
            while True:
                cache[entry.th32ProcessID] = entry.szExeFile
                if not kernel32.Process32NextW(hSnap, ctypes.byref(entry)):
                    break

        kernel32.CloseHandle(hSnap)
        self.pid_name_cache = cache
        self.last_cache_time = now

    def _get_process_name(self, pid: int) -> str:
        if pid == 0:
            return "System Idle"
        if pid == 4:
            return "System"
        name = self.pid_name_cache.get(pid)
        if name:
            return name
        return f"Process ({pid})"

    def _get_total_octets(self) -> Tuple[int, int]:
        """Calculates total inbound and outbound bytes across all active network interfaces."""
        try:
            pTable = ctypes.POINTER(MIB_IF_TABLE2)()
            res = iphlpapi.GetIfTable2(ctypes.byref(pTable))
            if res != 0 or not pTable:
                return 0, 0

            total_in = 0
            total_out = 0
            num = pTable.contents.NumEntries

            table_array = ctypes.cast(
                ctypes.addressof(pTable.contents.Table),
                ctypes.POINTER(MIB_IF_ROW2 * num)
            ).contents

            for row in table_array:
                # OperStatus == 1 indicates IfOperStatusUp
                if row.OperStatus == 1:
                    total_in += row.InOctets
                    total_out += row.OutOctets

            iphlpapi.FreeMibTable(pTable)
            return total_in, total_out
        except Exception:
            return 0, 0

    def get_bandwidth_speeds(self) -> Tuple[float, float, str, str]:
        """
        Computes live network download and upload speeds in KB/s.
        Returns: (down_kb_s, up_kb_s, formatted_down, formatted_up)
        """
        now = time.time()
        time_delta = max(0.2, now - self.last_sample_time)
        in_octets, out_octets = self._get_total_octets()

        if self.last_in_octets == 0 and self.last_out_octets == 0:
            self.last_in_octets = in_octets
            self.last_out_octets = out_octets
            self.last_sample_time = now
            return 0.0, 0.0, "0.0 KB/s", "0.0 KB/s"

        bytes_in = max(0, in_octets - self.last_in_octets)
        bytes_out = max(0, out_octets - self.last_out_octets)

        self.last_in_octets = in_octets
        self.last_out_octets = out_octets
        self.last_sample_time = now

        down_kb_s = (bytes_in / 1024.0) / time_delta
        up_kb_s = (bytes_out / 1024.0) / time_delta

        def format_speed(kb: float) -> str:
            if kb >= 1024.0:
                return f"{kb / 1024.0:.2f} MB/s"
            return f"{kb:.1f} KB/s"

        return down_kb_s, up_kb_s, format_speed(down_kb_s), format_speed(up_kb_s)

    def get_active_connections(self) -> List[Dict]:
        """
        Retrieves active TCP and UDP connections with PID, Process Name,
        Local/Remote endpoints, Service Name, and Connection State.
        """
        self._refresh_pid_cache()
        connections = []

        # --- 1. Enumerate TCP IPv4 ---
        try:
            size = wintypes.DWORD(0)
            iphlpapi.GetExtendedTcpTable(None, ctypes.byref(size), True, AF_INET, TCP_TABLE_OWNER_PID_ALL, 0)
            if size.value > 0:
                buf = ctypes.create_string_buffer(size.value)
                res = iphlpapi.GetExtendedTcpTable(buf, ctypes.byref(size), True, AF_INET, TCP_TABLE_OWNER_PID_ALL, 0)
                if res == 0:
                    num_entries = struct.unpack('I', buf.raw[:4])[0]
                    # Each row is 24 bytes: state(4), local_ip(4), local_port(4), remote_ip(4), remote_port(4), pid(4)
                    for i in range(num_entries):
                        offset = 4 + i * 24
                        state, l_ip, l_port, r_ip, r_port, pid = struct.unpack('IIIIII', buf.raw[offset:offset + 24])

                        local_ip_str = socket.inet_ntoa(struct.pack('I', l_ip))
                        remote_ip_str = socket.inet_ntoa(struct.pack('I', r_ip))
                        local_port_num = socket.ntohs(l_port)
                        remote_port_num = socket.ntohs(r_port)

                        state_str = TCP_STATES.get(state, "UNKNOWN")
                        service_name = COMMON_SERVICES.get(remote_port_num, COMMON_SERVICES.get(local_port_num, "Custom"))

                        # Don't show inactive 0.0.0.0 remote on non-listening unless relevant
                        is_active_remote = remote_ip_str not in ("0.0.0.0", "127.0.0.1") or remote_port_num > 0

                        connections.append({
                            "pid": pid,
                            "process_name": self._get_process_name(pid),
                            "protocol": "TCP",
                            "local_address": f"{local_ip_str}:{local_port_num}",
                            "remote_address": f"{remote_ip_str}:{remote_port_num}" if is_active_remote else "—",
                            "remote_ip": remote_ip_str,
                            "remote_port": remote_port_num,
                            "service": service_name,
                            "state": state_str,
                            "is_established": (state_str == "ESTABLISHED"),
                        })
        except Exception:
            pass

        # --- 2. Enumerate UDP IPv4 ---
        try:
            size = wintypes.DWORD(0)
            iphlpapi.GetExtendedUdpTable(None, ctypes.byref(size), True, AF_INET, UDP_TABLE_OWNER_PID, 0)
            if size.value > 0:
                buf = ctypes.create_string_buffer(size.value)
                res = iphlpapi.GetExtendedUdpTable(buf, ctypes.byref(size), True, AF_INET, UDP_TABLE_OWNER_PID, 0)
                if res == 0:
                    num_entries = struct.unpack('I', buf.raw[:4])[0]
                    # Each row is 12 bytes: local_ip(4), local_port(4), pid(4)
                    for i in range(num_entries):
                        offset = 4 + i * 12
                        l_ip, l_port, pid = struct.unpack('III', buf.raw[offset:offset + 12])
                        local_ip_str = socket.inet_ntoa(struct.pack('I', l_ip))
                        local_port_num = socket.ntohs(l_port)
                        service_name = COMMON_SERVICES.get(local_port_num, "UDP-Port")

                        connections.append({
                            "pid": pid,
                            "process_name": self._get_process_name(pid),
                            "protocol": "UDP",
                            "local_address": f"{local_ip_str}:{local_port_num}",
                            "remote_address": "*:*",
                            "remote_ip": "*",
                            "remote_port": 0,
                            "service": service_name,
                            "state": "BOUND",
                            "is_established": False,
                        })
        except Exception:
            pass

        # Sort: Active ESTABLISHED first, then by Process Name
        connections.sort(key=lambda c: (not c["is_established"], c["process_name"].lower()))
        return connections
