# Family7 (webOS)

Unofficial Family7+ wrapper for rooted LG webOS TVs, built as a Homebrew
Channel app. Not affiliated with Family7. Use at your own risk.

## How it works

Same one-line-redirect technique as
[f1tv-webos](https://github.com/ArnoldDeRuiter/f1tv-webos) in this same
account — see that repo's README for the full explanation of *why* this
tiny approach works (native webOS browser engine, per-app persistent cookie
storage, no custom code needed for login or playback).

```html
<script>location.href = "https://www.family7.nl/ondemandkijken";</script>
```

## What this actually solves, and what's still unverified

**Solved, high confidence** (same mechanism the F1TV wrapper relies on):
- **Stay logged in** — each installed app gets its own persistent cookie
  storage, exactly like leaving a browser tab open forever. Log in once,
  it stays.
- **No browser border** — this is a native app window, not the system
  Browser app, so there's no address bar/chrome to begin with.

**Tested live in a desktop browser tonight, genuinely promising but not a
guarantee on the real TV:**
- **D-pad navigation.** Checked the catalog/browse pages first: pressing
  Tab moves focus through real semantic `<a>`/`<button>` elements in a
  sensible order (verified via `document.activeElement`, not just
  eyeballing screenshots) — e.g. landed cleanly on the "Afspelen" (Play)
  button and the "Mijn lijst" button in sequence. That's a good sign;
  webOS maps D-pad up/down/left/right to standard tab-order focus movement
  on plain HTML, so this part should carry over.
- **The actual video player is a different story, technically.** The
  player itself isn't part of family7.nl's own page — it's a cross-origin
  iframe from a separate white-label video platform,
  `family7.tv/player.php?itemtoken=...`. That means its internal
  accessibility can't be inspected or guaranteed from outside (cross-origin
  restrictions block that from a wrapper's point of view, same as they
  would in F1TV's own related-but-different embedding situation). What
  *was* observed: pressing Tab while the player was open visibly expanded
  its control bar (rewind/forward buttons appeared), which means keyboard
  focus is doing *something* real inside that iframe — a good sign, but
  full play/pause/seek/volume operability via D-pad was not exhaustively
  confirmed.

If D-pad control of actual playback doesn't fully work once installed,
there's no fix available from this wrapper's side — that's Family7's
video-platform vendor's code, entirely outside this app's control.

## Installing

```sh
./build.sh
```
produces `nl.arnolderuiter.family7_<version>_all.ipk`.

## License

MIT.
