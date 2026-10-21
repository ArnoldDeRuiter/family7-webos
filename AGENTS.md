# AGENTS.md

Read `~/git/personal/slopbro/TV-HANDOVER.md` first for the TV's IP/SSH
access, CDP, root exec bridge, and standing rules. This file covers what's
specific to this repo.

## What this is

`type: web` Homebrew app (`nl.arnolderuiter.family7`) — full-screen wrapper
around a Family7 streaming site. Two background daemons started via the
root exec bridge from `index.html`, chained `"sh scrollfix; sh loginfill"`:

- `scrollfix.py` — fixes remote-control scroll/focus navigation (the real
  site wasn't built with a TV remote in mind).
- `loginfill.py` — login autofill, same architecture as f1tv-webos's. Auth
  session check uses an `SSESS`-prefixed cookie (Drupal convention).

See `TODO.md` — login autofill sometimes doesn't trigger yet, not root-caused.

## Build

```sh
sh build.sh
```

Hand-rolled `.ipk`, version from `appinfo.json`. **Don't hand-bump the
version** — CI auto-derives it from the release tag at build time (no git
push-back). Local `appinfo.json` version is stale by design.

## Testing changes live (do this before committing anything TV-facing)

```sh
scp index.html loginfill.py scrollfix.py start-loginfill.sh start-scrollfix.sh \
  tvtje:/media/developer/apps/usr/palm/applications/nl.arnolderuiter.family7/
```

Relaunch on the TV, check `/tmp/family7-loginfill.log` /
`/tmp/family7-scrollfix.log` (or equivalent — check actual filenames in the
`start-*.sh` scripts) over SSH before committing.

## Gotchas

- React-controlled `<input>` fields need the native-setter trick, not plain
  `.value = x` — see `setReactInputValue` in `loginfill.py`.
- Polling (not `MutationObserver`) is used to detect when login fields are
  ready — the site rebuilds DOM nodes during its loading-spinner → form
  transition, which discards nodes an observer would be watching.

## Rules

- Never `git push` — Captain pushes himself.
