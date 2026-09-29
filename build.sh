#!/bin/sh
# Builds the two outputs from game.html and the voice clips:
#   docs/                        the installable web app (GitHub Pages serves this folder)
#   android/app/src/main/assets/ the same game inside the Android app
set -e
cd "$(dirname "$0")"
ASSETS=android/app/src/main/assets
rm -rf docs web "$ASSETS"
mkdir -p docs "$ASSETS"

python3 tools/pack_voice.py voice docs

{
  printf '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
  printf '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover, user-scalable=no">\n'
  printf '<meta name="theme-color" content="#150F3B">\n'
  printf '<link rel="manifest" href="manifest.webmanifest">\n'
  printf '<link rel="icon" href="icon-192.png">\n'
  printf '<link rel="apple-touch-icon" href="apple-touch-icon.png">\n'
  printf '<meta name="apple-mobile-web-app-capable" content="yes">\n'
  printf '<meta name="mobile-web-app-capable" content="yes">\n'
  printf '<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">\n'
  printf '<meta name="apple-mobile-web-app-title" content="Math Rocket">\n'
  printf '</head>\n<body>\n'
  # Use the bundled font instead of Google's, so the app looks the same with no internet.
  sed 's#<link rel="stylesheet" href="https://fonts.googleapis.com/[^>]*>#<style>@font-face{font-family:"Baloo 2";font-weight:600 800;font-display:swap;src:url(fonts/baloo2.woff2) format("woff2")}</style>#' game.html
  printf '\n</body>\n</html>\n'
} > docs/index.html

cp site/manifest.webmanifest site/icon-192.png site/icon-512.png site/apple-touch-icon.png docs/
mkdir -p docs/fonts "$ASSETS/fonts"
cp site/fonts/baloo2.woff2 docs/fonts/
cp site/fonts/baloo2.woff2 "$ASSETS/fonts/"
# A new cache name each time the game or voice changes, so installed copies update themselves.
VERSION=$(cat docs/index.html docs/voice.json | shasum | cut -c1-10)
sed "s/__VERSION__/$VERSION/" site/sw.js > docs/sw.js
touch docs/.nojekyll

cp docs/index.html docs/voice.mp4 docs/voice.json "$ASSETS/"
echo "Built docs/ ($(du -sh docs | cut -f1)) and the Android assets. Version $VERSION"
