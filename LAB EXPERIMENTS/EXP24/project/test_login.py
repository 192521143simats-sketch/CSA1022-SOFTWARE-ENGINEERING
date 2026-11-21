import unittest
from login import login


class TestLogin(unittest.TestCase):
    def test_valid(self):
        self.assertTrue(login("admin", "admin123"))

    def test_wrong_password(self):
        self.assertFalse(login("admin", "bad"))

    def test_unknown_user(self):
        self.assertFalse(login("ghost", "x"))


if __name__ == "__main__":
    unittest.main()
