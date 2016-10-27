import plotly.offline as offline
import plotly.graph_objs as go
from plotly import tools
import numpy as np

# Initialize notebook
offline.init_notebook_mode()

# Open file and set configuration parameters
f = open('497_output_xlsx.txt', 'rb')
moving_average_window_size = 100

# Remove the first line (header)
f.readline()

# Create data arrays
x_human = []
x_computer = []
x_agreement = []
y_human = []
y_computer = []
y_agreement = []
x_phase = []
y_phase = []
agree_list = []
x_agree_running_proportion = []
y_agree_running_proportion = []

# Parse first line
first_line = f.readline()
split_line = first_line.split(' ')
val_human = split_line[2].strip()
val_computer = split_line[3].strip()
val_agreement = val_human == val_computer
phase = int(split_line[0].split('_')[0])
x_val = float(split_line[1].strip())

# Append first values to data arrays
x_human.append(x_val)
y_human.append(val_human)
x_computer.append(x_val)
y_computer.append(val_computer)
x_agreement.append(x_val)
y_agreement.append(val_agreement)
x_phase.append(x_val)
y_phase.append(phase)

# Iterate through remainder of the file
for line in f:
    split_line = line.split(' ')
    val_human = split_line[2].strip()
    val_computer = split_line[3].strip()
    val_agreement = val_human == val_computer
    x_val = float(split_line[1].strip())
    if not val_human == y_human[-1]:
        x_human.append(x_val)
        y_human.append(val_human)
    if not val_computer == y_computer[-1]:
        x_computer.append(x_val)
        y_computer.append(val_computer)
    if not val_agreement == y_agreement[-1]:
        x_agreement.append(x_val)
        y_agreement.append(val_agreement)
    agree_list.append(val_agreement)
    if len(agree_list) > moving_average_window_size:
        agree_list.pop(0)
    x_agree_running_proportion.append(x_val)
    y_agree_running_proportion.append(np.average(agree_list))
    phase = int(split_line[0].split('_')[0])
    if not phase == y_phase[-1]:
        x_phase.append(x_val)
        y_phase.append(phase)

# Create human plot line
trace_human = go.Scatter(
    x=x_human,
    y=y_human,
    mode='lines',
    name="Human",
    hoverinfo="none",
    line=dict(
        shape='vh'
    )
)

# Create computer plot line
trace_computer = go.Scatter(
    x=x_computer,
    y=y_computer,
    mode='lines',
    name="Computer",
    hoverinfo="none",
    line=dict(
        shape='vh'
    )
)

# Create agreement plot line
trace_agreement = go.Scatter(
    x=x_agreement,
    y=y_agreement,
    mode='lines',
    name="Agreement",
    hoverinfo="none",
    line=dict(
        shape='vh'
    ),
    yaxis='y2',
    fill='tozeroy'
)

# Create phase plot line
trace_phase = go.Scatter(
    x=x_phase,
    y=y_phase,
    mode='lines',
    name="Phase",
    hoverinfo="none",
    line=dict(
        shape='vh'
    ),
    yaxis='y3'
)

# Create moving average accuracy plot line
trace_running_accuracy = go.Scatter(
    x=x_agree_running_proportion,
    y=y_agree_running_proportion,
    mode='lines',
    name="Agreement % ({0} sample moving average)".format(moving_average_window_size),
    hoverinfo="y",
    line=dict(
        shape='vh'
    ),
    yaxis='y4'
)

# Generate subplots
fig = tools.make_subplots(rows=4, cols=1, shared_xaxes=True)

# Configure title and axis formats
fig['layout'].update(title='iKids Newborn Cognitive Visualization')
fig['layout']['yaxis1'].update(title='Raw Data', type="category")
fig['layout']['yaxis2'].update(title='Agreement', type="category")
fig['layout']['yaxis3'].update(title='Phase', type="category")
fig['layout']['yaxis4'].update(title='Accuracy')

# Add traces
fig.append_trace(trace_human, 1, 1)
fig.append_trace(trace_computer, 1, 1)
fig.append_trace(trace_agreement, 2, 1)
fig.append_trace(trace_phase, 3, 1)
fig.append_trace(trace_running_accuracy, 4, 1)

# Render plot
offline.plot(fig)
