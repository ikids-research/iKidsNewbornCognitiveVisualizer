import argparse
import os
import tkFileDialog

import plotly.graph_objs as go
import plotly.offline as offline
from plotly import tools

from iKidsParser import parse_basic_human_computer_comparison, parse_unity_log_files

try:
    import tkinter as tk
except ImportError:
    import Tkinter as tk
import logging

# Initialize the logger
logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.INFO)

# Generate arguments
parser = argparse.ArgumentParser(description="This script will visualize either Unity log files from the iKids " +
                                 "Newborn Cognitive Unity Stimulus program or validation files from the original " +
                                 "eye tracking data. If called via command line, some additional parameters can be " +
                                 "set. Otherwise, defaults are used and a dialog is displayed. All outputs are HTML " +
                                 "files which are saved in the directory of this script and opened automatically " +
                                 "upon creation. Rerunning this script on the same log file twice will regenerate " +
                                 "the output HTML file.")
parser.add_argument("-i", help="Any log file produced by Unity or a csv from original validation format. In the case " +
                    "of Unity log files, only one of the 3 file needs to be selected, the other two will be " +
                    "automatically detected. Note: Only required files being missing will halt execution.", default='',
                    dest='i')
parser.add_argument("-moving_avg_size", help="The size of the moving average window for visualization " +
                    "(default=100 points)", default=100, dest='avg_size', type=int)
parser.add_argument("-auto_open", help="Automatically open the output file.", default="true", dest="auto_open",
                    choices=['true', 'false'])
parser.add_argument("-minimum_latency", help="The minimum latency of update to allow for accuracy measurement " +
                                             "(default 0.1s).", default=0.1, dest="min_latency", type=float)
parser.add_argument("-latency_mode", help="Latency mode can be all, first, or second - meaning if latency " +
                    "exceeds -minimum_latency (default 0.1s), either both points surrounding the interval are ignored "
                    "(all), the first point around the interval is ignored (first), or the second point around the "
                    "interval is ignored (second). (default=all)", default="all", dest="latency_mode",
                    choices=['all', 'first', 'second'])
args = parser.parse_args()

auto_open = False
# Get auto_open parameter
if args.auto_open.lower() == "true":
    auto_open = True

# Get the path from the argument or a dialog if no argument is provided
path = args.i
if args.i == '' or args.i is None:
    root = tk.Tk()
    root.withdraw()
    path = tkFileDialog.askopenfilename()
if not os.path.exists(path):  # Path must exist otherwise exit by default.
    logging.error('Selected file ({0}) not found. Closing.'.format(path))
    exit()

logging.info("File {0} selected.".format(path))

# Detect if file is a Unity log file and search for the 3 required log files in the same directory
unity_file_key_string = 'ikids_newborn_cognitive_unity_'  # The prefix to find in the filename to identify as Unity log
unity_file_types = ['config', 'input', 'state']  # Types of files
unity_files = dict()  # Dictionary to store the log file names
if os.path.basename(path)[0:len(unity_file_key_string)] == unity_file_key_string:  # If it is a Unity log file
    logging.info("Found Unity log file prefix. Assuming Unity file format and searching for other log files in this " +
                 "directory.")
    mode = "unity"  # Set mode to unity and find log files
    current_type = os.path.basename(path)[len(unity_file_key_string):].split('_')[0]  # Identify the selected file type
    for expected_type in unity_file_types:  # Search local directory for correct log files and generate list
        if expected_type == current_type:
            unity_files[expected_type] = path
            continue  # We already found this file at the beginning so we just set and move on
        else:
            if not os.path.exists(path.replace(current_type, expected_type)):  # Confirm the additional log file exists
                logging.error(('File {0} not found adjacent to selected file as expected. ' +
                               'Closing.').format(os.path.exists(path.replace(current_type, expected_type))))
                exit()
            else:  # If the log exists, add it to the unity files
                unity_files[expected_type] = path.replace(current_type, expected_type)
else:  # If this is not a unity log file, assume it's an xlsx file
    logging.info("File assumed to be non-unity file (4 columns - id, time, human_state, computer_state).")
    mode = "xlsx"

participant_id = None
data = None
# Get the data from the parser and set the participant_id based on the input type
if mode == 'xlsx':
    if args.min_latency <= 0.1:
        logging.warning('For xlsx formats, it is typically better to have a >0.1s latency as frames will almost ' +
                        'always be slightly longer than that. 0.2 is suggested. Set this using the -min_latency ' +
                        'argument.')
    participant_id = os.path.splitext(os.path.basename(path))[0]  # Participant ID is the filename
    # Open file and set configuration parameters
    data = parse_basic_human_computer_comparison(path,
                                                 moving_average_window_size=args.avg_size,
                                                 minimum_latency=args.min_latency,
                                                 latency_mode=args.latency_mode)
elif mode == 'unity':
    participant_id = unity_files['input'].split('log-')[-1]  # Participant ID is date-part
    data = parse_unity_log_files(unity_files['input'], unity_files['state'], unity_files['config'],
                                 moving_average_window_size=args.avg_size,
                                 minimum_latency=args.min_latency,
                                 latency_mode=args.latency_mode)

if participant_id is None or data is None:
    logging.error("There was a problem in parsing. No data or participant_id found. Closing.")
    exit()

# Initialize notebook
offline.init_notebook_mode()

# Create human plot line
trace_human = go.Scatter(
    x=data.x_human,
    y=data.y_human,
    mode='lines',
    name="Human",
    hoverinfo="none",
    line=dict(
        shape='hv'
    )
)

# Create computer plot line
trace_computer = go.Scatter(
    x=data.x_computer,
    y=data.y_computer,
    mode='lines',
    name="Computer",
    hoverinfo="none",
    line=dict(
        shape='hv'
    )
)

# Create agreement plot line
trace_agreement = go.Scatter(
    x=data.x_agreement,
    y=data.y_agreement,
    mode='lines',
    name="Agreement",
    hoverinfo="none",
    line=dict(
        shape='hv'
    ),
    yaxis='y2',
    fill='tozeroy'
)

# Create agreement plot line
trace_agreement_latency_mask = go.Scatter(
    x=data.x_agreement,
    y=[not x for x in data.agreement_latency_mask],
    mode='lines',
    name="Agreement Latency Mask",
    hoverinfo="none",
    line=dict(
        shape='hv'
    ),
    yaxis='y2',
    fill='tozeroy'
)

# Create phase plot line
trace_phase = go.Scatter(
    x=data.x_phase,
    y=data.y_phase,
    mode='lines',
    name="Phase",
    hoverinfo="none",
    line=dict(
        shape='hv'
    ),
    yaxis='y3'
)

# Create phase plot line
trace_abstract_phase = go.Scatter(
    x=data.x_phase,
    y=data.abstract_phases,
    mode='lines',
    name="Abstract Phase",
    hoverinfo="none",
    line=dict(
        shape='hv'
    ),
    yaxis='y4'
)

# Create moving average accuracy plot line
trace_running_accuracy = go.Scatter(
    x=data.x_agree_running_proportion,
    y=data.y_agree_running_proportion,
    mode='lines',
    name="Agreement % ({0} S MA)".format(data.moving_average_window_size),
    hoverinfo="y",
    line=dict(
        shape='linear'
    ),
    yaxis='y5'
)

# Create moving average accuracy plot line
trace_latency = go.Scatter(
    x=data.x_agreement,
    y=data.latency_list,
    mode='lines',
    name="Latency (s)",
    hoverinfo="y",
    line=dict(
        shape='hv'
    ),
    yaxis='y6'
)

# Create moving average accuracy plot line
trace_latency_threshold = go.Scatter(
    x=[data.x_agreement[0], data.x_agreement[-1]],
    y=[args.min_latency, args.min_latency],
    mode='lines',
    name="Latency Mask Threshold ({0} s)".format(args.min_latency),
    hoverinfo="y",
    line=dict(
        shape='linear'
    ),
    yaxis='y6'
)

# Generate subplots
fig = tools.make_subplots(rows=6, cols=1, shared_xaxes=True, print_grid=False)

precision = '5'
title = ("iKids Newborn Cognitive - (Agreements: Time-Wise={0:." + precision +
         "f}, Sample-Wise={1:." + precision + "f}, Exclusion Ratio={2:." + precision + "f})").format(
        data.time_wise_agreement,
        data.sample_wise_agreement,
        float(data.agreement_latency_mask.count(False))/float(len(data.agreement_latency_mask)))

logging.info(title)
logging.info("Exclusion Details: False={0}, True={1}".format(float(data.agreement_latency_mask.count(False)),
                                                             float(data.agreement_latency_mask.count(True))))
# Configure title and axis formats
fig['layout'].update(title=title)
fig['layout']['yaxis1'].update(title='Raw Data', type="category")
fig['layout']['yaxis2'].update(title='Agreement', type="category", categoryorder='array', categoryarray=[False, True])
fig['layout']['yaxis3'].update(title='Phase', type="category")
fig['layout']['yaxis4'].update(title='Abstract Phase', categoryorder='array', categoryarray=data.abstract_phase_keys,
                               tickangle=-45)
fig['layout']['yaxis5'].update(title='Accuracy')
fig['layout']['yaxis6'].update(title='Latency', type='log')

# Add traces
fig.append_trace(trace_human, 1, 1)
fig.append_trace(trace_computer, 1, 1)
fig.append_trace(trace_agreement, 2, 1)
fig.append_trace(trace_agreement_latency_mask, 2, 1)
fig.append_trace(trace_phase, 3, 1)
fig.append_trace(trace_abstract_phase, 4, 1)
fig.append_trace(trace_running_accuracy, 5, 1)
fig.append_trace(trace_latency, 6, 1)
fig.append_trace(trace_latency_threshold, 6, 1)

# Render plot
offline.plot(fig, filename=participant_id + '.html', auto_open=auto_open)
