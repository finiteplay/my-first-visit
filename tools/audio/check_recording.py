"""Check that a native-speaker recording says the expected Icelandic name or phrase.

Transcribes the audio with the Icelandic Whisper model (CC BY 4.0, Language and Voice Lab,
Reykjavik University) and compares it with the expected text. This is a screening aid for
missing, truncated or wrong takes; it is not a pronunciation review, which still needs a
native listener.

Run with the faster-whisper environment:

    ~/.finiteplay/venv/Scripts/python tools/audio/check_recording.py take.wav "Þingvellir"
    ~/.finiteplay/venv/Scripts/python tools/audio/check_recording.py --pack is   # all takes in media.yaml

Model download (once, 3.1 GB, outside the repo):
    ~/.finiteplay/models/whisper-large-icelandic-967h-ct2  from
    huggingface.co/language-and-voice-lab/whisper-large-icelandic-62640-steps-967h-ct2
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODEL_DIR = Path.home() / ".finiteplay" / "models" / "whisper-large-icelandic-967h-ct2"


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFC", text).lower()
    return re.sub(r"[^\w\s]", "", text).strip()


def similarity(heard: str, expected: str) -> float:
    return difflib.SequenceMatcher(None, normalize(heard), normalize(expected)).ratio()


def load_model(device: str = "cpu"):
    """CPU int8 by default: short clips are fast enough, and the GPU path needs the CUDA 12
    cuBLAS/cuDNN DLLs on PATH (`--gpu` once they are installed)."""
    from faster_whisper import WhisperModel
    if device == "cuda":
        return WhisperModel(str(MODEL_DIR), device="cuda", compute_type="float16")
    return WhisperModel(str(MODEL_DIR), device="cpu", compute_type="int8")


def load_wav_16k(path: Path):
    """Read a PCM WAV without PyAV (its container API differs across installs) at 16 kHz mono."""
    import wave
    import numpy as np
    with wave.open(str(path), "rb") as wav:
        rate, channels, width = wav.getframerate(), wav.getnchannels(), wav.getsampwidth()
        raw = wav.readframes(wav.getnframes())
    if width != 2:
        raise ValueError("only 16-bit PCM WAV is supported without PyAV")
    audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    if channels > 1:
        audio = audio.reshape(-1, channels).mean(axis=1)
    if rate != 16000:
        target = int(len(audio) * 16000 / rate)
        audio = np.interp(np.linspace(0, len(audio) - 1, target), np.arange(len(audio)), audio).astype(np.float32)
    return audio


def transcribe(model, audio: Path) -> str:
    source = load_wav_16k(audio) if audio.suffix.lower() == ".wav" else str(audio)
    segments, _ = model.transcribe(source, language="is", beam_size=5, vad_filter=False)
    return " ".join(s.text.strip() for s in segments).strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("audio", nargs="?")
    ap.add_argument("expected", nargs="?")
    ap.add_argument("--pack")
    ap.add_argument("--threshold", type=float, default=0.8)
    args = ap.parse_args()
    if not MODEL_DIR.exists():
        sys.exit(f"Model not found at {MODEL_DIR}")
    model = load_model()

    jobs = []
    if args.pack:
        pack = ROOT / "content" / args.pack
        for item in json.loads((pack / "media.yaml").read_text(encoding="utf-8")).get("audio", []):
            for take, rel in item.get("files", {}).items():
                path = pack / rel
                if path.exists():
                    jobs.append((path, item["local"], f"{item['id']}/{take}"))
        if not jobs:
            print("No recorded audio files found yet (statuses are still 'missing').")
            return 0
    else:
        jobs.append((Path(args.audio), args.expected, args.audio))

    failures = 0
    for path, expected, label in jobs:
        heard = transcribe(model, path)
        score = similarity(heard, expected)
        ok = score >= args.threshold
        failures += not ok
        print(f"{'OK  ' if ok else 'CHECK'} {label}: expected {expected!r}, heard {heard!r} (match {score:.2f})")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
