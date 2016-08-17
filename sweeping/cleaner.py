"""
This script is designed to make life easier ;)

Specifically, it allows easier file handling and data gathering for the worm
simulation data. In a nutshell, it allows collection of all scattered data in
file paths and contents and accumulates it all into a single csv file.

__author__ = "Othman Alikhan"
__email__ = "sc14omsa@leeds.ac.uk"
__date__ = "2016-08-15"
"""
import os
import sys


class Janitor:
    """
    Responsible for extracting/parsing data from files and their paths,
    thereafter storing the extracted data in a separate file. Putting it
    another way, this class collects scattered data and centralizes it's
    location so that it is easier to manage.
    """

    def __init__(self, dataPath):
        """
        A simple constructor initializing paths

        :param dataPath: The path to the folder containing all the data.
        """
        self.dataPath = dataPath
        self.databasePath = os.path.join(".", "database.txt")

        # Formatting variables for CSV database file
        self.dataOrder = ["FR", "ASH", "AWA", "N", "N_OUT", "EXIT", "MULTI",
                          "DATE", "PATH"]
        self.databaseTemplate = len(self.dataOrder) * "{:<10}" + "\n"

    def cleanDatabase(self):
        """
        Creates an empty database file with a header if it doesn't exist
        otherwise empties the contents of the existing one and adds a header.
        """
        database = open(self.databasePath, "w")
        header = self.databaseTemplate.format(*self.dataOrder)
        database.write(header)
        database.close()

    def populateDatabase(self):
        """
        Initializes the database and then populates it with entries.
        """
        # Generates a new empty database file (with a header)
        self.cleanDatabase()

        # Loops over all valid file paths and builds the database
        for path in self.listAllFilePaths():
            # Extends the path from root to the data file
            path = os.path.join(self.dataPath, path)

            # Attempts to extract data from file path and contents
            # otherwise stores the error in a separate error log file
            try:
                dataFromPath = self.pickDataFromPath(path)
                dataFromFile = self.pickDataFromFile(path)
            except ValueError as e:
                print(e)
                continue

            # Merging both dictionaries
            data = dataFromPath.copy()
            data.update(dataFromFile)

            self.putDatabaseEntry(data)

    def putDatabaseEntry(self, entryData):
        """
        Writes the given entry data into the supplied database in the
        correct format.

        :param entryData: A dictionary containing the data for a single row
        in the database.
        """
        # Orders the entry data
        orderedEntry = []
        for order in self.dataOrder:
            orderedEntry.append(entryData[order])

        # Formats the entry data nicely and writes it into the database
        with open(self.databasePath, "a") as db:
            entry = self.databaseTemplate.format(*orderedEntry)
            db.write(entry)

    def pickDataFromPath(self, filePath):
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

    def pickDataFromFile(self, filePath):
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

                # Attempts to extract data for each entry
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
                exit = "-"

            dataExtracted = \
            {
            "N":        str(wormCount),
            "N_OUT":    str(wormExitedCount),
            "EXIT":     exit,
            "PATH":     filePath
            }
            return dataExtracted

    def listAllFilePaths(self):
        """
        Lists all the paths from the results directory to the data files.
        Initially, lists all existing files in the results directory then
        proceeds to filter out irrelevant ones.

        :return: A list containing all the paths from the results directory
        to the data files.
        """
        allPaths = []
        pathList = []
        expectedResultsDir = self.dataPath.split(os.sep)[-1]

        # Generate all the paths for all files starting from the rootPath
        for root, dirs, files in os.walk(self.dataPath):
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


if __name__ == '__main__':
    # Runs the script, ensuring sufficient arguments are passed
    if len(sys.argv) != 2:
        raise NameError("Please insert only one argument, "
                        "namely the path to the data directory.")
    else:
        dataPath = os.path.join(sys.argv[1])
        extractor = Janitor(dataPath)
        extractor.populateDatabase()

