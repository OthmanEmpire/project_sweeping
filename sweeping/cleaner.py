"""
This script is specifically designed for making management of generated data
much easier from a specific worm (C. Elegans) simulator written in Java.

In a nutshell, it collects scattered data, merged it into a single simple
text file based database, then queries it to find a goodness of fit for
certain parameters that can then be thrown into the java simulator once more
for improved results.

__author__ = "Othman Alikhan"
__email__ = "sc14omsa@leeds.ac.uk"
__date__ = "2016-08-15"
"""
import csv
import os
import time
import datetime
import configparser


class Extractor:
    """
    Responsible for extracting data from file contents and their paths.
    """

    def extractAllData(self, dataDirPath, logPath):
        """
        Extracts data from all sources (i.e. file paths and their contents)

        :param dataDirPath: The path to the directory that hosts all the data.
        :param logPath: The path to the log file.
        :return: A list containing dictionaries of the data parsed for each
        single file.
        """
        self._initializeLogFile(logPath)
        data = {}
        allData = []
        hasErrorOccurred = False     # Flag highlighting a parsing error

        for path in self._listAllFilePaths(dataDirPath):
            # Extends the path from root to the data file
            path = os.path.join(dataDirPath, path)

            # Attempts to extract data from file path and contents
            # otherwise stores the error in a separate error log file
            try:
                dataFromPath = self._extractDataFromPath(path)
                dataFromFile = self._extractDataFromFile(path)
            except ValueError as e:
                with open(logPath, "a") as log:
                    stamp = datetime.datetime.fromtimestamp(time.time())
                    stamp = stamp.strftime("%m/%d %H:%M:%S")
                    error = "{}, {}\n".format(stamp, str(e))
                    log.write(error)
                hasErrorOccurred = True
                continue

            # Merging both dictionaries
            data = dataFromPath.copy()
            data.update(dataFromFile)
            allData.append(data)

        # Warns the user if all or some data failed to be extracted
        if hasErrorOccurred:
            print("WARNING: Some files weren't parsed properly, check"
                  "error logs for more details!")
        elif not allData:
            print("WARNING: Could not find a extract a shred of data! "
                  "Perhaps the results directory is incorrectly specified?")
        return allData

    def _extractDataFromPath(self, filePath):
        """
        Parses the given file path and extracts data from it which is then
        returned as a dictionary. The data parsed contains: fructose
        concentration, simulation type (uni or multi), ASH value, AWA value,
        path to file, and date of simulation.

        :param filePath: The path of the data file from the root directory.
        The root directory should be the "results" directory otherwise it
        should be two directories above a data file.
        :return: A dictionary containing data extracted from the file path.
        """
        paths = filePath.split(os.sep)
        folder, file = paths[-2], paths[-1]

        # Extracting data from the folder name. The convention
        # is "date_<letter>_fructose"
        folder = folder.split("_")

        if len(folder) == 3:
            simDate = folder[0]
            fructose = folder[-1]
        elif len(folder) == 4:
            simDate = folder[1]
            fructose = folder[-1]
        else:
            raise NameError("The following folder is named inconsistently, {}"
                            .format(filePath))

        # Extracting data from the file name
        file = file.split("_")
        file = file[-1]     # Only the end contains useful data
        file = file.rstrip(".csv")
        file = file.split("&")
        uniMulti, awa, ash, = file

        dataExtracted = \
        {
            "FR":       fructose,
            "MULTI":    uniMulti,
            "ASH":      ash,
            "AWA":      awa,
            "PATH":     filePath,
            "DATE":     simDate
        }
        return dataExtracted

    def _extractDataFromFile(self, filePath):
        """
        Reads the given file name, parses the contents to extract data.
        The data parsed contains: the total number of worms, the worms
        exited, percentage exited (calculated), and file name.

        :param filePath: The path of the data file from the root directory.
        The root directory should be the "results" directory otherwise it
        should be two directories above a data file.
        :return: A dictionary containing the data extracted from the file
        contents.
        """
        with open(filePath, "r") as file:
            header = file.readline()    # Skips first line containing header
            wormCount = 0
            wormExitedCount = 0

            for i, entry in enumerate(file, start=1):
                # Skips over blank lines
                if not entry.strip():
                    continue

                # Attempts to extract data for each entry1
                try:
                    wormNum, timeExited = entry.rstrip().split(",")
                except ValueError as e:
                    raise ValueError("Unable to parse line {} from the "
                                     "following file: {}".format(i+1, filePath))

                # Counting total worms and those that exited
                wormCount += 1
                if float(timeExited) != -1.0:
                    wormExitedCount += 1

            # Avoiding the formation of a blackhole by dividing by zero
            if wormCount:
                exit = str(float(wormExitedCount) / float(wormCount))
            else:
                exit = "0"

            dataExtracted = \
            {
            "N":        str(wormCount),
            "N_OUT":    str(wormExitedCount),
            "EXIT":     exit,
            "PATH":     filePath
            }
            return dataExtracted

    def _listAllFilePaths(self, dataDirPath):
        """
        Lists all the relevant paths from the results directory to the data
        files. Initially, lists all existing files in the results directory
        then proceeds to filter out irrelevant ones.

        :param dataDirPath: The path to the directory that hosts all the data.
        :return: A list containing all the paths from the results directory
        to the data files.
        """
        allPaths = []
        pathList = []
        expectedResultsDir = dataDirPath.split(os.sep)[-1]

        # Generate all the paths for all files starting from the rootPath
        for root, dirs, files in os.walk(dataDirPath):
            for file in files:
                pathFromRoot = os.path.join(root, file)
                allPaths.append(pathFromRoot)

        # Filter out invalid paths (e.g. paths that point to .txt files
        # instead of csv files, or paths that contain
        # "in_spot_processed_output instead of "exit_time_raw_output")
        for pathFromRoot in allPaths:

            # Remove all path components except the last three parts which
            # have the results dir, data dir, and data file respectively
            path = pathFromRoot.split(os.sep)
            resultsDir, dataDir, file = path[-3], path[-2], path[-1]

            # Filter file paths based on depth from results directory (done
            # indirectly), file name, and extension
            if resultsDir == expectedResultsDir:
                if file.endswith(".csv") and "exit_time_raw_output" in file:
                    path = os.path.join(dataDir, file)
                    pathList.append(path)
            else:
                raise NameError("The following folder is named inconsistently,"
                                " {}".format(pathFromRoot))

        return pathList

    def _initializeLogFile(self, filePath):
        """
        Deletes the log file if it already exists.

        :param filePath: The path to the log file.
        """
        if os.path.exists(filePath):
            os.remove(filePath)


class Database:
    """
    Responsible for managing the database. Namely for inputting entries and
    querying.
    """

    def __init__(self):
        """
        A simple constructor.
        """
        # Initializing formatting variables for CSV database file
        self.dataOrder = ["FR", "ASH", "AWA", "N", "N_OUT",
                          "EXIT", "MULTI", "DATE", "PATH"]
        self.template = len(self.dataOrder)*"{:<9} " + "\n"

    def read(self, databasePath):
        """
        Reads the the given database.

        :param databasePath: The path to the database file.
        :return: A list containing the database entries as dictionaries.
        """
        allEntries = []

        with open(databasePath, "r") as database:
            database = csv.reader(database,
                                  delimiter=" ",
                                  skipinitialspace=True)
            header = next(database)

            for data in database:
                allEntries.append(dict(zip(header, data)))

        return allEntries

    def create(self, databasePath, entries):
        """
        Populates the database with entries.

        :param databasePath: The path to the database file.
        :param entries: A list containing dictionaries which themselves
        contain data for a single row in the database.
        """
        self._initializeDataFile(databasePath)

        for entry in entries:
            self._writeEntry(databasePath, entry)

    def query(self, database, query):
        """
        Queries the database with the filters specified in the .ini file and
        generates the output in a file specified in the .ini as well.

        :param database: A list containing database entries as dictionaries.
        :param query: A dictionary containing the query data.
        :return: A list containing dictionaries which themselves contain data
        for a single row in the database.
        """
        totalCriteria = len(query)
        validMatches = []

        # For every entry1 in the database, checks whether the query
        # criteria are matched, and if so then stores the line.
        for entry in database:

            # Counts the number of criteria matches
            criteriaMatched = 0
            for key in query.keys():
                if float(query[key]) == float(entry[key]):
                    criteriaMatched += 1

            # If all the criteria match then the result is stored
            if criteriaMatched == totalCriteria:
                validMatches.append(entry)

        return validMatches

    def sort(self, database):
        """
        Sorts the database in ascending number based on the fructose
        concentration followed by the ASH value.

        :param database: A list containing database entries as dictionaries.
        :return: A list containing the sorted database entries as dictionaries.
        """
        sortedDatabase = sorted(database, key=lambda k: (float(k["FR"]),
                                                         float(k["ASH"])))
        return sortedDatabase

    #TODO: Return the purged entries as well perhaps
    def sanitize(self, database):
        """
        Sanitizes the database by removing results that are not considered
        interesting.

        Namely, it removes results where the number of worms is zero or not a
        multiple of 100 (implying an error in the data itself).

        :param database: A list containing database entries as dictionaries.
        :return: A list containing the sanitized database entries as
        dictionaries.
        """
        sanitizedEntries = []

        for i, entry in enumerate(database):
            worms = int(entry["N"])
            if worms != 0 and worms % 100 == 0:
                sanitizedEntries.append(entry)

        return sanitizedEntries

    def _writeEntry(self, databasePath, data):
        """
        Writes the given entry1 data into the supplied database in the
        correct format.

        :param data: A dictionary containing the data for a single row in
        the database.
        :param databasePath: The path to the database file.
        """
        orderedData = [data[order] for order in self.dataOrder]

        # Writes the data formatted prettily into the database
        with open(databasePath, "a") as database:
            database.write(self.template.format(*orderedData))

    def _initializeDataFile(self, filePath):
        """
        Creates a new file with a header containing the data parameters.

        :param filePath: The path to the database file.
        """
        with open(filePath, "w") as file:
            header = self.template.format(*self.dataOrder)
            file.write(header)


# TODO: Start implementing the first part of the dumb algorithm
class Controller:
    """
    The puppeteer that

    """

    def __init__(self, settingsPath):
        """
        A simple constructor.

        :param settingsPath: The path to the .ini file containing settings.
        """
        # Reads the .ini file
        self.config = configparser.ConfigParser()
        self.config.read(settingsPath)

        # Initializing variables
        self.database = Database()
        self.extractor = Extractor()

    def run(self):
        paths = self.config["PATHS"]
        data = self.extractor.extractAllData(paths["results_read"],
                                             paths["results_read_log"])
        data = self.database.sort(data)
        data = self.database.sanitize(data)
        self.database.create(paths["database_output"], data)

        for entry in data:
            uniQuery = {"FR": entry["FR"], "ASH": entry["ASH"],
                        "MULTI": "0"}
            multiQuery = {"FR": entry["FR"], "ASH": entry["ASH"],
                          "AWA": entry["AWA"], "MULTI": "1"}

            uniMatches = self.database.query(data, uniQuery)
            multiMatches = self.database.query(data, multiQuery)

            if not uniMatches:
                print("No Uni matches found!")
            else:
                print(uniMatches)

            if not multiMatches:
                print("No multi matches found!")
            else:
                print(multiMatches)

            print()


if __name__ == '__main__':
    controller = Controller("settings.ini")
    controller.run()
