import argparse
import datetime
import os
import tkFileDialog

from iKidsParser import parse_unity_log_files, phase_key_numbered

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

participant_ids = []
data = []
for sample in unity_files:
    # noinspection PyTypeChecker
    participant_ids.append(sample['input'].split('log-')[1])  # Participant ID is date-part
    # noinspection PyTypeChecker
    data.append(parse_unity_log_files(sample['input'], sample['state'], sample['config'],
                                      moving_average_window_size=args.avg_size,
                                      minimum_latency=args.min_latency,
                                      latency_mode=args.latency_mode))


def make_output_line(data_sample):
    p = data_sample.participant_id
    c = data_sample.condition
    keys = phase_key_numbered
    phases = dict()
    for k in keys:
        phases[k] = [0, 0, 0]

    for idx, (x, state, label) in enumerate(zip(data_sample.x_human, data_sample.y_human,
                                                data_sample.abstract_phases_numbered)):
        if label in keys:
            try:
                t = (data_sample.x_human[idx + 1] - x)
            except IndexError:
                t = 0
            if state == 'left':
                phases[label][0] += t
                phases[label][2] += t
            elif state == 'right':
                phases[label][1] += t
                phases[label][2] += t

    states = []
    for phase in phases:
        value = phases[phase]
        states.append(str(value[0]))
        states.append(str(value[1]))
        states.append(str(value[2]))

    return_val = [p, c]
    return_val.extend(states)
    return return_val


output_filename = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                               datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%p.csv"))
phase_key_numbered_expanded = []
for key in phase_key_numbered:
    phase_key_numbered_expanded.append(key + '_left')
    phase_key_numbered_expanded.append(key + '_right')
    phase_key_numbered_expanded.append(key + '_total')
f = open(output_filename, 'wb')
header = 'Participant ID,Condition,' + ','.join(phase_key_numbered_expanded)
f.write(header + '\n')
for d in data:
    output = make_output_line(d)
    f.write(','.join(output) + '\n')
