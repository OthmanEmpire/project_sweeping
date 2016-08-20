"""
Unit tests and integration tests for the cleaner module.

__author__ = "Othman Alikhan"
__email__ = "sc14omsa@leeds.ac.uk"
__date__ = "2016-08-15"
"""
import filecmp
import os
import unittest
import mock
from sweeping.cleaner import Extractor, Database, Controller


################################# UNIT TESTS ###################################


class TestExtractor(unittest.TestCase):
    """
    Unit tests for the Extractor class.
    """

    def setUp(self):
        """
        Constructs an Extractor instance before running any test.
        """
        self.dataPath = os.path.join("..", "test", "results", "type_a")
        self.extractor = Extractor()

    @mock.patch("sweeping.cleaner.print", create=True)
    @mock.patch("sweeping.cleaner.Extractor.listAllFilePaths")
    @mock.patch("sweeping.cleaner.Extractor.extractDataFromPath")
    @mock.patch("sweeping.cleaner.Extractor.extractDataFromFile")
    def testExtractAllData(self, mockfileExtract, mockPathExtract,
                           mockList, mockPrint):
        """
        Tests whether all required data can be extracted properly.
        """
        error1 = 'WARNING: Could not find a extract a shred of data! ' \
                 'Perhaps the results directory is incorrectly specified?'
        error2 = 'WARNING: Some files weren\'t parsed properly, check' \
                 'error logs for more details!'

        # Covers the case when no data could be extracted
        self.extractor.extractAllData(self.dataPath, "baz")
        mockPrint.assert_called_once_with(error1)

        # Covers the case when some data could be extracted
        mockPrint.reset_mock()
        mockList.return_value = ["baz"]
        mockPathExtract.side_effect = ValueError()
        mockOpen = mock.mock_open()
        with mock.patch("builtins.open", mockOpen, create=True):
            self.extractor.extractAllData("foo", "bar")
            mockPrint.assert_called_once_with(error2)
            mockOpen.assert_has_calls([mock.call("bar", "a")])

        # Covers the case when all data could be extracted
        mockPrint.reset_mock()
        mockList.return_value = ["baz"]
        mockPathExtract.side_effect = None
        mockPathExtract.return_value = {"FR": "50"}
        mockfileExtract.return_value = {"N": "100"}
        data = self.extractor.extractAllData("foo", "bar")[0]
        self.assertDictEqual(data, {"FR": "50", "N": "100"})

    def testExtractDataFromPath(self):
        """
        Tests whether the data extracted from the paths to the data files
        is parsed correctly from the paths themselves.
        """
        filePath = os.path.join("12Aug_m_50",
                                "exit_time_raw_output_1&-2.2&0.32.csv")
        data = \
        {
            "FR":       "50",
            "MULTI":     "1",
            "AWA":      "-2.2",
            "ASH":      "0.32",
            "PATH":     filePath,
            "DATE":     "12Aug"
        }

        dataExtracted = self.extractor.extractDataFromPath(filePath)
        self.assertDictEqual(dataExtracted, data)

    def testExtractDataFromFile(self):
        """
        Tests whether data extracted from the contents of a data file is
        done correctly.
        """
        filePath = os.path.join("..", "test", "results",
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
        allPathsFile = os.path.join("..", "test", "results",
                                    "type_a_path_list.txt")

        # Reads all the pre-processed data paths from a file and formats
        # the paths appropriately to allow easy comparing down the line
        databasePaths = []
        with open(allPathsFile, "r") as file:
            for path in file:
                path = path.strip().split("/")
                path = os.path.join(*path)
                databasePaths.append(path)

        # Attempts to processes the data paths (requires I/O reading)
        paths = self.extractor.listAllFilePaths(self.dataPath)

        # Sorting otherwise ordering of elements which isn't
        # significant causes the test to fail
        databasePaths = sorted(databasePaths)
        paths = sorted(paths)

        # Compares element by element basis
        for i, _ in enumerate(paths):
            self.assertEqual(paths[i], databasePaths[i])

    @mock.patch("os.path")
    @mock.patch("os.remove")
    def testInitializeLogFile(self, mockRemove, mockPath):
        """
        Tests whether the log file can be initialized properly.
        """
        mockLogPath = "baz"
        mockPath.exists.return_value = True

        self.extractor.initializeLogFile(mockLogPath)
        mockRemove.assert_called_once_with(mockLogPath)


class TestDatabase(unittest.TestCase):
    """
    Unit tests for the Database class.
    """

    def setUp(self):
        """
        Constructs an Database instance before running any test.
        """
        self.database = Database()

    def testInitializeDataFile(self):
        """
        Tests whether the data file can be initialized properly.
        """
        # Mocking built in opening of file to isolate unit test
        mockOpen = mock.mock_open()
        with mock.patch("builtins.open", mockOpen, create=True):
            database = Database()
            database.initializeDataFile("bar")

            # Asserts whether the header was written into the database file
            header = database.databaseTemplate.format(*database.dataOrder)
            mockOpen().write.assert_called_once_with(header)

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
        orderedEntry = [entryData[order] for order in self.database.dataOrder]
        expectedEntry = self.database.databaseTemplate.format(*orderedEntry)

        # Mocking built in opening of file to isolate unit test
        mockOpen = mock.mock_open()
        with mock.patch("builtins.open", mockOpen, create=True):
            self.database.addEntry("foo", entryData)

            # Asserts whether written data matches expected
            mockOpen().write.assert_called_once_with(expectedEntry)

    @mock.patch("csv.reader")
    def testQueryDatabase(self, mockReader):
        """
        Tests whether the database can be queried properly.
        """
        query = \
        {
            "FR":       "100",
            "ASH":      "0.30",
            "AWA":      "-0.55",
            "MULTI":    "1",
        }

        entry = \
        {
            "N":        "100",
            "N_OUT":    "0",
            "EXIT":     "0.0",
            "DATE":     "16Aug",
            "PATH":     "../test/results/type_a_subset/16Aug_m_100/"
                        "exit_time_raw_output_1&-0.55&0.3.csv"
        }
        entry.update(query)     # Merges with queries dictionary

        mockReader.return_value = iter([entry.keys(), entry.values()])

        # Mocking built in opening of file to isolate unit test
        mockOpen = mock.mock_open()
        with mock.patch("builtins.open", mockOpen, create=True):
            database = Database()
            match = database.query("foo", query)[0]
            self.assertDictEqual(match, entry)

    @mock.patch("os.path")
    @mock.patch("os.remove")
    def testPopulateDatabase(self, mockRemove, mockPath):
        """
        Tests whether the database can be populated properly.
        """
        entry = \
        {

            "FR":       "100",
            "ASH":      "0.30",
            "AWA":      "-0.55",
            "MULTI":    "1",
            "N":        "100",
            "N_OUT":    "0",
            "EXIT":     "0.0",
            "DATE":     "16Aug",
            "PATH":     "../test/results/type_a_subset/16Aug_m_100/"
                        "exit_time_raw_output_1&-0.55&0.3.csv"
        }
        entry1 = entry.copy()
        entry1["FR"] = "50"
        entry2 = entry.copy()
        entry2["FR"] = "40"
        entry3 = entry.copy()
        entry3["FR"] = "30"
        entries = [entry1, entry2, entry3]

        # Mocking built in opening of file to isolate unit test
        mockOpen = mock.mock_open()
        with mock.patch("builtins.open", mockOpen, create=True):
            database = Database()
            database.generate("foo", entries)

            # Check whether header was written
            header = database.databaseTemplate.format(*database.dataOrder)
            mockOpen().write.assert_any_call(header)

            # Check whether entries were written
            for entry in entries:
                orderedEntry = [entry[order] for order in database.dataOrder]
                orderedEntry = database.databaseTemplate.format(*orderedEntry)
                mockOpen().write.assert_any_call(orderedEntry)


############################# INTEGRATION TESTS ################################


class TestIntegration(unittest.TestCase):

    def setUp(self):
        """
        Runs this method before every test which initializes some variables.
        """
        self.databaseDir = os.path.join("..", "test", "database")
        self.resultsDir = os.path.join("..", "test", "results")
        settingsPath = os.path.join(".", "settings.ini")

        self.controller = Controller(settingsPath)

    def testReadIniFile(self):
        """
        Tests whether the .ini file can be correctly parsed.
        """
        self.assertListEqual(self.controller.config.sections(), ["PATHS"])

    def testGenerateDatabaseTypeA(self):
        """
        Tests whether the type_a database can populate properly.
        """
        expectedDatabase = os.path.join(self.databaseDir, "type_a.txt")
        producedDatabase = os.path.join(self.databaseDir, "type_a_output.txt")
        log = os.path.join(self.databaseDir, "type_a_error_log.txt")
        results = os.path.join(self.resultsDir, "type_a")

        self.controller.config["PATHS"]["results_dir"] = results
        self.controller.config["PATHS"]["database_file"] = producedDatabase
        self.controller.config["PATHS"]["database_log_file"] = log
        self.controller.run()

        self.assertTrue(filecmp.cmp(producedDatabase, expectedDatabase,
                                    shallow=False))

    def testQueryDatabaseTypeA(self):
        """
        Tests whether the database entries can be queried and fetched correctly.
        """
        database = os.path.join(self.databaseDir, "mock.txt")
        self.controller.config["PATHS"]["database_file"] = database

        matches = self.controller.database.query(database, {"FR": 100, "AWA": -1.7})

        self.assertTrue(len(matches) == 5)

    def testTidyDatabase(self):
        """
        Tests whether irrelevant entries in the database can be removed.
        """
        readDatabase = os.path.join(self.databaseDir, "mock")
        expectedDatabase = os.path.join(self.databaseDir, "mock_tidy.txt")
        producedDatabase = os.path.join(self.databaseDir, "mock_tidy_output.txt")
        log = os.path.join(self.databaseDir, "mock_tidy_error_log.txt")

        self.controller.config["PATHS"]["database_file"] = producedDatabase
        self.controller.config["PATHS"]["database_log_file"] = log
        self.controller.database.tidy(readDatabase)

        self.assertTrue(filecmp.cmp(producedDatabase, expectedDatabase,
                                    shallow=False))


################################# DEBUGGING ####################################


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
    unittest.main()
    #cleanDatabaseDir()
