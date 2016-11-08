import plotly.offline as offline
import plotly.graph_objs as go
from plotly import tools
from iKidsParser import parse_basic_human_computer_comparison, parse_unity_log_files
import argparse
import os
import tkFileDialog
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
                    "(default=100 points)", default=100, dest='avg_size')
parser.add_argument("-auto_open", help="Automatically open the output file.", default="true", dest="auto_open")
args = parser.parse_args()

auto_open = False
# Get auto_open parameter
if args.auto_open.lower() == "true" or args.auto_open == "1":
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
    participant_id = os.path.splitext(os.path.basename(path))[0]  # Participant ID is the filename
    # Open file and set configuration parameters
    data = parse_basic_human_computer_comparison(path, moving_average_window_size=args.avg_size)
elif mode == 'unity':
    participant_id = unity_files['input'].split('log-')[1]  # Participant ID is date-part
    data = parse_unity_log_files(unity_files['input'], unity_files['state'], moving_average_window_size=args.avg_size)

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

# Create moving average accuracy plot line
trace_running_accuracy = go.Scatter(
    x=data.x_agree_running_proportion,
    y=data.y_agree_running_proportion,
    mode='lines',
    name="Agreement % ({0} sample moving average)".format(data.moving_average_window_size),
    hoverinfo="y",
    line=dict(
        shape='linear'
    ),
    yaxis='y4'
)

# Generate subplots
fig = tools.make_subplots(rows=4, cols=1, shared_xaxes=True)

# Configure title and axis formats
fig['layout'].update(title='iKids Newborn Cognitive Visualization')
fig['layout']['yaxis1'].update(title='Raw Data', type="category")
fig['layout']['yaxis2'].update(title='Agreement', type="category", categoryorder='array', categoryarray=[False, True])
fig['layout']['yaxis3'].update(title='Phase', type="category")
fig['layout']['yaxis4'].update(title='Accuracy')

# Add traces
fig.append_trace(trace_human, 1, 1)
fig.append_trace(trace_computer, 1, 1)
fig.append_trace(trace_agreement, 2, 1)
fig.append_trace(trace_phase, 3, 1)
fig.append_trace(trace_running_accuracy, 4, 1)

# Render plot
offline.plot(fig, filename=participant_id + '.html', auto_open=auto_open)
