from datetime import datetime
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image
import piexif
from src.geotag import tag_jpeg, gps_dms


class ImageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source.jpg"
        self.destination = self.root / "output" / "tagged.jpg"
        Image.new("RGB", (16, 16), "blue").save(self.source, "JPEG")

    def test_round_trip_gps_time_pixels_and_source_preservation(self):
        original = self.source.read_bytes()
        stamp = datetime(2026, 1, 1, 9, 30)
        tag_jpeg(self.source, self.destination, -37.8, 144.9, stamp)
        metadata = piexif.load(str(self.destination))
        self.assertEqual(metadata["GPS"][piexif.GPSIFD.GPSLatitudeRef], b"S")
        self.assertEqual(metadata["GPS"][piexif.GPSIFD.GPSLongitudeRef], b"E")
        self.assertEqual(
            metadata["Exif"][piexif.ExifIFD.DateTimeOriginal], b"2026:01:01 09:30:00"
        )
        self.assertEqual(original, self.source.read_bytes())
        with Image.open(self.source) as before, Image.open(self.destination) as after:
            self.assertEqual(before.tobytes(), after.tobytes())

    def test_existing_output_and_input_are_protected(self):
        self.destination.parent.mkdir()
        self.destination.write_bytes(b"previous-output")
        with self.assertRaises(FileExistsError):
            tag_jpeg(self.source, self.destination, 0, 0)
        self.assertEqual(self.destination.read_bytes(), b"previous-output")
        with self.assertRaises(ValueError):
            tag_jpeg(self.source, self.source, 0, 0, overwrite=True)

    def test_failed_metadata_update_preserves_existing_output(self):
        self.destination.parent.mkdir()
        self.destination.write_bytes(b"previous-output")
        with patch(
            "src.geotag.piexif.insert", side_effect=ValueError("synthetic failure")
        ):
            with self.assertRaises(ValueError):
                tag_jpeg(self.source, self.destination, 0, 0, overwrite=True)
        self.assertEqual(self.destination.read_bytes(), b"previous-output")
        self.assertEqual(list(self.destination.parent.glob(".geotag-*")), [])

    def test_non_jpeg_and_invalid_coordinates(self):
        for lat, lon in ((91, 0), (0, 181), (float("nan"), 0)):
            with self.assertRaises(ValueError):
                tag_jpeg(self.source, self.destination, lat, lon)
        png = self.root / "image.png"
        Image.new("RGB", (4, 4), "blue").save(png)
        with self.assertRaises(ValueError):
            tag_jpeg(png, self.destination, 0, 0)

    def test_dms_carry_does_not_produce_sixty_seconds(self):
        dms = gps_dms(12.99999999999)
        self.assertLess(dms[2][0] / dms[2][1], 60)
