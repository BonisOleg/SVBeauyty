from django.test import SimpleTestCase

from apps.catalog.product_grid import pick_grid_columns


class PickGridColumnsTests(SimpleTestCase):
    def test_examples_from_skill(self):
        cases = {
            0: 2,
            1: 3,
            2: 3,
            5: 5,
            6: 3,
            7: 4,
            8: 4,
            9: 3,
            10: 5,
            11: 4,
            13: 5,
            14: 5,
        }
        for count, expected in cases.items():
            with self.subTest(count=count):
                self.assertEqual(pick_grid_columns(count), expected)

    def test_seven_centers_as_four_plus_three(self):
        self.assertEqual(pick_grid_columns(7), 4)
        self.assertEqual(7 % 4, 3)
