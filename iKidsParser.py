from collections import OrderedDict
import logging
from collections import deque
import numpy as np
import sklearn.metrics as metrics


def list_mask_by_latency(t, latency=0.1, remove_start_point=True, remove_end_point=False):
    # Find all remove/keep positions
    mask_t = [True] * len(t)
    latencies = [-1.0] * len(t)
    iterator = enumerate(t)
    next(iterator)
    for idx, current_t in iterator:
        prev_t = t[idx - 1]
        current_latency = float(current_t) - float(prev_t)
        latencies[idx] = current_latency
        if current_latency > latency:
            if remove_start_point:
                mask_t[idx - 1] = False
            if remove_end_point:
                mask_t[idx] = False

    return mask_t, latencies


def parse_basic_human_computer_comparison(filename,
                                          moving_average_window_size=100,
                                          minimum_latency=0.1,
                                          latency_mode='all'):
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
        phase = int(split_line[0].split('_')[0])
        x_val = float(split_line[1].strip())
        x_human.append(x_val)
        y_human.append(val_human)
        x_computer.append(x_val)
        y_computer.append(val_computer)
        x_agreement.append(x_val)
        y_agreement.append(val_agreement)
        x_phase.append(x_val)
        y_phase.append(phase)
        '''if not val_human == y_human[-1]:
            x_human.append(x_val)
            y_human.append(val_human)
        if not val_computer == y_computer[-1]:
            x_computer.append(x_val)
            y_computer.append(val_computer)
        if not val_agreement == y_agreement[-1]:
            x_agreement.append(x_val)
            y_agreement.append(val_agreement)
        if not phase == y_phase[-1]:
            x_phase.append(x_val)
            y_phase.append(phase)'''

    # Generate a mask on the agreement values that have a certain latency
    agreement_latency_mask, latency_list = list_mask_by_latency(
        x_agreement,
        latency=minimum_latency,
        remove_start_point=(latency_mode == 'all' or latency_mode == 'first'),
        remove_end_point=(latency_mode == 'all' or latency_mode == 'second'))

    x_interval_sum = 0
    sample_count = 0
    sample_wise_agreement_sum = 0.0
    time_wise_agreement_sum = 0
    # Use the mask to compute the running average, sample-wise agreement percentage, and time-wise agreement percentage
    for idx, mask_val in enumerate(agreement_latency_mask):
        if mask_val:
            if not (idx >= len(x_agreement) - 1):
                delta_t = x_agreement[idx + 1] - x_agreement[idx]
                x_interval_sum += delta_t
                time_wise_agreement_sum += y_agreement[idx] * delta_t
            else:  # We interpolate the final point delta-t by assuming it is the average
                delta_t = x_interval_sum / sample_count
                time_wise_agreement_sum += y_agreement[idx] * delta_t
                x_interval_sum += delta_t
            sample_count += 1
            sample_wise_agreement_sum += float(y_agreement[idx])
            agree_list.append(y_agreement[idx])
            if len(agree_list) > moving_average_window_size:
                agree_list.pop(0)
            x_agree_running_proportion.append(x_agreement[idx])
            y_agree_running_proportion.append(np.average(agree_list))
    sample_wise_agreement = sample_wise_agreement_sum / sample_count
    time_wise_agreement = time_wise_agreement_sum / x_interval_sum

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
    data.agreement_latency_mask = agreement_latency_mask
    data.x_agree_running_proportion = x_agree_running_proportion
    data.y_agree_running_proportion = y_agree_running_proportion
    data.moving_average_window_size = moving_average_window_size
    data.sample_wise_agreement = sample_wise_agreement
    data.time_wise_agreement = time_wise_agreement
    data.latency_list = latency_list
    data.abstract_phases = y_phase
    data.abstract_phase_keys = ['']

    return data


phase_key = ['Calibration PreT', 'Calibration', 'Habituation PreT', 'Habituation',
             'Test PreT', 'Test']

phase_numbers = [[1, 0, 4, 3, 42, 41, 45, 44],
                 [2, 5, 43, 46],
                 [7, 6, 10, 9, 13, 12, 16, 15, 19, 18, 22, 21, 25, 24, 28, 27, 31, 30, 48, 47, 51, 50, 54, 53, 57,
                  56, 60, 59, 63, 62, 66, 65, 69, 68, 72, 71],
                 [8, 11, 14, 17, 20, 23, 26, 29, 32, 49, 52, 55, 58, 61, 64, 67, 70, 73],
                 [34, 33, 38, 37, 75, 74, 79, 78],
                 [35, 36, 39, 40, 76, 77, 80, 81]]

phase_key_numbered = ['Calibration PreT_1', 'Calibration_1', 'Habituation PreT_1', 'Habituation_1',
                      'Test PreT_1', 'Test_1', 'Calibration PreT_2', 'Calibration_2', 'Habituation PreT_2',
                      'Habituation_2', 'Test PreT_2', 'Test_2']

phase_numbers_numbered = [[1, 0, 4, 3],
                          [2, 5],
                          [7, 6, 10, 9, 13, 12, 16, 15, 19, 18, 22, 21, 25, 24, 28, 27, 31, 30],
                          [8, 11, 14, 17, 20, 23, 26, 29, 32],
                          [34, 33, 38, 37],
                          [35, 36, 39, 40],
                          [42, 41, 45, 44],
                          [43, 46],
                          [48, 47, 51, 50, 54, 53, 57, 56, 60, 59, 63, 62, 66, 65, 69, 68, 72, 71],
                          [49, 52, 55, 58, 61, 64, 67, 70, 73],
                          [75, 74, 79, 78],
                          [76, 77, 80, 81]]


def parse_unity_log_files(input_filename,
                          state_filename,
                          config_filename,
                          moving_average_window_size=100,
                          minimum_latency=0.1,
                          latency_mode='all',
                          fill_holes=False,
                          filter_window_size=10):
    logging.info('filter_window_size={0}'.format(filter_window_size))
    fi = open(input_filename, 'rb')
    fs = open(state_filename, 'rb')
    fc = open(config_filename, 'rb')

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

    state_reference = ['down', 'up', 'left', 'right', 'none']
    tcp_state_lookup = ['d', 'c', 'r', 'l', '']
    keyboard_state_lookup = ['down', 'up', 'left', 'right', '']

    # TODO: This assumes there is one value at a time - not always true (for instance, if two buttons are pressed)
    def find_subval_in_val(val, substr, lookup, reference):
        try:
            found_value = [sx for sx in val if substr in sx][0].split(':')[1].strip()
        except IndexError:
            return -1
        found_value = found_value.replace('*EOF*', ',')  # Occasionally *EOF* can slip through on TCP.
        # This is a bug, but this is a simple fix until the bug is found.
        if ',' in found_value:
            found_value = found_value.split(',')[0]
        try:
            output_val = reference[lookup.index(found_value)]
        except ValueError:
            output_val = ''
        return output_val

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

    window = deque()

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

        if fill_holes and (val_computer == "none"):
            val_computer = y_computer[-1]
        if val_computer == -1:
            val_computer = y_computer[-1]
        if val_computer == 'off':
            val_computer = y_computer[-1]

        if filter_window_size is not None:
            window.append(val_computer)
            if len(window) > filter_window_size:
                window.popleft()
            counts = []
            for uy in state_reference:
                counts.append(window.count(uy))

        try:
            phase = int([s for s in state_list if 'Current Task Index' in s][0].split(':')[1].strip())
        except IndexError:
            phase = -1
        x_val = si_key

        if val_human == 'down':
            val_human = 'off'
        if val_computer == 'down':
            val_computer = 'off'

        val_agreement = val_human == val_computer
        x_human.append(x_val)
        y_human.append(val_human)
        x_computer.append(x_val)
        y_computer.append(val_computer)
        x_agreement.append(x_val)
        y_agreement.append(val_agreement)
        x_phase.append(x_val)
        y_phase.append(phase)
        '''if not val_human == y_human[-1]:
            x_human.append(x_val)
            y_human.append(val_human)
        if not val_computer == y_computer[-1]:
            x_computer.append(x_val)
            y_computer.append(val_computer)
        if not val_agreement == y_agreement[-1]:
            x_agreement.append(x_val)
            y_agreement.append(val_agreement)
        if not phase == y_phase[-1]:
            x_phase.append(x_val)
            y_phase.append(phase)'''

    # Generate a mask on the agreement values that have a certain latency
    agreement_latency_mask, latency_list = list_mask_by_latency(
        x_agreement,
        latency=minimum_latency,
        remove_start_point=(latency_mode == 'all' or latency_mode == 'first'),
        remove_end_point=(latency_mode == 'all' or latency_mode == 'second'))

    flattened_phase_numbers = [item for sublist in phase_numbers for item in sublist]

    x_interval_sum = 0
    sample_count = 0
    sample_wise_agreement_sum = 0.0
    time_wise_agreement_sum = 0
    time_wise_agreement_sum_by_phase = dict()
    time_wise_total_by_phase = dict()
    time_wise_agreement_by_phase = dict()
    for i in range(min(flattened_phase_numbers), max(flattened_phase_numbers)+1):
        time_wise_agreement_sum_by_phase[i] = 0
        time_wise_total_by_phase[i] = 0
        time_wise_agreement_by_phase[i] = 0

    # Use the mask to compute the running average, sample-wise agreement percentage, and time-wise agreement percentage
    for idx, mask_val in enumerate(agreement_latency_mask):
        if mask_val:
            if not (idx >= len(x_agreement) - 1):
                phase = y_phase[idx]
                delta_t = x_agreement[idx + 1] - x_agreement[idx]
                x_interval_sum += delta_t
                interval = y_agreement[idx] * delta_t
                time_wise_agreement_sum += interval
                if phase == -1:
                    logging.warning('Phase value not found for agreement value. (len(phase)={0}, len(agreement)={1}'
                                    .format(len(y_phase), len(x_agreement)))
                else:
                    time_wise_agreement_sum_by_phase[phase] += interval
                    time_wise_total_by_phase[phase] += delta_t
            else:  # We interpolate the final point delta-t by assuming it is the average
                phase = y_phase[idx-1]
                delta_t = x_interval_sum / sample_count
                interval = y_agreement[idx] * delta_t
                time_wise_agreement_sum += interval
                if phase == -1:
                    logging.warning('Phase value not found for agreement value. (len(phase)={0}, len(agreement)={1}'
                                    .format(len(y_phase), len(x_agreement)))
                else:
                    time_wise_agreement_sum_by_phase[phase] += interval
                    time_wise_total_by_phase[phase] += delta_t
                x_interval_sum += delta_t
            sample_count += 1
            sample_wise_agreement_sum += float(y_agreement[idx])
            agree_list.append(y_agreement[idx])
            if len(agree_list) > moving_average_window_size:
                agree_list.pop(0)
            x_agree_running_proportion.append(x_agreement[idx])
            y_agree_running_proportion.append(np.average(agree_list))
    sample_wise_agreement = sample_wise_agreement_sum / sample_count
    time_wise_agreement = time_wise_agreement_sum / x_interval_sum
    for i in range(min(flattened_phase_numbers), max(flattened_phase_numbers)):
        if time_wise_total_by_phase[i] == 0:
            time_wise_agreement_by_phase[i] = -1
        else:
            time_wise_agreement_by_phase[i] = time_wise_agreement_sum_by_phase[i]/time_wise_total_by_phase[i]

    abstract_phases = [None] * len(x_phase)
    abstract_phases_numbered = [None] * len(x_phase)
    for idx, p in enumerate(y_phase):
        abstract_phase = None
        abstract_phase_numbered = None
        for key, numbers in zip(phase_key, phase_numbers):
            if int(p) in numbers:
                abstract_phase = key
                break
        for key, numbers in zip(phase_key_numbered, phase_numbers_numbered):
            if int(p) in numbers:
                abstract_phase_numbered = key
                break
        abstract_phases[idx] = abstract_phase
        abstract_phases_numbered[idx] = abstract_phase_numbered

    participant_id = ''
    condition = ''
    for line in fc:
        if 'Participant ID: ' in line:
            participant_id = line.split('Participant ID: ')[-1]
        if 'Condition Configuration Filename: ' in line:
            condition = line.split('Condition Configuration Filename: ')[-1]

    # End Parser
    # Fill object with parser results and return
    data = type("iKidsDataObject", (object,), {})()
    data.x_human = x_human
    data.x_computer = x_computer
    data.x_agreement = x_agreement
    data.y_human = y_human
    data.y_computer = y_computer
    data.confusion_matrix = metrics.confusion_matrix(y_human, y_computer)
    data.confusion_matrix_labels = sorted(list(set(y_human+y_computer)))
    data.y_agreement = y_agreement
    data.x_phase = x_phase
    data.y_phase = y_phase
    data.agreement_latency_mask = agreement_latency_mask
    data.x_agree_running_proportion = x_agree_running_proportion
    data.y_agree_running_proportion = y_agree_running_proportion
    data.moving_average_window_size = moving_average_window_size
    data.sample_wise_agreement = sample_wise_agreement
    data.time_wise_agreement = time_wise_agreement
    data.latency_list = latency_list
    data.abstract_phases = abstract_phases
    data.abstract_phases_numbered = abstract_phases_numbered
    data.abstract_phase_keys = phase_key
    data.participant_id = participant_id.strip()
    data.condition = condition.strip()
    data.time_wise_agreement_by_phase = time_wise_agreement_by_phase
    data.time_wise_agreement_sum_by_phase = time_wise_agreement_sum_by_phase
    data.time_wise_total_by_phase = time_wise_total_by_phase

    return data
