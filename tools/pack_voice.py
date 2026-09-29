"""Packs the voice clips in voice/ into one audio file plus a small index.

Usage: python3 tools/pack_voice.py voice <output folder>
Writes voice.mp4 (all clips, AAC) and voice.json (where each clip starts and how long it is).
One file downloads and caches far better than 132 small ones, on tablets and on GitHub.
Uses only the Python standard library and macOS `afconvert`.
"""
import array
import json
import os
import subprocess
import sys
import tempfile
import wave

RATE = 22050
GAP = 0.25   # silence between clips, so a small decoder offset never clips a word
LEAD = 0.3   # silence before the first clip


def read_pcm(path, tmp):
    """Decodes one clip to 16-bit mono samples."""
    wav = os.path.join(tmp, "clip.wav")
    subprocess.run(["afconvert", "-f", "WAVE", "-d", "LEI16@%d" % RATE, "-c", "1", path, wav], check=True)
    data = open(wav, "rb").read()
    i = data.index(b"data") + 8   # afconvert writes an extended header wave can't read; find the samples directly
    size = int.from_bytes(data[i - 4:i], "little")
    return array.array("h", data[i:i + size])


def main():
    src, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    names = sorted(f[:-4] for f in os.listdir(src) if f.endswith(".mp4"))
    samples = array.array("h", [0] * int(LEAD * RATE))
    index = {}
    with tempfile.TemporaryDirectory() as tmp:
        for name in names:
            pcm = read_pcm(os.path.join(src, name + ".mp4"), tmp)
            index[name] = [round(len(samples) / RATE, 4), round(len(pcm) / RATE, 4)]
            samples.extend(pcm)
            samples.extend([0] * int(GAP * RATE))
        # The first loud moment lets the game correct any start delay the decoder adds.
        marker = next(i for i, v in enumerate(samples) if abs(v) > 650) / RATE
        wav = os.path.join(tmp, "all.wav")
        with wave.open(wav, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(RATE)
            wf.writeframes(samples.tobytes())
        subprocess.run(["afconvert", "-f", "m4af", "-d", "aac", "-b", "64000", wav, os.path.join(out, "voice.mp4")], check=True)
    with open(os.path.join(out, "voice.json"), "w") as f:
        json.dump({"marker": round(marker, 4), "clips": index}, f, separators=(",", ":"))
    print("Packed %d clips into %s/voice.mp4 (%.0f KB)" % (len(names), out, os.path.getsize(os.path.join(out, "voice.mp4")) / 1024))


if __name__ == "__main__":
    main()
