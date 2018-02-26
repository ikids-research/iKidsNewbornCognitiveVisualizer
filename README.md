# Easy Setup (Windows Only)

1. Run Setup.bat
2. Unzip iKidsNewbornCognitiveVisualizerData.zip (or have log files you wish to visualize in a known location)
3. Run Run.bat (and select a log file)

# Setup

To use this program, the following software should be installed. This has only been tested on Windows 10, but other version of Windows should work (and perhaps other OSes as nothing is particularly OS specific).

1. Install Anaconda Python 2.7 64bit (32 might work, haven't tested) from https://www.continuum.io/downloads
2. Run the following command:

    `pip install plotly argparse`

3. (optional) Install PyCharm Community Edition from https://www.jetbrains.com/pycharm/download/
4. Download this repo as zip (https://github.com/kevroy314/iKidsNewbornCognitiveVisualizer/archive/master.zip) and unzip in a known location or call git clone

# Script Files

* **Main.py** - Performs the primary visualization on a specific file.
* **BatchVisualize.py** - Calls Main.py on all files in a specified folder.
* **BatchProcessFolder.py** - Parses a folder of Unity log files and produces an output CSV.
* **VideoLogger.py** - Allows for the manual labeling of a video.

# Usage

Verious processes/functions can be run conveniently by running the various .bat Batch Files. Otherwise, scripts can be run using the 'python' command from the command line. Most scripts also have argparse command-line arguments to modify its function. These will appear automatically when the function is called with only the -h argument.
