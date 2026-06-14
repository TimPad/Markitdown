import base64
import unittest
from io import BytesIO

from PIL import Image

from services.nebius_ocr_service import NebiusOCRService


class NebiusOCRServiceTest(unittest.TestCase):
    def test_image_to_data_url_returns_jpeg_data_url(self):
        image = Image.new("RGB", (10, 10), color="white")

        data_url = NebiusOCRService.image_to_data_url(image)

        self.assertTrue(data_url.startswith("data:image/jpeg;base64,"))
        payload = data_url.split(",", 1)[1]
        decoded = base64.b64decode(payload)
        # JPEG начинается с маркера 0xFFD8.
        self.assertEqual(decoded[:2], b"\xff\xd8")
        # Декодируется обратно в изображение.
        Image.open(BytesIO(decoded)).verify()


if __name__ == "__main__":
    unittest.main()
