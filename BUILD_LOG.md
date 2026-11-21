# Build record — news-image-20261121

All times below are Asia/Shanghai (UTC+8) unless a source carries its own zone.

## Bounty rechecked

- Rechecked at 2026-11-21 10:57 Asia/Shanghai from
  https://make.fun/api/competitions/news-image-20261121 and
  https://make.fun/api/competitions/news-image-20261121/requirements
- Status: open, acceptingSubmissions=true, entry fee none
- Entries close: 2026-11-23 08:00 Asia/Shanghai
- At that recheck, submissionCount was 1147
- Official gate: program writes /output/entry.png with no network; two runs
  must be identical bytes; whole PNG or JPEG, at most 1 MiB and 1024×1024
- Transcripts are required to submit. This file is a build note, not a kit
  transcript bundle.

## What was built

- Original typographic poster, drawn in Python (Pillow) from Liberation fonts
  and simple geometry only. No image-generation API, no third-party photos.
- Fixed bitmap: assets/entry.png (copied to preview/entry.png)
  1024×1024 PNG, 160263 bytes, SHA-256
  f4a30f5885de631de38edb6f970b3201648e95ee2c59bb885f1152ced03ec6de
- main.py copies that file to /output/entry.png and does nothing else
- LICENSE is the MIT license
- Renderer run twice at 2026-11-21 11:01 Asia/Shanghai; both runs wrote the
  same SHA-256. Two independent copies of the asset also matched.
- This machine cannot create /output (permission denied). The official
  entrypoint path is unchanged. Verification therefore compared two copies
  of the baked asset, which is the only data main.py would write.

## What was not done

- No git init, clone, checkout, commit, or push
- No bounty submission, transcript upload, payment, signing, new wallet or
  key, claim, or public comment

## Isolated /output runs (2026-11-21 11:14 Asia/Shanghai)

The host cannot create `/output` (permission denied at the filesystem root). The official
entrypoint was still run for real, twice, with bubblewrap (`bwrap`): a temporary directory
was mounted at `/output` inside the sandbox, and `python3 main.py` wrote
`/output/entry.png` there. This is not privilege escalation; it only relocates that
path. Both runs and the baked asset were identical:

- format: PNG, 1024×1024, 160263 bytes
- SHA-256: f4a30f5885de631de38edb6f970b3201648e95ee2c59bb885f1152ced03ec6de

On the make.fun grader, `/output` is expected to be writable, so `main.py` can write
`/output/entry.png` directly.
