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
        settingsPath = os.path.join("..", "test", "settings", "unittests.ini")
        self.janitor = Janitor(settingsPath)

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
        for order in self.janitor.dataOrder:
            orderedEntry.append(entryData[order])
        expectedEntry = self.janitor.databaseTemplate.format(*orderedEntry)

        # Mocking built in opening of file to isolate unit test
        m = mock.mock_open()
        with mock.patch("builtins.open", m, create=True):
            # Adds the database entry
            self.janitor.putDatabaseEntry(entryData)

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
        dataExtracted1 = self.janitor.pickDataFromPath(filePath1)

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

        dataExtracted = self.janitor.pickDataFromFile(filePath)
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
        databasePaths = []
        with open(allPathsFile, "r") as file:
            for path in file:
                path = path.strip().split("/")
                path = os.path.join(*path)
                databasePaths.append(path)

        # Attempts to processes the data paths (requires I/O reading)
        paths = self.janitor.inventoryAllFilePaths()

        # Sorting otherwise ordering of elements which isn't
        # significant causes the test to fail
        databasePaths = sorted(databasePaths)
        paths = sorted(paths)

        # Compares element by element basis
        for i, _ in enumerate(paths):
            self.assertEqual(paths[i], databasePaths[i])


# A list of integration tests that need not to be ran
class TestIntegrationExtractor(unittest.TestCase):

    def setUp(self):
        """
        Runs this method before every test which initializes some variables.
        """
        self.testDir = os.path.join("..", "test")

    def testPrepareSettings(self):
        """
        Tests whether the .ini file can be correctly parsed.
        """
        settingsPath = os.path.join(self.testDir, "settings", "mock_subset.ini")
        janitor = Janitor(settingsPath)

        sections = ["QUERY", "QUERY_SETTINGS", "PATHS"]
        self.assertListEqual(janitor.config.sections(), sections)
        self.assertEqual(janitor.config["PATHS"]["results_dir"],
                         "../test/results/mock_subset")

    def testPopulateMockSubsetDatabase(self):
        """
        Tests whether the subset of the mock database can populate properly.
        """
        settingsPath = os.path.join(self.testDir, "settings", "mock_subset.ini")
        expectedDatabasePath = os.path.join(self.testDir,
                                            "database", "mock_subset.txt")
        self._assertPopulateDatabase(settingsPath, expectedDatabasePath)

    def testPopulateSampleSubsetDatabase(self):
        """
        Tests whether the subset of the sample database can populate properly.
        """
        settingsPath = os.path.join(self.testDir, "settings",
                                    "sample_subset.ini")
        expectedDatabasePath = os.path.join(self.testDir,
                                            "database", "sample_subset.txt")
        self._assertPopulateDatabase(settingsPath, expectedDatabasePath)

    def testPopulateSampleProcessedDatabase(self):
        """
        Tests whether the sample database can populate properly.
        """
        settingsPath = os.path.join(self.testDir, "settings",
                                    "sample_processed.ini")
        expectedDatabasePath = os.path.join(self.testDir,
                                            "database", "sample_processed.txt")
        self._assertPopulateDatabase(settingsPath, expectedDatabasePath)

    def _assertPopulateDatabase(self, settingsPath, expectedDatabasePath):
        """
        Populates the database and then proceeds to assert whether the output
        matches the expected results.

        :param settingsPath: The path to the settings .ini file.
        :param expectedDatabasePath: The path to the expected database.
        """
        # Populates the database
        janitor = Janitor(settingsPath)
        janitor.populateDatabase()

        # Checks whether expected and produced files match
        self.assertTrue(filecmp.cmp(janitor.config["PATHS"]["database_file"],
                                    expectedDatabasePath,
                                    shallow=False))


# A helper class (used for debugging file comparing assertions)
class Debugger(unittest.TestCase):
    """
    A simple class designed to help debug some common problems.
    """

    def debugFileComparing(self, filePath1, filePath2):
        """
        Asserts that the two files are equal line by line.

        Use this function to help debug when file comparing tests fail.

        :param filePath1: Path to the first file to be compared.
        :param filePath2: Path to the second file to be compared.
        """

        with open(filePath1, "r") as f1, open(filePath2, "r") as f2:
            contents1 = f1.readlines()
            contents2 = f2.readlines()

        if len(contents1) != len(contents2):
            print("The amount of lines in both files don't match!")

        for i, _ in enumerate(contents1):
            self.assertEqual(contents1[i], contents2[i])


def cleanDatabaseDir():
    """
    Removes all output and log files generated in the database directory.
    """
    deleteFilesContaining = ["log", "output"]
    databaseDir = os.path.join("..", "test", "database")

    # Lists all the files in the database directory then loops over
    # all the files and removes any that match a key word in the filter
    for root, _, files in os.walk(databaseDir):
        for file in files:
            for filter in deleteFilesContaining:
                if filter in file:
                    os.remove(os.path.join(root, file))
                    break


if __name__ == '__main__':
    #unittest.main()
    cleanDatabaseDir()
