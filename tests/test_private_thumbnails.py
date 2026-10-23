"""Private previews stay in memory and respect image orientation."""
import sys
import tempfile
import unittest
from io import BytesIO
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from video_thumbnails import private_preview


class PrivateThumbnailTests(unittest.TestCase):
    def test_transparency_and_no_disk_cache(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'portrait.png'
            Image.new('RGBA', (800, 1200), (30, 100, 140, 128)).save(path)
            preview = Image.open(BytesIO(private_preview(path)))
            self.assertEqual(preview.size, (213, 320))
            self.assertEqual(preview.mode, 'RGB')
            self.assertEqual(set(Path(directory).iterdir()), {path})

    def test_camera_orientation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'rotated.jpg'
            image = Image.new('RGB', (800, 400))
            exif = Image.Exif()
            exif[274] = 6
            image.save(path, exif=exif)
            preview = Image.open(BytesIO(private_preview(path)))
            self.assertEqual(preview.size, (160, 320))


if __name__ == '__main__':
    unittest.main()
