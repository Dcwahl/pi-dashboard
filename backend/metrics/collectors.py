import psutil
import os
from pathlib import Path
from datetime import timedelta

def get_cpu_usage():
    """Get CPU usage statistics"""
    return {
        "percent": psutil.cpu_percent(interval=1),
        "per_cpu": psutil.cpu_percent(interval=1, percpu=True),
        "count": psutil.cpu_count(),
        "frequency": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
    }

def get_memory_usage():
    """Get memory usage statistics"""
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    
    return {
        "total": mem.total,
        "available": mem.available,
        "used": mem.used,
        "percent": mem.percent,
        "swap": {
            "total": swap.total,
            "used": swap.used,
            "percent": swap.percent
        }
    }

def get_disk_usage():
    """Get disk usage statistics"""
    disk = psutil.disk_usage('/')
    io = psutil.disk_io_counters()
    
    return {
        "total": disk.total,
        "used": disk.used,
        "free": disk.free,
        "percent": disk.percent,
        "io": {
            "read_bytes": io.read_bytes,
            "write_bytes": io.write_bytes,
            "read_count": io.read_count,
            "write_count": io.write_count
        } if io else None
    }

def get_temperature():
    """Get system temperature - works on Raspberry Pi"""
    temps = {}
    
    # Try psutil first
    if hasattr(psutil, "sensors_temperatures"):
        sensors = psutil.sensors_temperatures()
        if sensors:
            temps["sensors"] = {
                name: [{"label": temp.label, "current": temp.current} 
                       for temp in temps_list]
                for name, temps_list in sensors.items()
            }
    
    # Fallback to reading thermal zones directly (common on Pi)
    thermal_zones = Path("/sys/class/thermal")
    if thermal_zones.exists():
        zones = []
        for zone in thermal_zones.glob("thermal_zone*"):
            temp_file = zone / "temp"
            type_file = zone / "type"
            if temp_file.exists():
                try:
                    temp = int(temp_file.read_text().strip()) / 1000.0
                    zone_type = type_file.read_text().strip() if type_file.exists() else "unknown"
                    zones.append({
                        "zone": zone.name,
                        "type": zone_type,
                        "temperature": temp
                    })
                except (ValueError, IOError):
                    pass
        
        if zones:
            temps["thermal_zones"] = zones
    
    return temps

def get_network_stats():
    """Get network statistics"""
    net_io = psutil.net_io_counters()
    
    return {
        "bytes_sent": net_io.bytes_sent,
        "bytes_recv": net_io.bytes_recv,
        "packets_sent": net_io.packets_sent,
        "packets_recv": net_io.packets_recv,
        "errin": net_io.errin,
        "errout": net_io.errout,
        "dropin": net_io.dropin,
        "dropout": net_io.dropout
    }

def get_system_uptime():
    """Get system uptime"""
    boot_time = psutil.boot_time()
    uptime_seconds = psutil.time.time() - boot_time
    uptime = timedelta(seconds=uptime_seconds)
    
    return {
        "boot_time": boot_time,
        "uptime_seconds": uptime_seconds,
        "uptime_formatted": str(uptime).split('.')[0]  # Remove microseconds
    }