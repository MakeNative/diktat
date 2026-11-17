#!/bin/sh
# Installiert Diktat auf einem Mac: uv (falls nötig), Diktat selbst und die App „Diktat“.
# Erneut ausführen aktualisiert auf den neuesten Stand.
set -eu

SOURCE="${DIKTAT_SOURCE:-https://github.com/MakeNative/diktat/archive/refs/heads/main.zip}"
APP="$HOME/Applications/Diktat.app"

step() { printf '\n==> %s\n' "$1"; }
fail() { printf '\nFehler: %s\n' "$1" >&2; exit 1; }

[ "$(uname -s)" = Darwin ] || fail "Diktat läuft bisher nur auf dem Mac."
[ "$(sysctl -n hw.optional.arm64 2>/dev/null)" = 1 ] || fail "Diktat braucht einen Mac mit Apple-Chip (M1 oder neuer)."

if command -v uv >/dev/null 2>&1; then
  UV=$(command -v uv)
else
  UV="$HOME/.local/bin/uv"
  if [ ! -x "$UV" ]; then
    step "Installiere uv, das Werkzeug, das Diktat und Python einrichtet …"
    curl -LsSf https://astral.sh/uv/install.sh | sh
  fi
fi

step "Installiere Diktat (lädt etwa 300 MB, dauert ein paar Minuten) …"
"$UV" tool install --force --python 3.12 "diktat @ $SOURCE"
DIKTAT="$("$UV" tool dir --bin)/diktat"
[ -x "$DIKTAT" ] || fail "Diktat wurde nicht gefunden unter $DIKTAT."

step "Lege die App „Diktat“ an …"
mkdir -p "$(dirname "$APP")"
rm -rf "$APP"
osacompile -o "$APP" \
  -e "set cmd to (quoted form of \"$DIKTAT\") & \" --detach\"" \
  -e "do shell script cmd"

step "Fertig. Diktat startet jetzt im Browser."
echo "Beim ersten Start lädt Diktat einmalig das Sprachmodell (etwa 1,6 GB)."
echo "Später öffnest du Diktat über Spotlight (⌘ + Leertaste, „Diktat“ tippen, Enter)."
open "$APP"
