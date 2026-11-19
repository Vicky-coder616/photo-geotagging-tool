"""Batch JPEG EXIF updates with atomic writes and explicit overwrite policy."""

import argparse
from datetime import datetime, timedelta
from fractions import Fraction
import math
import os
from pathlib import Path
import shutil
import tempfile

import piexif
from PIL import Image


def gps_dms(decimal):
    if not math.isfinite(decimal):
        raise ValueError("Coordinate must be finite")
    # Round once in integer microseconds to keep seconds below 60.
    units = round(abs(decimal) * 3600 * 1000000)
    degrees, units = divmod(units, 3600 * 1000000)
    minutes, seconds = divmod(units, 60 * 1000000)
    fraction = Fraction(seconds, 1000000)
    return ((degrees, 1), (minutes, 1), (fraction.numerator, fraction.denominator))


def tag_jpeg(source, destination, latitude, longitude, when=None, overwrite=False):
    source, destination = Path(source), Path(destination)
    if (
        not math.isfinite(latitude)
        or not math.isfinite(longitude)
        or not -90 <= latitude <= 90
        or not -180 <= longitude <= 180
    ):
        raise ValueError("Invalid GPS coordinates")
    if source.resolve() == destination.resolve():
        raise ValueError("Input and output must be different")
    if destination.is_symlink():
        raise ValueError("Output must not be a symbolic link")
    if when is not None and when.tzinfo is not None:
        raise ValueError("EXIF timestamp must be local wall time without timezone")
    if destination.exists() and not overwrite:
        raise FileExistsError("Output exists; use --overwrite deliberately")
    with Image.open(source) as image:
        if image.format != "JPEG":
            raise ValueError("Only JPEG input is supported")
        image.verify()
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix=".geotag-", suffix=".jpg", dir=destination.parent
    )
    os.close(descriptor)
    temporary = Path(temporary)
    try:
        shutil.copy2(source, temporary)
        exif = piexif.load(str(temporary))
        exif["GPS"][piexif.GPSIFD.GPSLatitudeRef] = b"N" if latitude >= 0 else b"S"
        exif["GPS"][piexif.GPSIFD.GPSLatitude] = gps_dms(latitude)
        exif["GPS"][piexif.GPSIFD.GPSLongitudeRef] = b"E" if longitude >= 0 else b"W"
        exif["GPS"][piexif.GPSIFD.GPSLongitude] = gps_dms(longitude)
        if when:
            stamp = when.strftime("%Y:%m:%d %H:%M:%S").encode("ascii")
            exif["Exif"][piexif.ExifIFD.DateTimeOriginal] = stamp
            exif["Exif"][piexif.ExifIFD.DateTimeDigitized] = stamp
        piexif.insert(piexif.dump(exif), str(temporary))
        if overwrite:
            os.replace(temporary, destination)
        else:
            # Atomic create: a competing writer cannot be overwritten silently.
            if os.name == "nt":
                # Windows rename refuses an existing target, without hard links.
                os.rename(temporary, destination)
            else:
                os.link(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--latitude", type=float, required=True)
    parser.add_argument("--longitude", type=float, required=True)
    parser.add_argument("--start-time", type=datetime.fromisoformat)
    parser.add_argument("--interval-seconds", type=int, default=60)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    if args.input.resolve() == args.output.resolve() or not args.input.is_dir():
        parser.error("Input directory must exist and differ from output")
    if args.interval_seconds < 0:
        parser.error("Interval cannot be negative")
    if (
        not math.isfinite(args.latitude)
        or not math.isfinite(args.longitude)
        or not -90 <= args.latitude <= 90
        or not -180 <= args.longitude <= 180
    ):
        parser.error("Invalid GPS coordinates")
    if args.start_time and args.start_time.tzinfo:
        parser.error("Use a local timestamp without timezone for EXIF")
    files = sorted(
        p
        for p in args.input.iterdir()
        if p.is_file() and p.suffix.lower() in (".jpg", ".jpeg")
    )
    if not files:
        parser.error("No JPEG files found")
    failures = 0
    for index, source in enumerate(files):
        try:
            when = (
                args.start_time + timedelta(seconds=index * args.interval_seconds)
                if args.start_time
                else None
            )
            tag_jpeg(
                source,
                args.output / source.name,
                args.latitude,
                args.longitude,
                when,
                args.overwrite,
            )
        except (
            OSError,
            ValueError,
            OverflowError,
            piexif.InvalidImageDataError,
        ) as exc:
            failures += 1
            print(f"{source.name}: failed ({type(exc).__name__})")
    print(
        f"Geotagged {len(files) - failures}/{len(files)} JPEG images; failures: {failures}"
    )
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
