import matplotlib.pyplot as plt
from numpy import *
from collections import deque

x = linspace(0, 30, 30/0.03 + 1)
y = random.random_integers(0, 3, len(x))
unique_y = list(set(y))
for idx in range(0, len(y)):
    if random.rand() > 0.5:
        y[idx] = 2
y_filtered = []

filter_window_size = 10.
window = deque()

state_history = []

for xe, ye in zip(x, y):
    window.append(ye)
    if len(window) > filter_window_size:
        window.popleft()
    counts = []
    for uy in unique_y:
        counts.append(window.count(uy))
    state_history.append(counts)
    y_filtered.append(unique_y[array(counts).argmax(axis=0)])


plt.figure(1)
plt.step(x, y)
plt.step(x, y_filtered, color='r')
plt.ylim(-0.5, 3.5)
plt.ylabel('State')
plt.xlabel('Time (s)')
plt.figure(2)
state_history = transpose(state_history)
[plt.plot(x, state_history[idx]) for idx in range(0, len(unique_y))]
plt.show()
