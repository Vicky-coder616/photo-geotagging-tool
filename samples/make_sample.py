"""Create a synthetic JPEG containing no personal photo data."""

from pathlib import Path
from PIL import Image

if __name__ == "__main__":
    destination = Path(__file__).parent / "generated" / "demo.jpg"
    destination.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (64, 64), "#336699").save(destination, "JPEG")
    print(destination)
