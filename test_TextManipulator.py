import unittest
from TextManipulator import TextManipulator

class TestTextManipulator(unittest.TestCase):
    def setUp(self):
        self.text_manipulator = TextManipulator()

    def test_manipulate_bold_text(self):
        input_text = "This is a test message with B(bold) text."
        expected_output = "This is a test message with \033[1mbold\033[0m text."
        result = self.text_manipulator.manipulate(input_text)
        self.assertEqual(result, expected_output, "Expected bold text manipulation")

    def test_manipulate_italic_text(self):
        input_text = "This is a test message with I(italic) text."
        expected_output = "This is a test message with \033[3mitalic\033[0m text."
        result = self.text_manipulator.manipulate(input_text)
        self.assertEqual(result, expected_output, "Expected italic text manipulation")



    def test_manipulate_red_text(self):
        input_text = "This is a test message with RED(red) text."
        expected_output = "This is a test message with \033[93mred\033[0m text."
        result = self.text_manipulator.manipulate(input_text)
        self.assertEqual(result, expected_output, "Expected red text manipulation")

    def test_manipulate_green_text(self):
        input_text = "This is a test message with GREEN(green) text."
        expected_output = "This is a test message with \033[92mgreen\033[0m text."
        result = self.text_manipulator.manipulate(input_text)
        self.assertEqual(result, expected_output, "Expected green text manipulation")

    def test_manipulate_blue_text(self):
        input_text = "This is a test message with BLUE(blue) text."
        expected_output = "This is a test message with \033[94mblue\033[0m text."
        result = self.text_manipulator.manipulate(input_text)
        self.assertEqual(result, expected_output, "Expected blue text manipulation")


if __name__ == '__main__':
    unittest.main()
