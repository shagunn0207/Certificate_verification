import unittest
from src.utils import normalize_institution, is_internal_program
from src.data_loader import DataLoader

class TestMatchingUtilities(unittest.TestCase):
    def setUp(self):
        self.data_loader = DataLoader()

    def test_institution_normalization(self):
        # MSRIT -> Ramaiah Institute of Technology
        self.assertEqual(normalize_institution("MSRIT"), "Ramaiah Institute of Technology")
        self.assertEqual(normalize_institution("RIT"), "Ramaiah Institute of Technology")
        self.assertEqual(normalize_institution("MSRIT Bangalore"), "Ramaiah Institute of Technology")
        self.assertEqual(normalize_institution("M.S. Ramaiah Institute of Technology"), "Ramaiah Institute of Technology")
        
        # Genuine other institutions must NOT be merged
        self.assertNotEqual(normalize_institution("Ramaiah University of Applied Sciences"), "Ramaiah Institute of Technology")
        self.assertEqual(normalize_institution("NIT Patna"), "NIT Patna")

    def test_internal_external_classification(self):
        # Internal refers to FDP institution, NOT faculty member
        self.assertTrue(is_internal_program("Ramaiah Institute of Technology"))
        self.assertTrue(is_internal_program("MSRIT"))
        self.assertTrue(is_internal_program("RIT"))
        self.assertFalse(is_internal_program("NIT Patna"))
        self.assertFalse(is_internal_program("BITS Pilani"))
        self.assertFalse(is_internal_program("Ramaiah University of Applied Sciences"))

    def test_faculty_id_matching(self):
        # Preferred matching key is Faculty ID
        res = self.data_loader.find_faculty(faculty_id="F012")
        self.assertIsNotNone(res)
        self.assertEqual(res[0], "F012")
        self.assertEqual(res[1], "Dr. Sushma B")

    def test_faculty_name_matching(self):
        # Case insensitive and honorific handling
        res = self.data_loader.find_faculty(faculty_name="Sushma B")
        self.assertIsNotNone(res)
        self.assertEqual(res[0], "F012")

        res2 = self.data_loader.find_faculty(faculty_name="Dr. Mallegowda M.")
        self.assertIsNotNone(res2)
        self.assertEqual(res2[0], "F015")

    def test_wrong_faculty_matching(self):
        # Non-existent faculty must return None
        res = self.data_loader.find_faculty(faculty_id="F999", faculty_name="NonExistent Professor XYZ")
        self.assertIsNone(res)

if __name__ == "__main__":
    unittest.main()
