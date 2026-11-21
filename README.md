# WORLD / 21 NOV 2026

[![make.fun · news-image-20261121](https://make.fun/badge/news-image-20261121.svg)](https://make.fun/bounty/news-image-20261121?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)
[![rank](https://make.fun/badge/news-image-20261121/hyiiiii/news-image-20261121/rank.svg)](https://make.fun/bounty/news-image-20261121/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)
[![reward](https://make.fun/badge/news-image-20261121/hyiiiii/news-image-20261121/reward.svg)](https://make.fun/bounty/news-image-20261121?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)

An original editorial front-page illustration for the **make.fun** news-image
bounty, depicting the world news of Saturday 21 November 2026 as an early
edition.

- [make.fun](https://make.fun/)
- [Bounty](https://make.fun/bounty/news-image-20261121)

## Ownership metadata

`.makefun/owner.json` declares the account's confirmed public Solana entry
wallet for make.fun's `repo_owner` ownership rule. It is public ownership
metadata only: not a private key, signature, transfer, or claim of reward. It
lets ownership be read from this repository instead of relying on an
unconfirmed make.fun GitHub-link setting.

The shipped image is `assets/entry.png`: 1024 x 1024 RGB, created for this
entry. It is not a dashboard of cards. One dominant Riyadh night scene carries
the lead, with an atlas globe and four compact dispatch windows for COP31,
North Korea, Iran–US diplomacy, and the scheduled Dragon return.

## Local runtime

```sh
python3 main.py
```

The installer requires only Python 3 and its standard library. It never uses
the network. It reads `assets/entry.png` relative to `main.py`, validates the
PNG signature, chunk CRCs, IHDR dimensions and RGB format, decompresses the
image data to check its scanlines, enforces the 1,048,576-byte limit, and
writes the exact validated bytes to `/output/entry.png`. Missing, truncated,
corrupt, or oversized assets fail with a clear error and do not produce a new
output file.

## Regeneration

The original rendering source is `tools/render_entry.py`. Rendering needs
Pillow and the DejaVu fonts available in this environment; the runtime
installer does not.

```sh
python3 tools/render_entry.py --out assets/entry.png
python3 main.py
```

Rendering is deterministic: the random seed, layout, paper grain, and save
settings are fixed. The rendered PNG is written directly under `assets/`; no
duplicate preview or generated output image is kept in the repository.

## Tests

```sh
python3 -m unittest discover -s tests -v
```

The suite checks real PNG chunk structure and CRCs, exact 1024 x 1024 8-bit
RGB dimensions, decompressed scanline length, the size cap, the editorial
status and attribution copy, stdlib-only offline runtime imports, clear
failure on missing or corrupt assets, exact deterministic installation from
different working directories, regeneration of the shipped asset from
`tools/render_entry.py`, and the live README intake branding.

## Edition cutoff and limitations

This is an **early edition as of 03:45 UTC on 21 November 2026**
(11:45 Asia/Shanghai), not a final end-of-day digest. It records the following
limits, detailed in `SOURCES.md`:

- The Riyadh intercept count is attributed to the Saudi-led coalition. A
  Reuters witness saw a projectile and heard a bang; every intercept is not
  independently confirmed here.
- COP31 is shown in Saturday overtime. No final agreement is confirmed.
- The North Korea item is labelled as a state-media report about a Friday
  visit, first reported on Saturday. It is not presented as a Saturday
  inspection or as proof of a diplomatic rejection.
- The Iran–US item is a Saturday report that includes Friday remarks. No
  agreement is claimed.
- The Dragon splashdown is **scheduled**, not completed. It had not happened
  at the cutoff, so the image says "SCHEDULED / NOT YET CONFIRMED" and does not
  draw the capsule in the water.

The illustrations are symbolic editorial imagery, not photographs or portraits.
They intentionally avoid fabricated likenesses and do not add later events.

## Files

- `assets/entry.png` — shipped image
- `main.py` — dependency-free validated installer
- `tools/render_entry.py` — original deterministic Pillow renderer
- `tests/test_entry.py` — structural, runtime, regeneration, copy, and README intake tests
- `SOURCES.md` — source URLs, dates, and attribution caveats
- `.makefun/owner.json` — public entry-wallet ownership metadata
- `LICENSE` — MIT
