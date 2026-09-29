"""Builds the teacher's voice clips for Math Rocket with Piper (offline neural speech).

Usage:
    python make_voice.py <voice.onnx> <output folder>            # all clips (.mp4, AAC audio)
    python make_voice.py <voice.onnx> <output file.wav> --sample # one demo sentence

The game joins clips such as "what is" + "38" + "plus" + "47" at play time, so every
question can be spoken without recording thousands of sentences.

Neural voices garble very short words said on their own (a one-word "add" can come out
as a hum). So numbers and joining words are spoken inside a whole sentence, e.g.
"Seven plus three.", and the word is cut out using Piper's timing for each sound.

Needs: pip install piper-tts onnx, and macOS `afconvert` for the audio files.
"""
import os
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
import piper
from piper import PiperVoice, SynthesisConfig

ONES = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
        "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"]
TENS = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]


def number_words(n):
    if n < 20:
        return ONES[n]
    return TENS[n // 10] + ("" if n % 10 == 0 else " " + ONES[n % 10])


# Clip name -> (words before, the words we keep, words after), or a plain sentence kept whole.
# Names must match the clip names used in game.html.
CLIPS = {
    "add": ("Seven", "plus", "three."),
    "sub": ("Nine", "minus", "four."),
    "equals": ("Five plus three", "equals", "eight."),
    "whatnum": ("Five plus", "what number", "equals eight?"),
    "q0": ("", "What is", "five plus three?"),
    "q1": ("", "So, what is", "five plus three?"),
    "q2": ("", "Can you work out", "five plus three?"),
    "q3": ("", "Right then, what is", "five plus three?"),
    "yes": ("", "Yes,", "five plus three equals eight."),
    "right": ("", "That's right,", "five plus three equals eight."),
    "welldone": ("", "Well done,", "five plus three equals eight."),
    "puzzle": "Here's a puzzle.",
    "c0": "Well done, that's right!", "c1": "Brilliant, well done!", "c2": "Lovely work!", "c3": "Fantastic, well done!",
    "c4": "Yes, spot on!", "c5": "Super job!", "c6": "You're a star!", "c7": "Great thinking!",
    "g0": "Ooh, not quite. Have another go.", "g1": "Good try! Let's count them together.",
    "g2": "Nearly! You can do it.", "g3": "So close. Have one more go.",
    "end3": "Wow, three stars! That was perfect.", "end2": "Well done, two stars! Lovely work.",
    "end1": "You did it! Let's have another go for more stars.",
    "endboss": "Hooray! You beat Zorp. Well done!",
    "endall": "Hooray! You've finished every planet. What a superstar!",
    "hello": "Hello! I'll read the questions with you. Let's get started.",
    "test0": "Hello there! Ready to fly? Shall we do some maths together?",
    "test1": "Hello, space explorer! Let's do some plus and minus together.",
}
for i in range(100):
    CLIPS["n%d" % i] = ("The answer is", number_words(i), ".")

SAMPLE = ("Hello, space explorer! Right then, what is thirty-eight plus forty-seven? "
          "Well done, that's right! Ooh, not quite. Have another go.")


def config(pace):
    return SynthesisConfig(length_scale=pace)


def word_count(voice, text):
    """How many words espeak hears in text (so we know where our words sit)."""
    if not text.strip():
        return 0
    phonemes = [p for sentence in voice.phonemize(text) for p in sentence]
    return len([w for w in "".join(phonemes).split(" ") if w.strip(",.!?;:")])


def speak_in_sentence(voice, before, keep, after, pace):
    """Speaks before+keep+after as one sentence and returns only the audio for `keep`."""
    text = " ".join(t for t in (before, keep, after) if t).replace(" .", ".")
    chunks = list(voice.synthesize(text, syn_config=config(pace), include_alignments=True))
    if len(chunks) != 1 or not chunks[0].phoneme_alignments:
        raise RuntimeError("No timing for: " + text)
    chunk = chunks[0]
    audio = chunk.audio_int16_array.astype(np.float32)

    # Group the sounds into words, noting where each starts and ends in the audio.
    words, pos, cur = [], 0, None
    for a in chunk.phoneme_alignments:
        if a.phoneme in ("^", "$", " ") or a.phoneme in ",.!?;:":
            if cur and a.phoneme in (" ", "$"):
                words.append(cur)
                cur = None
            elif cur:
                cur[1] = pos + a.num_samples
        else:
            cur = cur or [pos, pos]
            cur[1] = pos + a.num_samples
        pos += a.num_samples
    if cur:
        words.append(cur)

    first = word_count(voice, before)
    last = len(words) - word_count(voice, after)
    if not 0 <= first < last <= len(words):
        raise RuntimeError("Could not find %r in %r (%d words)" % (keep, text, len(words)))
    return cut_at_quiet(audio, words[first][0], words[last - 1][1], chunk.sample_rate), chunk.sample_rate


def cut_at_quiet(audio, start, end, rate):
    """Moves each cut to the quietest moment nearby so no neighbouring sound leaks in."""
    frame = int(.005 * rate)

    def quietest(lo, hi):
        lo, hi = max(0, lo), min(len(audio) - frame, hi)
        if hi <= lo:
            return max(0, min(lo, len(audio)))
        best = min(range(lo, hi, frame), key=lambda i: np.sqrt(np.mean(audio[i:i + frame] ** 2)))
        return best + frame // 2

    s = quietest(start - int(.06 * rate), start + int(.005 * rate))
    e = quietest(end - int(.005 * rate), end + int(.08 * rate))
    clip = audio[s:e].copy()
    fade = min(int(.008 * rate), len(clip) // 4)
    if fade:
        clip[:fade] *= np.linspace(0, 1, fade)
        clip[-fade:] *= np.linspace(1, 0, fade)
    return clip


def speak_whole(voice, text, pace):
    parts = [c for c in voice.synthesize(text, syn_config=config(pace))]
    return np.concatenate([c.audio_int16_array for c in parts]).astype(np.float32), parts[0].sample_rate


def tidy(audio, rate):
    """Trims silence at both ends and evens out loudness so joined clips flow."""
    loud = np.where(np.abs(audio) > 400)[0]
    if len(loud):
        audio = audio[max(0, loud[0] - int(.02 * rate)): loud[-1] + int(.04 * rate)]
    peak = np.max(np.abs(audio)) or 1
    return np.clip(audio * (0.89 * 32767 / peak), -32767, 32767).astype(np.int16)


def save_wav(path, audio, rate):
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(audio.tobytes())


def main():
    model, out = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
    # espeak-ng can't handle very long data paths, so load its data by a short relative path.
    os.chdir(Path(piper.__file__).parent)
    voice = PiperVoice.load(str(model), espeak_data_dir="espeak-ng-data", include_alignments=True)

    if "--sample" in sys.argv:
        audio, rate = speak_whole(voice, SAMPLE, 1.05)
        save_wav(out, audio.astype(np.int16), rate)
        return

    out.mkdir(parents=True, exist_ok=True)
    for name, spec in CLIPS.items():
        if isinstance(spec, tuple):
            audio, rate = speak_in_sentence(voice, *spec, pace=1.08)
        else:
            audio, rate = speak_whole(voice, spec, 1.03)
        text = " ".join(spec[1:2]) if isinstance(spec, tuple) else spec
        sounds = sum(len(s) for s in voice.phonemize(text))
        seconds = len(audio) / rate
        if seconds > 0.35 + sounds * 0.13:
            print("WARNING: %s is %.2fs for %d sounds - may be garbled" % (name, seconds, sounds))
        wav = out / (name + ".wav")
        save_wav(wav, tidy(audio, rate), rate)
        subprocess.run(["afconvert", "-f", "m4af", "-d", "aac", "-b", "48000", str(wav), str(out / (name + ".mp4"))], check=True)
        wav.unlink()
    print("Made %d clips in %s" % (len(CLIPS), out))


if __name__ == "__main__":
    main()
