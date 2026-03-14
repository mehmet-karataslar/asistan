from __future__ import annotations

import ctypes
import time
from pathlib import Path
import subprocess
from typing import Callable

from .settings import ActionSettings
from .window_control import control_active_window, control_window


class SystemActions:
    def __init__(self, logger: Callable[[str], None], status_setter: Callable[[str], None]) -> None:
        self.logger = logger
        self.status_setter = status_setter

    def run(self, settings: ActionSettings, source: str) -> None:
        action = settings.action
        if action == "uyku":
            self.sleep(source)
            return
        if action == "kapat":
            self.shutdown(source)
            return
        if action == "yeniden_baslat":
            self.restart(source)
            return
        if action == "ozel_komut":
            self.custom(settings.custom_command, source)
            return
        raise RuntimeError(f"Desteklenmeyen eylem: {action}")

    def sleep(self, source: str) -> None:
        self.logger(f"Uyku komutu gönderiliyor ({source})...")
        self.status_setter("Uyku komutu gönderildi")
        try:
            ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)

            # Birinci yol: doğrudan Windows güç API'siyle uykuya geç.
            result = ctypes.windll.powrprof.SetSuspendState(False, True, False)
            if result == 0:
                # İkinci yol: API başarısızsa komutu ayrı süreçte gönder.
                creation_flags = 0x00000008 | 0x00000200 | 0x08000000
                subprocess.Popen(
                    ["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"],
                    creationflags=creation_flags,
                )
        except Exception as exc:
            self.logger(f"Uyku komutu başarısız: {exc}")
            self.status_setter("Uyku komutu başarısız")
            raise RuntimeError("Bilgisayar uyku moduna alınamadı") from exc

    def shutdown(self, source: str) -> None:
        self.logger(f"Kapatma komutu gönderiliyor ({source})...")
        self.status_setter("Kapatma komutu gönderildi")
        try:
            result = subprocess.run(["shutdown", "/s", "/t", "0"], capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                error_text = (result.stderr or result.stdout or "Bilinmeyen hata").strip()
                raise OSError(error_text)
        except Exception as exc:
            self.logger(f"Kapatma komutu başarısız: {exc}")
            self.status_setter("Kapatma komutu başarısız")
            raise RuntimeError("Bilgisayar kapatılamadı") from exc

    def restart(self, source: str) -> None:
        self.logger(f"Yeniden baslatma komutu gönderiliyor ({source})...")
        self.status_setter("Yeniden baslatma komutu gönderildi")
        try:
            result = subprocess.run(["shutdown", "/r", "/t", "0"], capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                error_text = (result.stderr or result.stdout or "Bilinmeyen hata").strip()
                raise OSError(error_text)
        except Exception as exc:
            self.logger(f"Yeniden baslatma komutu başarısız: {exc}")
            self.status_setter("Yeniden baslatma komutu başarısız")
            raise RuntimeError("Bilgisayar yeniden baslatılamadı") from exc

    def custom(self, command: str, source: str) -> None:
        if not command.strip():
            self.status_setter("Özel komut bekleniyor")
            raise RuntimeError("Özel komut boş")
        self.logger(f"Özel komut çalıştırılıyor ({source}): {command}")
        self.status_setter("Özel komut çalıştırıldı")
        try:
            subprocess.Popen(command, shell=True)
        except Exception as exc:
            self.logger(f"Özel komut başarısız: {exc}")
            self.status_setter("Özel komut başarısız")
            raise RuntimeError("Özel komut çalıştırılamadı") from exc

    def execute_named_action(self, action: str, source: str, *, target: str = "", value: int = 0) -> None:
        if action == "sesi_ac":
            self.volume_up(max(1, value or 6), source)
            return
        if action == "sesi_kis":
            self.volume_down(max(1, value or 6), source)
            return
        if action == "sesi_sessize_al":
            self.volume_mute(source)
            return
        if action == "parlaklik_arttir":
            self.brightness_change(abs(value or 15), source)
            return
        if action == "parlaklik_azalt":
            self.brightness_change(-abs(value or 15), source)
            return
        if action == "ekrani_kilitle":
            self.lock_screen(source)
            return
        if action == "ekran_goruntusu":
            self.take_screenshot(source)
            return
        if action == "cop_kutusu_ac":
            self.open_recycle_bin(source)
            return
        if action == "wifi_ac":
            self.set_wifi(True, source)
            return
        if action == "wifi_kapat":
            self.set_wifi(False, source)
            return
        if action == "bluetooth_ac":
            self.set_bluetooth(True, source)
            return
        if action == "bluetooth_kapat":
            self.set_bluetooth(False, source)
            return
        if action == "senaryo_calistir":
            self.run_scenario(target, source)
            return
        if action == "tum_pencereleri_kucult":
            self.minimize_all_windows(source)
            return
        if action == "aktif_pencere_kucult":
            self.control_active_window("kucult", source)
            return
        if action == "aktif_pencere_buyut":
            self.control_active_window("buyut", source)
            return
        if action == "aktif_pencere_sola_yasla":
            self.control_active_window("sola_yasla", source)
            return
        if action == "aktif_pencere_saga_yasla":
            self.control_active_window("saga_yasla", source)
            return
        if action == "pencere_one_getir":
            self.control_named_window("one_getir", target, source)
            return
        if action == "pencere_kucult":
            self.control_named_window("kucult", target, source)
            return
        if action == "pencere_buyut":
            self.control_named_window("buyut", target, source)
            return
        if action == "pencere_sola_yasla":
            self.control_named_window("sola_yasla", target, source)
            return
        if action == "pencere_saga_yasla":
            self.control_named_window("saga_yasla", target, source)
            return
        raise RuntimeError(f"Desteklenmeyen komut eylemi: {action}")

    def volume_up(self, steps: int, source: str) -> None:
        self.logger(f"Ses aciliyor ({source})...")
        self.status_setter("Ses artiriliyor")
        self._press_media_key(0xAF, steps)

    def volume_down(self, steps: int, source: str) -> None:
        self.logger(f"Ses kisiliyor ({source})...")
        self.status_setter("Ses azaltiliyor")
        self._press_media_key(0xAE, steps)

    def volume_mute(self, source: str) -> None:
        self.logger(f"Ses sessize aliniyor ({source})...")
        self.status_setter("Ses sessize alindi")
        self._press_media_key(0xAD, 1)

    def brightness_change(self, delta: int, source: str) -> None:
        self.logger(f"Parlaklik ayarlaniyor ({source})...")
        self.status_setter("Parlaklik ayarlaniyor")
        current = self._get_brightness_level()
        target = min(100, max(10, current + delta))
        script = (
            "$ErrorActionPreference='Stop';"
            "$methods=Get-CimInstance -Namespace root/WMI -ClassName WmiMonitorBrightnessMethods;"
            "if(-not $methods){throw 'Parlaklik denetimi bulunamadi'};"
            f"foreach($m in $methods){{$null=$m.WmiSetBrightness(1,{target})}}"
        )
        self._run_powershell(script, "Parlaklik ayarlanamadi")
        self.logger(f"Parlaklik seviyesi: %{target}")

    def lock_screen(self, source: str) -> None:
        self.logger(f"Ekran kilitleniyor ({source})...")
        self.status_setter("Ekran kilitleniyor")
        try:
            ctypes.windll.user32.LockWorkStation()
        except Exception as exc:
            raise RuntimeError("Ekran kilitlenemedi") from exc

    def take_screenshot(self, source: str) -> None:
        self.logger(f"Ekran goruntusu aliniyor ({source})...")
        self.status_setter("Ekran goruntusu aliniyor")
        screenshot_dir = Path.home() / "Pictures" / "Asistan"
        screenshot_dir.mkdir(parents=True, exist_ok=True)
        file_path = screenshot_dir / f"ekran_goruntusu_{time.strftime('%Y%m%d_%H%M%S')}.png"
        script = (
            "Add-Type -AssemblyName System.Windows.Forms;"
            "Add-Type -AssemblyName System.Drawing;"
            "$bounds=[System.Windows.Forms.Screen]::PrimaryScreen.Bounds;"
            "$bitmap=New-Object System.Drawing.Bitmap $bounds.Width,$bounds.Height;"
            "$graphics=[System.Drawing.Graphics]::FromImage($bitmap);"
            "$graphics.CopyFromScreen($bounds.Location,[System.Drawing.Point]::Empty,$bounds.Size);"
            f"$bitmap.Save('{str(file_path).replace('\\', '\\\\')}',[System.Drawing.Imaging.ImageFormat]::Png);"
            "$graphics.Dispose();$bitmap.Dispose();"
        )
        self._run_powershell(script, "Ekran goruntusu alinamadi")
        self.logger(f"Ekran goruntusu kaydedildi: {file_path}")

    def open_recycle_bin(self, source: str) -> None:
        self.logger(f"Cop kutusu aciliyor ({source})...")
        self.status_setter("Cop kutusu aciliyor")
        try:
            subprocess.Popen(["explorer.exe", "shell:RecycleBinFolder"])
        except Exception as exc:
            raise RuntimeError("Cop kutusu acilamadi") from exc

    def set_wifi(self, enabled: bool, source: str) -> None:
        state_label = "aciliyor" if enabled else "kapatiliyor"
        self.logger(f"Wi-Fi {state_label} ({source})...")
        self.status_setter(f"Wi-Fi {state_label}")
        action = "Enable-NetAdapter" if enabled else "Disable-NetAdapter"
        script = (
            "$ErrorActionPreference='Stop';"
            "$adapter=Get-NetAdapter | Where-Object {$_.Name -match 'Wi-Fi|Kablosuz|Wireless|WLAN'} | Select-Object -First 1;"
            "if(-not $adapter){throw 'Wi-Fi bagdastiricisi bulunamadi'};"
            f"{action} -Name $adapter.Name -Confirm:$false"
        )
        self._run_powershell(script, "Wi-Fi durumu degistirilemedi")

    def set_bluetooth(self, enabled: bool, source: str) -> None:
        state_label = "aciliyor" if enabled else "kapatiliyor"
        self.logger(f"Bluetooth {state_label} ({source})...")
        self.status_setter(f"Bluetooth {state_label}")
        state = "On" if enabled else "Off"
        script = (
            "$ErrorActionPreference='Stop';"
            "Add-Type -AssemblyName System.Runtime.WindowsRuntime;"
            "$null=[Windows.Devices.Radios.Radio,Windows.Devices.Radios,ContentType=WindowsRuntime];"
            "$radiosTask=[Windows.Devices.Radios.Radio]::GetRadiosAsync();"
            "$radios=[System.WindowsRuntimeSystemExtensions]::AsTask($radiosTask).Result;"
            "$targets=$radios | Where-Object {$_.Kind -eq [Windows.Devices.Radios.RadioKind]::Bluetooth};"
            "if(-not $targets){throw 'Bluetooth radyosu bulunamadi'};"
            f"foreach($radio in $targets){{[System.WindowsRuntimeSystemExtensions]::AsTask($radio.SetStateAsync([Windows.Devices.Radios.RadioState]::{state})).Wait()}}"
        )
        self._run_powershell(script, "Bluetooth durumu degistirilemedi")

    def run_scenario(self, scenario_name: str, source: str) -> None:
        scenario_steps = {
            "ders_modu": [
                ("sesi_sessize_al", ""),
                ("parlaklik_azalt", "15"),
                ("tum_pencereleri_kucult", ""),
            ],
            "is_modu": [
                ("wifi_ac", ""),
                ("parlaklik_arttir", "10"),
                ("sesi_kis", "4"),
            ],
            "oyun_modu": [
                ("parlaklik_arttir", "20"),
                ("sesi_ac", "8"),
            ],
            "toplanti_modu": [
                ("sesi_sessize_al", ""),
                ("parlaklik_arttir", "5"),
            ],
            "gece_modu": [
                ("parlaklik_azalt", "25"),
                ("sesi_kis", "8"),
            ],
        }
        steps = scenario_steps.get(scenario_name)
        if not steps:
            raise RuntimeError(f"Bilinmeyen senaryo: {scenario_name}")

        self.logger(f"Senaryo calistiriliyor ({source}): {scenario_name}")
        for action_name, raw_value in steps:
            self.execute_named_action(action_name, f"senaryo:{scenario_name}", value=int(raw_value or 0))
        self.status_setter(f"Senaryo tamamlandi: {scenario_name}")

    def control_named_window(self, action: str, target: str, source: str) -> None:
        self.logger(f"Pencere eylemi calisiyor ({source}): {target} -> {action}")
        ok, msg = control_window(action, target)
        self.logger(msg)
        if not ok:
            raise RuntimeError(msg)
        self.status_setter(msg)

    def control_active_window(self, action: str, source: str) -> None:
        self.logger(f"Aktif pencere eylemi calisiyor ({source}): {action}")
        ok, msg = control_active_window(action)
        self.logger(msg)
        if not ok:
            raise RuntimeError(msg)
        self.status_setter(msg)

    def minimize_all_windows(self, source: str) -> None:
        self.logger(f"Tum pencereler kucultuluyor ({source})...")
        self.status_setter("Tum pencereler kucultuluyor")
        self._press_key_combo([(0x5B, True), (0x4D, True), (0x4D, False), (0x5B, False)])

    def _press_media_key(self, key_code: int, times: int) -> None:
        for _ in range(max(1, times)):
            ctypes.windll.user32.keybd_event(key_code, 0, 0, 0)
            ctypes.windll.user32.keybd_event(key_code, 0, 2, 0)
            time.sleep(0.03)

    def _press_key_combo(self, sequence: list[tuple[int, bool]]) -> None:
        for key_code, is_down in sequence:
            flags = 0 if is_down else 2
            ctypes.windll.user32.keybd_event(key_code, 0, flags, 0)
            time.sleep(0.03)

    def _get_brightness_level(self) -> int:
        script = (
            "$value=Get-CimInstance -Namespace root/WMI -ClassName WmiMonitorBrightness | "
            "Select-Object -ExpandProperty CurrentBrightness -First 1;"
            "Write-Output $value"
        )
        result = self._run_powershell(script, "Parlaklik okunamadi", expect_output=True)
        try:
            return int((result or "50").strip())
        except Exception:
            return 50

    def _run_powershell(self, script: str, error_message: str, *, expect_output: bool = False) -> str:
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
                capture_output=True,
                text=True,
                timeout=25,
                check=False,
            )
            if result.returncode != 0:
                details = (result.stderr or result.stdout or "Bilinmeyen hata").strip()
                raise OSError(details)
            return (result.stdout or "").strip() if expect_output else ""
        except Exception as exc:
            self.logger(f"{error_message}: {exc}")
            self.status_setter(error_message)
            raise RuntimeError(error_message) from exc
