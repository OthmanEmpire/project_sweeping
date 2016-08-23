## Project Sweeping--Tidying Files And Collecting Data

The project is specifically designed for making management of generated data much easier from a specific worm (C. Elegans) simulator written in Java. 

In a nutshell, it collects scattered data, merged it into a single simple text file based database, then queries it to find a goodness of fit for certain parameters that can then be thrown into the java simulator.

On a side note but on an important note about the project: many thanks to Dr. Netta Cohen for providing me with guidance and supplying the data throughout.


## Requirements

* Python 3+


## Key Features

* Extracting information from data file path names and their contents
* Generating a database from the collected database
* Querying the database based on specified criteria
* Using queried data to find a goodness of fit for certain parameters


## Running

The only files needed are the *cleaner.py* and *settings.ini* files. To run the code, specify the paths of the directories and files in the *settings.ini* file and then run normally run the *cleaner.py* script. 


## Authors

Supervisor: Dr. Netta Cohen

Author: Othman Ali Khan  
Email: sc14omsa@leeds.ac.uk


## License

This code is distributed under the MIT license. For further information, see the LICENSE file.
