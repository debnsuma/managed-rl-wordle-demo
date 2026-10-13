#!/bin/sh
# Launch the booth demo full screen in kiosk mode (macOS). Ctrl+Q or Cmd+Q quits.
cd "$(dirname "$0")"
caffeinate -d -i &                                   # keep the display awake while the demo runs
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
exec "$CHROME" --kiosk --noerrdialogs --disable-session-crashed-bubble --disable-infobars \
  --autoplay-policy=no-user-gesture-required --user-data-dir="$TMPDIR/booth-chrome" \
  "file://$PWD/index.html"
