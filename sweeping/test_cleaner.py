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
        self.dataPath = os.path.join("..", "test", "results", "type_a")
        self.extractor = Extractor()

    @mock.patch("sweeping.cleaner.print", create=True)
    @mock.patch("sweeping.cleaner.Extractor._listAllFilePaths")
    @mock.patch("sweeping.cleaner.Extractor._extractDataFromPath")
    @mock.patch("sweeping.cleaner.Extractor._extractDataFromFile")
    def testExtractAllData(self, mockfileExtract, mockPathExtract,
                           mockList, mockPrint):
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

    def test_ExtractDataFromPath(self):
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

        dataExtracted = self.extractor._extractDataFromPath(filePath)
        self.assertDictEqual(dataExtracted, data)

    def test_ExtractDataFromFile(self):
        filePath = os.path.join("..", "test", "results",
                                "exit_time_raw_output_0&-2.25&0.27.csv")
        data = \
        {
            "N":        "100",
            "N_OUT":    "13",
            "EXIT":     "0.13",
            "PATH":     filePath
        }

        dataExtracted = self.extractor._extractDataFromFile(filePath)
        self.assertDictEqual(dataExtracted, data)

    def test_ListAllFilePaths(self):
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
        paths = self.extractor._listAllFilePaths(self.dataPath)

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
        mockLogPath = "baz"
        mockPath.exists.return_value = True

        self.extractor._initializeLogFile(mockLogPath)
        mockRemove.assert_called_once_with(mockLogPath)


class TestDatabase(unittest.TestCase):
    """
    Unit tests for the Database class.
    """

    def setUp(self):
        self.database = Database()

        self.header = ["FR", "ASH", "AWA", "N", "N_OUT",
                       "EXIT", "MULTI", "DATE", "PATH"]

        self.entryData1 = ["50", "0.30", "-0.55", "110", "0", "0", "0.0",
                           "16Aug", "../test/results/type_a_subset/16Aug_m_100/"
                           "exit_time_raw_output_1&-0.55&0.3.csv"]
        self.entryData2 = ["100", "-0.30", "-0.55", "0", "0", "0", "0.0",
                           "16Aug", "../test/results/type_a_subset/16Aug_m_100/"
                           "exit_time_raw_output_1&-0.55&0.3.csv"]
        self.entryData3 = ["20", "0.60", "-0.55", "130", "0", "0", "0.0",
                           "16Aug", "../test/results/type_a_subset/16Aug_m_100/"
                           "exit_time_raw_output_1&-0.55&0.3.csv"]

        self.entry1 = dict(zip(self.header, self.entryData1))
        self.entry2 = dict(zip(self.header, self.entryData2))
        self.entry3 = dict(zip(self.header, self.entryData3))

    @mock.patch("csv.reader")
    def testRead(self, mockReader):
        mockReader.return_value = iter([self.header, self.entryData1])

        mockOpen = mock.mock_open()
        with mock.patch("builtins.open", mockOpen, create=True):
            database = self.database.read("foo")

            self.assertDictEqual(database[0], self.entry1)

    @mock.patch("os.path")
    @mock.patch("os.remove")
    def testCreate(self, mockRemove, mockPath):
        entries = [self.entry1, self.entry2, self.entry3]

        mockOpen = mock.mock_open()
        with mock.patch("builtins.open", mockOpen, create=True):
            self.database.create("foo", entries)

            # Check whether header was written
            header = self.database.template.format(*self.database.dataOrder)
            mockOpen().write.assert_any_call(header)

            # Check whether entries were written
            for entry in entries:
                orderedEntry = [entry[order] for order in self.database.dataOrder]
                orderedEntry = self.database.template.format(*orderedEntry)
                mockOpen().write.assert_any_call(orderedEntry)

    def testQuery(self):
        query = \
        {
            "FR":       "50",
            "ASH":      "0.30",
            "AWA":      "-0.55",
            "MULTI":    "0.0",
        }
        database = [self.entry1]
        matches = self.database.query(database, query)

        self.assertDictEqual(matches[0], self.entry1)

    def testSort(self):
        entry4 = self.entry3.copy()
        entry4["ASH"] = "0.40"
        database = [self.entry1, self.entry2, self.entry3,
                    entry4, entry4, entry4, self.entry2]
        sortedEntries = self.database.sort(database)

        self._assertSorted(iter(sortedEntries))

    def testSanitize(self):
        database = [self.entry1, self.entry2, self.entry3]

        self.assertListEqual(self.database.sanitize(database), [])

    def test_WriteEntry(self):
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

        # Orders the entry1 data and formats it appropriately
        orderedEntry = [entryData[order] for order in self.database.dataOrder]
        expectedEntry = self.database.template.format(*orderedEntry)

        mockOpen = mock.mock_open()
        with mock.patch("builtins.open", mockOpen, create=True):
            self.database._writeEntry("foo", entryData)

            mockOpen().write.assert_called_once_with(expectedEntry)

    def test_InitializeDataFile(self):
        mockOpen = mock.mock_open()
        with mock.patch("builtins.open", mockOpen, create=True):
            self.database._initializeDataFile("bar")

            # Asserts whether the header was written into the database file
            header = self.database.template.format(*self.database.dataOrder)
            mockOpen().write.assert_called_once_with(header)

    def _assertSorted(self, entries):
        """
        Asserts whether the database is sorted based on fructose
        concentration then by ASH value (in ascending order).

        :param entries: A list containing the dictionary of entries.
        """
        try:
            while(True):
                entryA = next(entries)
                entryB = next(entries)

                fructoseA, ashA = float(entryA["FR"]), float(entryA["ASH"])
                fructoseB, ashB = float(entryB["FR"]), float(entryB["ASH"])

                if fructoseA > fructoseB:
                    self.fail("Fructose concentrations are not sorted!")

                if fructoseA == fructoseB:
                    if ashA > ashB:
                        self.fail("ASH values are not sorted")
        except StopIteration:
            pass


############################# INTEGRATION TESTS ################################


class TestIntegration(unittest.TestCase):

    def setUp(self):
        self.databaseDir = os.path.join("..", "test", "database")
        self.resultsDir = os.path.join("..", "test", "results")
        settingsPath = os.path.join(".", "settings.ini")

        self.controller = Controller(settingsPath)

    def testReadIniFile(self):
        self.assertListEqual(self.controller.config.sections(), ["PATHS"])

    def testGenerateTypeASubsetDatabase(self):
        expectedDatabase = os.path.join(self.databaseDir, "expected",
                                        "type_a_subset_sorted.txt")
        producedDatabase = os.path.join(self.databaseDir, "produced",
                                        "type_a_subset_output.txt")
        ignoredDatabase = os.path.join(self.databaseDir, "produced",
                                       "type_a_subset_ignored.txt")
        results = os.path.join(self.resultsDir, "type_a_subset")
        resultsLog = os.path.join(self.databaseDir, "produced",
                                  "type_a_subset_results_log.txt")

        self.controller.config["PATHS"]["results_read"] = results
        self.controller.config["PATHS"]["results_read_log"] = resultsLog
        self.controller.config["PATHS"]["database"] = producedDatabase
        self.controller.config["PATHS"]["database_ignored"] = ignoredDatabase

        # Extracting data, sorting then storing it in a database
        self.controller.generateDatabase()
        self.assertTrue(filecmp.cmp(producedDatabase, expectedDatabase,
                                    shallow=False))

    def testQueryMockDatabase(self):
        mockPath = os.path.join(self.databaseDir, "expected", "mock.txt")
        database = self.controller.database.read(mockPath)
        matches = self.controller.database.query(database, {"FR": 100, "AWA": -1.7})

        self.assertTrue(len(matches) == 5)

    def testSanitizeMockDatabase(self):
        mockPath = os.path.join(self.databaseDir, "expected", "mock.txt")
        database = self.controller.database.read(mockPath)
        sanitizedEntries = self.controller.database.sanitize(database)

        self.assertTrue(len(sanitizedEntries) == 7)

    def testSortMockDatabase(self):
        mockPath = os.path.join(self.databaseDir, "expected", "mock.txt")
        mockSorted = os.path.join(self.databaseDir, "expected", "mock_sorted.txt")

        database1 = self.controller.database.read(mockPath)
        sortedDatabase1 = self.controller.database.sort(database1)
        sortedDatabase2 = self.controller.database.read(mockSorted)

        if len(sortedDatabase1) != len(sortedDatabase2):
            self.fail("Sorted database entries does not match expectations!")

        for i, _ in enumerate(sortedDatabase1):
            print(sortedDatabase1[i])
            print(sortedDatabase2[i])
            print()
            self.assertDictEqual(sortedDatabase1[i], sortedDatabase2[i])


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


if __name__ == '__main__':
    unittest.main()
