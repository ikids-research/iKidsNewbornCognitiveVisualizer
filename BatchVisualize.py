import argparse
import datetime
import os
import tkFileDialog

from iKidsParser import parse_unity_log_files, phase_key_numbered, phase_numbers_numbered

from subprocess import call

try:
    import tkinter as tk
except ImportError:
    import Tkinter as tk
import logging

# Initialize the logger
logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.INFO)

# Generate arguments
parser = argparse.ArgumentParser(description="This script will batch parse a folder of Unity log files, producing a " +
                                             "single file with appropriate output metrics.")
parser.add_argument("-i", help="A folder of Unity log files (nested or flat) containing Unity log files. Note: " +
                               "All 3 log files should be present and in the same directory for each sample " +
                               "otherwise execution may fail.",
                    default='', dest='i')
parser.add_argument("-moving_avg_size", help="The size of the moving average window for visualization " +
                                             "(default=100 points)", default=100, dest='avg_size', type=int)
parser.add_argument("-minimum_latency", help="The minimum latency of update to allow for accuracy measurement " +
                                             "(default 0.1s).", default=0.1, dest="min_latency", type=float)
parser.add_argument("-latency_mode", help="Latency mode can be all, first, or second - meaning if latency " +
                                          "exceeds -minimum_latency (default 0.1s), either both points surrounding the interval are ignored "
                                          "(all), the first point around the interval is ignored (first), or the second point around the "
                                          "interval is ignored (second). (default=all)", default="all",
                    dest="latency_mode",
                    choices=['all', 'first', 'second'])
args = parser.parse_args()

# Get the path from the argument or a dialog if no argument is provided
directory = args.i
if args.i == '' or args.i is None:
    root = tk.Tk()
    root.withdraw()
    directory = tkFileDialog.askdirectory()
if not os.path.exists(directory):  # Path must exist otherwise exit by default.
    logging.error('Selected file ({0}) not found. Closing.'.format(directory))
    exit()

unity_file_key_string = 'ikids_newborn_cognitive_unity_'  # The prefix to find in the filename to identify as Unity log

paths = []
for root, dirs, files in os.walk(directory):
    for f in files:
        if f.startswith(unity_file_key_string + 'config'):
            paths.append(os.path.join(root, f))

logging.info("Directory {0} selected.".format(directory))

# Detect if file is a Unity log file and search for the 3 required log files in the same directory

unity_file_types = ['config', 'input', 'state']  # Types of files
unity_files = []  # Dictionary to store the log file names
for path in paths:
    unity_files_dict = dict()
    current_type = os.path.basename(path)[len(unity_file_key_string):].split('_')[0]  # Identify the selected file type
    base_directory = os.path.dirname(path)
    for expected_type in unity_file_types:  # Search local directory for correct log files and generate list
        validate_path = os.path.join(base_directory, path.replace(current_type, expected_type))
        if expected_type == current_type:
            unity_files_dict[expected_type] = validate_path
            continue  # We already found this file at the beginning so we just set and move on
        else:
            if not os.path.exists(validate_path):  # Confirm the additional log file exists
                logging.error(('File {0} not found adjacent to selected file as expected. ' +
                               'Closing.').format(os.path.exists(validate_path)))
                exit()
            else:  # If the log exists, add it to the unity files
                unity_files_dict[expected_type] = validate_path
    unity_files.append(unity_files_dict)

for file_group in unity_files:
    command = "python \""+os.path.join(os.path.dirname(__file__), "Main.py")+\
              "\" -auto_open false -i \""+file_group['config']+"\""
    call(command)
