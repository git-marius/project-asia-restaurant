import os
import shlex
import subprocess
from pathlib import Path


def _duration_seconds(duration_seconds: int | None = None) -> int:
    """Nutzt übergebenen Wert oder Standarddauer aus VIDEO_CAPTURE_DURATION_SECONDS."""
    return duration_seconds or int(os.getenv("VIDEO_CAPTURE_DURATION_SECONDS", "5"))


def capture_mp4(output_path: Path, duration_seconds: int | None = None) -> Path:
    """Nimmt ein Video auf und stellt sicher, dass am Ende eine MP4-Datei existiert."""
    duration = _duration_seconds(duration_seconds)
    duration_ms = duration * 1000
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Optionaler Test-/Alternativbefehl, z. B. für lokale ffmpeg-Testvideos ohne Raspberry-Pi-Kamera.
    custom_command = os.getenv("VIDEO_CAPTURE_COMMAND")
    if custom_command:
        command = custom_command.format(
            output=shlex.quote(str(output_path)),
            duration_seconds=duration,
            duration_ms=duration_ms,
        )
        subprocess.run(command, shell=True, check=True, timeout=duration + 30)
        if not output_path.exists():
            raise FileNotFoundError(f"Capture command did not create {output_path}")
        return output_path

    # Standard auf dem Raspberry Pi: erst rohes H264 mit raspivid aufnehmen.
    raw_path = output_path.with_suffix(".h264")
    # Danach in einen browserfähigen MP4-Container schreiben.
    subprocess.run(
        [
            "raspivid",
            "-o",
            str(raw_path),
            "-t",
            str(duration_ms),
            "-w",
            "320",
            "-h",
            "240",
            "-fps",
            "10",
            "-b",
            "500000",
        ],
        check=True,
        timeout=duration + 30,
    )
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-framerate",
            "10",
            "-i",
            str(raw_path),
            "-c",
            "copy",
            "-movflags",
            "+faststart",
            str(output_path),
        ],
        check=True,
        timeout=duration + 30,
    )
    return output_path


def capture(filename):
    """Kompatibler Wrapper für bestehenden Code: erzeugt jetzt MP4 statt rohem H264."""
    return capture_mp4(Path(f"{filename}.mp4"))
