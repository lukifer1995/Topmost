import psutil
import wmi


def getCpuRam():
    memory_usage = psutil.virtual_memory().percent
    return int(memory_usage)


