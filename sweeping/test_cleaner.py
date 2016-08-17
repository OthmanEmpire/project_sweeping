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
from sweeping.cleaner import Janitor


# A list of unit tests that need not to be ran
class TestExtractor(unittest.TestCase):
    """
    Unit tests for the Extractor class.
    """

    def setUp(self):
        """
        Constructs an Extractor instance before running any test.
        """
        self.extractor = Janitor(os.path.join("..", "test", "mock"))

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
            self.extractor.putDatabaseEntry(entryData)

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
        dataExtracted1 = self.extractor.pickDataFromPath(filePath1)

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

        dataExtracted = self.extractor.pickDataFromFile(filePath)
        self.assertDictEqual(dataExtracted, data)

    def testListAllFilePaths(self):
        """
        Tests whether all data file paths from the results folder are listed
        as expected.
        """
        allPathsFile = os.path.join("..", "test", "results",
                                    "mock_path_list.txt")

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

    def setUp(self):
        """
        Runs this method before every integration test which initializes some
        variables.
        """
        self.testPath = os.path.join("..", "test")

    def testPopulateMockSubsetDatabase(self):
        """
        Tests whether the smaller database is populated properly.
        """
        resultsPath = os.path.join(self.testPath,
                                   "results", "mock_subset")
        databasePath = os.path.join(self.testPath,
                                    "database", "mock_subset_output.txt")
        expectedPath = os.path.join(self.testPath,
                                    "database", "mock_subset.txt")

        # Populates the database after changing paths
        extractor = Janitor(resultsPath)
        extractor.databasePath = databasePath
        extractor.populateDatabase()

        # Checks whether expected and produced files match
        self.assertTrue(filecmp.cmp(databasePath, expectedPath, shallow=False))

    def testPopulateSampleDatabase(self):
        """
        Tests whether the sample database can be populated properly.
        """
        resultsPath = os.path.join(self.testPath,
                                   "results", "sample_subset")
        databasePath = os.path.join(self.testPath,
                                    "database", "sample_subset_output.txt")
        expectedPath = os.path.join(self.testPath,
                                    "database", "sample_subset.txt")

        # Populates the database after changing paths
        extractor = Janitor(resultsPath)
        extractor.databasePath = databasePath
        extractor.populateDatabase()

        # Checks whether expected and produced files match
        self.assertTrue(filecmp.cmp(databasePath, expectedPath, shallow=False))


# A helper class (used for debugging file comparing assertions)
class Debugger(unittest.TestCase):
    """
    A simple class designed to help debug some common problems.
    """

    def debugFileComparing(self, file1, file2):
        """
        Asserts that the two files are equal line by line.

        Use this function to help debug when file comparing tests fail.

        :param file1: Path to the first file to be compared.
        :param file2: Path to the second file to be compared.
        """

        with open(file1, "r") as f1, open(file2, "r") as f2:
            contents1 = f1.readlines()
            contents2 = f2.readlines()

        if len(contents1) != len(contents2):
            print("The amount of lines in both files don't match!")

        for i, _ in enumerate(contents1):
            self.assertEqual(contents1[i], contents2[i])


if __name__ == '__main__':
    unittest.main()
