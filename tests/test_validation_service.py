import unittest

from services.validation_service import validate_file


class ValidationServiceTest(unittest.TestCase):
    def test_validate_file_rejects_unsupported_extension(self):
        with self.assertRaisesRegex(ValueError, "не поддерживается"):
            validate_file("script.exe", 12, 50)

    def test_validate_file_rejects_empty_file(self):
        with self.assertRaisesRegex(ValueError, "пустой"):
            validate_file("document.pdf", 0, 50)

    def test_validate_file_rejects_file_over_size_limit(self):
        with self.assertRaisesRegex(ValueError, "превышает 1 МБ"):
            validate_file("document.pdf", 2 * 1024 * 1024, 1)

    def test_validate_file_accepts_supported_file_under_limit(self):
        validate_file("document.PDF", 1024, 50)


if __name__ == "__main__":
    unittest.main()
