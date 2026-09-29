# Math Rocket

An offline maths game for Android tablets. The child picks **Addition** or
**Subtraction** on the home screen; each path has 10 planets × 10 levels (200 levels),
answered by tapping A, B, C or D. Every number and answer stays at 99 or below.

| Planet | Addition | Subtraction |
|---|---|---|
| 1 | Add up to 10 (pictures) | Take away up to 10 (pictures) |
| 2 | Add up to 20 | Take away up to 20 |
| 3 | Missing numbers to 20 | Crossing ten: 13 − 8 |
| 4 | Three numbers | Missing numbers to 20 |
| 5 | Tens: 40 + 30, 10 more | Tens: 80 − 30, 10 less |
| 6 | Tens and ones: 47 + 8 | Tens and ones: 42 − 7 |
| 7 | 2-digit, no carrying: 23 + 45 | 2-digit, no borrowing: 68 − 25 |
| 8 | Carrying: 38 + 47 | Borrowing: 72 − 38 |
| 9 | Missing numbers to 99 | Missing numbers to 99 |
| 10 | Big mix (20 + 15 + 30) | Big mix (90 − 20 − 15) |

Each level has 5 questions; level 10 of every planet is a boss (Zorp) with 8.
Stars: 3 = all right the first time, 2 = at least 70%, 1 = finished.
Finishing a level unlocks the next; beating the boss unlocks the next planet.
Questions are generated fresh every time, so replaying is never the same.

The "Talking teacher" (Settings) reads questions and cheers in a natural British
woman's voice ("Cori"). The voice is pre-made audio in `voice/` (133 clips: numbers
0–99 plus phrases), joined together as the child plays, so it sounds the same on every
tablet and needs no internet. It was made with Piper, a free offline neural voice;
the Cori voice is trained on public-domain LibriVox recordings.

To remake or change the voice (for example to add new phrases):

    pip install piper-tts onnx
    # download en_GB-cori-high.onnx and .onnx.json from huggingface.co/rhasspy/piper-voices
    python tools/make_voice.py en_GB-cori-high.onnx voice
    ./build.sh

## Files

- `game.html` – the game (edit this one)
- `voice/` – Cori's voice clips; `tools/make_voice.py` remakes them
- `site/` – app icon, install details (manifest) and offline cache (service worker)
- `build.sh` – builds everything below from the files above
- `docs/` – the finished web app, about 1.5 MB (GitHub Pages serves this folder)
- `android/` – Android Studio project wrapping the same game
- `.github/workflows/build-apk.yml` – builds the Android APK on GitHub for free

After changing the game or voice, run `./build.sh`.

## Put it online with GitHub (for iPad and Android)

1. Create a **public** repository on github.com (GitHub Pages is free for public repos)
   and upload everything in this folder to it.
2. In the repository: **Settings › Pages › Build and deployment**, choose
   **Deploy from a branch**, branch **main**, folder **/docs**, then **Save**.
3. After a minute the game is at `https://<your-username>.github.io/<repository-name>/`.

## Install on the iPad

1. Open the link in **Safari** (it must be Safari) while online.
2. Tap **Share › Add to Home Screen › Add**.
3. Open Math Rocket from its new icon once while still online, so it saves itself.
   After that it works with no internet, voice included.

On iPads with a side mute switch, turn silent mode off to hear the voice.

## Install on an Android tablet

**Easiest:** open the same link in **Chrome**, then **⋮ menu › Install app** (or
**Add to Home screen**). Works offline after the first visit.

**Or as a real app (APK):** in the GitHub repository open **Actions › Build APK ›
Run workflow**, wait about 5 minutes, and download **MathRocket-apk** from the finished run.
Copy the APK to the tablet, tap it, and allow "Install unknown apps" when asked.
The APK needs Android 8.0 or newer.

Or build it yourself: open the `android` folder in Android Studio and choose
Build › Build App Bundle(s) / APK(s) › Build APK(s).
