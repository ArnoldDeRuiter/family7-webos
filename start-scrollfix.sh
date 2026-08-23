#!/bin/sh
# Starts scrollfix.py in the background, unless it's already running.
# Kept as its own file (rather than inlined in index.html's exec-bridge
# call) to avoid multiple layers of shell-quoting mangling a one-liner.
DIR="$(dirname "$0")"
PIDFILE=/tmp/family7-scrollfix.pid

if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
    exit 0
fi

nohup python3 "$DIR/scrollfix.py" >/tmp/family7-scrollfix.log 2>&1 &
echo $! > "$PIDFILE"
