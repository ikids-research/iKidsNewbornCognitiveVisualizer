import numpy as np
from collections import OrderedDict


def parse_basic_human_computer_comparison(filename, moving_average_window_size=100):
    f = open(filename, 'rb')

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

    # Begin Parser

    # Remove the first line (header)
    f.readline()

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
    agree_list.append(val_agreement)
    x_phase.append(x_val)
    y_phase.append(phase)
    y_agree_running_proportion.append(np.average(agree_list))

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

    # End Parser

    # Fill object with parser results and return
    data = type("iKidsDataObject", (object,), {})()
    data.x_human = x_human
    data.x_computer = x_computer
    data.x_agreement = x_agreement
    data.y_human = y_human
    data.y_computer = y_computer
    data.y_agreement = y_agreement
    data.x_phase = x_phase
    data.y_phase = y_phase
    data.agree_list = agree_list
    data.x_agree_running_proportion = x_agree_running_proportion
    data.y_agree_running_proportion = y_agree_running_proportion
    data.moving_average_window_size = moving_average_window_size

    return data


# TODO: Config file is not used
def parse_unity_log_files(input_filename, state_filename, moving_average_window_size=100):
    fi = open(input_filename, 'rb')
    fs = open(state_filename, 'rb')

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

    # Begin Parser

    fs.readline()  # First line in state file should be "Finished loading..." which we don't need

    states_and_inputs = OrderedDict()

    # Merge the two log files so we can easily read all the information at each time point
    for line in fs:
        split_lines = line.split(' : ')
        time = round(float(split_lines[0].strip()), 4)
        rest = ''.join(split_lines[1:])
        if time not in states_and_inputs:
            states_and_inputs[time] = {'state': [], 'input': []}
        if not states_and_inputs[time]['state']:
            states_and_inputs[time]['state'] = []
        states_and_inputs[time]['state'].append(rest)

    for line in fi:
        split_lines = line.split(' : ')
        time = round(float(split_lines[0].strip()), 4)
        rest = ''.join(split_lines[1:])
        if time not in states_and_inputs:
            states_and_inputs[time] = {'state': [], 'input': []}
        if not states_and_inputs[time]['input']:
            states_and_inputs[time]['input'] = []
        states_and_inputs[time]['input'].append(rest)

    # Confirm that the raw data is sorted by time (should be anyway, but it's good to confirm)
    states_and_inputs = OrderedDict(sorted(states_and_inputs.iteritems(), key=lambda x: x[0]))

    state_reference = ['down', 'up', 'left', 'right', 'off']
    tcp_state_lookup = ['d', 'c', 'l', 'r', '']
    keyboard_state_lookup = ['down', 'up', 'left', 'right', '']

    # TODO: This assumes there is one value at a time - not always true (for instance, if two buttons are pressed)
    def find_subval_in_val(val, substr, lookup, reference):
        try:
            found_value = [sx for sx in val if substr in sx][0].split(':')[1].strip()
        except IndexError:
            return -1
        if ',' in found_value:
            found_value = found_value.split(',')[0]
        return reference[lookup.index(found_value)]

    si = states_and_inputs.values()[0]
    si_key = states_and_inputs.keys()[0]
    state_list = si['state']
    input_list = si['input']

    val_human = find_subval_in_val(input_list, 'Keyboard Commands', keyboard_state_lookup, state_reference)
    val_computer = find_subval_in_val(input_list, 'TCP Commands', tcp_state_lookup, state_reference)
    val_agreement = val_human == val_computer
    phase = int([s for s in state_list if 'Current Task Index' in s][0].split(':')[1].strip())
    x_val = si_key

    x_human.append(x_val)
    x_computer.append(x_val)
    x_agreement.append(x_val)
    x_phase.append(x_val)
    x_agree_running_proportion.append(x_val)
    y_human.append(val_human)
    y_computer.append(val_computer)
    y_agreement.append(val_agreement)
    y_phase.append(phase)
    agree_list.append(val_agreement)
    y_agree_running_proportion.append(np.average(agree_list))

    iter_si = iter(states_and_inputs)
    next(iter_si)
    for si_key in iter_si:
        si = states_and_inputs[si_key]
        state_list = si['state']
        input_list = si['input']

        val_human = find_subval_in_val(input_list, 'Keyboard Commands', keyboard_state_lookup, state_reference)
        if val_human == -1:
            val_human = y_human[-1]
        val_computer = find_subval_in_val(input_list, 'TCP Commands', tcp_state_lookup, state_reference)
        if val_computer == -1:
            val_computer = y_computer[-1]
        if val_computer == 'off':
            val_computer = y_computer[-1]
        val_agreement = val_human == val_computer
        try:
            phase = int([s for s in state_list if 'Current Task Index' in s][0].split(':')[1].strip())
        except IndexError:
            phase = -1
        x_val = si_key

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
        y_agree_running_proportion.append(np.mean(agree_list))
        if not phase == y_phase[-1]:
            x_phase.append(x_val)
            y_phase.append(phase)

    # End Parser

    # Fill object with parser results and return
    data = type("iKidsDataObject", (object,), {})()
    data.x_human = x_human
    data.x_computer = x_computer
    data.x_agreement = x_agreement
    data.y_human = y_human
    data.y_computer = y_computer
    data.y_agreement = y_agreement
    data.x_phase = x_phase
    data.y_phase = y_phase
    data.agree_list = agree_list
    data.x_agree_running_proportion = x_agree_running_proportion
    data.y_agree_running_proportion = y_agree_running_proportion
    data.moving_average_window_size = moving_average_window_size

    return data
