import unittest
from src.geotag import gps_dms


class GPSTests(unittest.TestCase):
    def test_whole_degrees(self):
        self.assertEqual(gps_dms(-37.0), ((37, 1), (0, 1), (0, 1)))


if __name__ == "__main__":
    unittest.main()
