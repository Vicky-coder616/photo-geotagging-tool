# Photo Geotagging Tool

> **Portfolio reconstruction / demonstration.** This is a reference implementation based on a described project, not a verified copy of original production source or evidence of deployment.

## Problem and purpose

Batch JPEG GPS and timestamp metadata utility. This demo makes the workflow reproducible with synthetic data or mocked API responses and exposes the assumptions that need review before real use.

## Stack and flow

Python, Pillow, piexif.

JPEG validation -> temporary output copy -> EXIF GPS/time changes -> atomic destination creation.

`src/` contains processing code, `tests/` contains offline regression tests, `.github/workflows/checks.yml` runs offline checks on pushes and pull requests. Samples are synthetic; `output/` and runtime files are ignored.

## Setup and execution

Use Python 3.12 and an isolated virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.lock
python samples/make_sample.py
python -m src.geotag --input samples/generated --output output/geotagged --latitude -37.8 --longitude 144.9 --start-time 2026-01-01T09:00:00
```

`requirements.txt` records direct dependencies; `requirements.lock` pins the resolved runtime set. Offline transformations/tests do not require API credentials after installation. No API or email call is executed automatically.

## Implemented behavior and example output

Tests round-trip GPS and timestamp tags, compare decoded pixels, preserve source bytes and preserve previous output on failure. Existing output is refused unless --overwrite is explicitly supplied. Batch failures are reported per file, with a nonzero exit status. Use a new output folder for each demonstration.

## Tests

```powershell
python -m unittest discover -s tests -v
python -m compileall -q src tests
```

The suite uses synthetic files and mocked service responses. See the preparation validation report for actual results and environment limitations; a workflow file is not evidence of a completed GitHub Actions run.

## Limitations and future work

JPEG only; no HEIC/HEIF/PNG or recursive processing. Timestamp means local wall time without timezone conversion. Coordinates are operator-supplied. Atomic no-overwrite creation uses Windows rename or POSIX hard links and can fail safely on unsupported/network filesystems. Future work: approved format support and broader filesystem validation. Use synthetic photos for public examples.

## Data and publication

Do not commit real customer records, tokens, production identifiers, proprietary drawings, pricing data or personal photos. Keep `.env` local. Error messages from the adapter omit request URLs and credential values. Local file paths/messages can still reveal context; review logs before sharing.

This repository contains a reconstructed demonstration prepared for a public engineering portfolio. See `docs/PROVENANCE.md` for its origin and limits. No original employer/client implementation is included. No license is granted by this publication; third-party dependencies retain their own license terms.
