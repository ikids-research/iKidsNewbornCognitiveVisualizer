import plotly.offline as offline
import plotly.graph_objs as go
from plotly import tools
from iKidsParser import parse_basic_human_computer_comparison, parse_unity_log_files
import argparse
import os

parser = argparse.ArgumentParser()
parser.add_argument("-test_mode", help="either 'xlsx' or 'unity' to test both types of input files", default='unity')
args = parser.parse_args()

# Initialize notebook
offline.init_notebook_mode()

test_mode = 'unity'
if args.test_mode:
    test_mode = args.test_mode

if test_mode == 'xlsx':
    if not os.path.exists('./497_output_xlsx.txt'):
        print ("Error: The expected input file '497_output_xlsx.txt' was not found. Please unzip the sample data from" +
               " iKidsNewbornCognitiveVisualizerData.zip and try again.")
        exit()
    input_filename = '497_output_xlsx.txt'
    participant_id = input_filename[0:3]
    # Open file and set configuration parameters
    data = parse_basic_human_computer_comparison(input_filename, moving_average_window_size=100)
elif test_mode == 'unity':
    if not os.path.exists('./ikids_newborn_cognitive_unity_input_log-2016-10-26_11-03-28-AM.log'):
        print ("Error: The expected input file '497_output_xlsx.txt' was not found. Please unzip the sample data from" +
               " iKidsNewbornCognitiveVisualizerData.zip and try again.")
        exit()
    if not os.path.exists('./ikids_newborn_cognitive_unity_state_log-2016-10-26_11-03-28-AM.log'):
        print ("Error: The expected input file '497_output_xlsx.txt' was not found. Please unzip the sample data from" +
               " iKidsNewbornCognitiveVisualizerData.zip and try again.")
        exit()
    participant_id = 'test'
    data = parse_unity_log_files('ikids_newborn_cognitive_unity_input_log-2016-10-26_11-03-28-AM.log',
                                 'ikids_newborn_cognitive_unity_state_log-2016-10-26_11-03-28-AM.log')

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
offline.plot(fig, filename=participant_id + '.html')
