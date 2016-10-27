import plotly.offline as offline
import plotly.graph_objs as go
from plotly import tools
import numpy as np

offline.init_notebook_mode()

f = open('497_output_xlsx.txt', 'rb')

moving_average_window_size = 100

f.readline()
x_human = []
x_computer = []
x_agreement = []
y_human = []
y_computer = []
y_agreement = []
first_line = f.readline()
split_line = first_line.split(' ')
val_human = split_line[2].strip()
val_computer = split_line[3].strip()
val_agreement = val_human == val_computer
x_val = float(split_line[1].strip())
x_human.append(x_val)
y_human.append(val_human)
x_computer.append(x_val)
y_computer.append(val_computer)
x_agreement.append(x_val)
y_agreement.append(val_agreement)

phase = int(split_line[0].split('_')[0])
x_phase.append(x_val)
y_phase.append(phase)
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

fig = tools.make_subplots(rows=4, cols=1, shared_xaxes=True)

fig['layout'].update(title='iKids Newborn Cognitive Visualization')
fig['layout']['yaxis1'].update(title='Raw Data', type="category")
fig['layout']['yaxis2'].update(title='Agreement', type="category")
fig['layout']['yaxis3'].update(title='Phase', type="category")
fig['layout']['yaxis4'].update(title='Accuracy')


fig.append_trace(trace_human, 1, 1)
fig.append_trace(trace_computer, 1, 1)
fig.append_trace(trace_agreement, 2, 1)
fig.append_trace(trace_phase, 3, 1)
fig.append_trace(trace_running_accuracy, 4, 1)

offline.plot(fig)
