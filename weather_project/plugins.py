import comtypes
from ctypes import POINTER, cast
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IMMNotificationClient, IMMDeviceEnumerator, IAudioEndpointVolume
import subprocess
# pip install pycaw comtypes



class AudioNotificationClient(IMMNotificationClient):
    def OnDefaultDeviceChanged(self, flow, role, default_device_id):
        devices = AudioUtilities.GetAllDevices()
        for d in devices:
            if d.id == default_device_id:
                name = d.FriendlyName.lower()
                if "headphone" in name or "headset" in name:
                    print(f"🆕 Headphone connected: {name}")
                    subprocess.Popen(["start", "wmplayer", "C:\\Path\\To\\Music.mp3"], shell=True)

    # Các hàm khác phải có (dù không dùng)
    def OnDeviceAdded(self, device_id): pass
    def OnDeviceRemoved(self, device_id): pass
    def OnDeviceStateChanged(self, device_id, new_state): pass
    def OnPropertyValueChanged(self, device_id, key): pass

def main():
    from comtypes.client import CreateObject
    enumerator = CreateObject(IMMDeviceEnumerator, interface=IMMDeviceEnumerator)
    client = AudioNotificationClient()
    enumerator.RegisterEndpointNotificationCallback(client)
    print("🎧 Đang theo dõi sự kiện âm thanh (realtime)...")

    import pythoncom
    while True:
        pythoncom.PumpWaitingMessages()

if __name__ == "__main__":
    main()
