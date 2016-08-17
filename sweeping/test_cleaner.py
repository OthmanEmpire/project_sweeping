"""
Unit tests and integration tests for the data_sorting module.

__author__ = "Othman Alikhan"
__email__ = "sc14omsa@leeds.ac.uk"
__date__ = "2016-08-15"
"""
import filecmp
import os
import unittest
import mock
from sweeping.cleaner import Extractor


# A list of unit tests that need not to be ran
class TestExtractor(unittest.TestCase):
    """
    Unit tests for the Extractor class.
    """

    def setUp(self):
        """
        Constructs an Extractor instance before running any test.
        """
        self.extractor = Extractor(os.path.join("..", "test", "results_mock"))

    def testAddDatabaseEntry(self):
        """
        Tests whether an entry can be added to the database successfully
        and in the correct format.
        """
        entryData = \
        {
            "FR":       "50",
            "MULTI":     "1",
            "ASH":      "0.32",
            "AWA":      "-2.2",
            "N":        "100",
            "N_OUT":    "21",
            "EXIT":     "0.21",
            "DATE":     "13Aug",
            "PATH":     "12Aug_multi_100/exit_time_raw_output_1&-2.0&0.30.csv"
        }

        # Orders the entry data and formats it appropriately
        orderedEntry = []
        for order in self.extractor.dataOrder:
            orderedEntry.append(entryData[order])
        expectedEntry = self.extractor.databaseTemplate.format(*orderedEntry)

        # Mocking built in opening of file to isolate unit test
        m = mock.mock_open()
        with mock.patch("builtins.open", m, create=True):
            # Adds the database entry
            self.extractor.addDatabaseEntry(entryData)

            # Asserting whether written data matches expected
            handle = m()
            handle.write.assert_called_once_with(expectedEntry)

    def testExtractDataFromPath(self):
        """
        Tests whether the data extracted from the paths to the data files
        is parsed correctly from the paths themselves.
        """
        filePath1 = os.path.join("12Aug_m_50",
                                 "exit_time_raw_output_1&-2.2&0.32.csv")

        data1 = \
        {
            "FR":       "50",
            "MULTI":     "1",
            "AWA":      "-2.2",
            "ASH":      "0.32",
            "PATH":     filePath1,
            "DATE":     "12Aug"
        }
        dataExtracted1 = self.extractor.extractDataFromPath(filePath1)

        self.assertDictEqual(dataExtracted1, data1)

    def testExtractDataFromFile(self):
        """
        Tests whether data extracted from the contents of a data file is
        done correctly.
        """
        filePath = os.path.join("..", "test",
                                "exit_time_raw_output_0&-2.25&0.27.csv")
        data = \
        {
            "N":        "100",
            "N_OUT":    "13",
            "EXIT":     "0.13",
            "PATH":     filePath
        }

        dataExtracted = self.extractor.extractDataFromFile(filePath)
        self.assertDictEqual(dataExtracted, data)

    def testListAllFilePaths(self):
        """
        Tests whether all data file paths from the results folder are listed
        as expected.
        """
        allPathsFile = os.path.join("..", "test", "folder_structure",
                                    "results_mock_path_list.txt")

        # Reads all the pre-processed data paths from a file and formats
        # the paths appropriately to allow easy comparing down the line
        expectedPaths = []
        with open(allPathsFile, "r") as file:
            for path in file:
                path = path.strip().split("/")
                path = os.path.join(*path)
                expectedPaths.append(path)

        # Attempts to processes the data paths (requires I/O reading)
        paths = self.extractor.listAllFilePaths()

        # Sorting otherwise ordering of elements which isn't
        # significant causes the test to fail
        expectedPaths = sorted(expectedPaths)
        paths = sorted(paths)

        # Compares element by element basis
        for i, _ in enumerate(paths):
            self.assertEqual(paths[i], expectedPaths[i])


# A list of integration tests that need not to be ran
class TestIntegrationExtractor(unittest.TestCase):

    def testPopulateSmallerDatabase(self):
        """
        Tests whether the smaller database is populated properly.
        """
        resultsPath = os.path.join("..", "test", "folder_structure",
                                   "results_smaller")
        databasePath = os.path.join("..", "test", "database",
                                    "database_smaller_output.txt")
        expectedPath = os.path.join("..", "test", "database",
                                    "database_smaller.txt")

        # Populates the database after changing paths
        extractor = Extractor(resultsPath)
        extractor.databasePath = databasePath
        extractor.populateDatabase()

        # Checks whether expected and produced files match
        self.assertTrue(filecmp.cmp(databasePath, expectedPath, shallow=False))

    def testPopulateSampleDatabase(self):
        """
        Tests whether the sample database can be populated properly.
        """
        resultsPath = os.path.join("..", "test", "folder_structure",
                                   "results_sample")
        databasePath = os.path.join("..", "test", "database"
                                    "database_sample_output.txt")
        expectedPath = os.path.join("..", "test", "database"
                                    "database_sample_netta.txt")

        # Populates the database after changing paths
        extractor = Extractor(resultsPath)
        extractor.databasePath = databasePath
        extractor.populateDatabase()

        # Checks whether expected and produced files match
        self.assertTrue(filecmp.cmp(databasePath, expectedPath, shallow=False))


if __name__ == '__main__':
    unittest.main()
