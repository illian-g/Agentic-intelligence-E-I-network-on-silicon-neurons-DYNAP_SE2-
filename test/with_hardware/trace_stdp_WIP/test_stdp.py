import samna
import samna.dynapse1 as dyn1

import time
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns; sns.set()

from stdp import Stdp

import sys
# Note: change the path to where your lib files are
sys.path.append("/home/jingyue/aa_projects/samna_projects/ctxctl_contrib/")
import Dynapse1Utils as ut
from NetworkGenerator import Neuron, NeuronGroup, Synapses, add_synapses, NetworkGenerator

from params import gen_param_group

def get_selected_timestamps(spikes, neuron_ids):
    """
    Filter out timestamps of selected neuron_ids.

    Parameters
    -----------
    spikes : list[Dynapse1Spike]
        result of sink_node.get_events()
    neuron_ids : list[(int,int,int)]
        neuron_ids
    
    Returns
    ---------
    timestamps : list[list[int]]
        spike timestamps of selected neurons. The list indexing is the same as
        the neuron indexing in the list neuron_ids.
    """
    if len(set(neuron_ids)) != len(neuron_ids):
        raise Exception("Duplicate neuron ids exist!")

    num_neurons = len(neuron_ids)
    timestamps = []
    for i in range(num_neurons):
        timestamps.append([])
    
    for spike in spikes:
        spike_neuron = (spike.chip_id, spike.core_id, spike.neuron_id)
        try:
            # if spike_neuron in neuron_ids, add timestamp to corresponding timestamp list
            id_in_list = neuron_ids.index(spike_neuron)
            timestamps[id_in_list].append(spike.timestamp)
        except ValueError:
            # if not, do nothing
            pass
    
    return timestamps

def get_selected_traces(timed_traces, neuron_ids):
    """
    Filter out timestamps and trace_values of selected neuron_ids.

    Parameters
    -----------
    timed_traces : list[Dynapse1Trace]
        result of sink_node.get_events()
    neuron_ids : list[(int,int,int)]
        neuron_ids
    
    Returns
    ---------
    timestamps : list[list[int]]
        spike timestamps of selected neurons. The list indexing is the same as
        the neuron indexing in the list neuron_ids.
    trace_values : list[list[float]]
        trace values at spike times. The list indexing is the same as
        the neuron indexing in the list neuron_ids.
    """
    if len(set(neuron_ids)) != len(neuron_ids):
        raise Exception("Duplicate neuron ids exist!")

    num_neurons = len(neuron_ids)
    timestamps = []
    for i in range(num_neurons):
        timestamps.append([])
    trace_values = []
    for i in range(num_neurons):
        trace_values.append([])
    
    # tracemap over time
    for trace in timed_traces:
        trace_map = trace.trace_map
        timestamp = trace.timestamp

        for i in range(num_neurons):
            neuron_id = neuron_ids[i]
            trace_value = trace_map.get(neuron_id)
            if trace_value != None:
                trace_values[i].append(trace_value)
                timestamps[i].append(timestamp)
    
    return timestamps, trace_values

# plot and compare the spikes and traces

# plot the raster
def plot_raster(spikes, neuron_ids, t_start=None, t_end=None):
    """
    plot the raster of neuron_ids from collected spikes.
    spikes: spike
    """
    if len(set(neuron_ids)) != len(neuron_ids):
        raise Exception("Duplicate neuron ids exist!")
    
    timestamps = get_selected_timestamps(spikes, neuron_ids)

    ax = plt.subplot()
    for i in range(len(neuron_ids)):
        print(i, timestamps[i])
        ax.plot(timestamps[i], np.ones(len(timestamps[i]))*i, '.', label=str(i)+': '+str(neuron_ids[i]))
        # for time in timestamps[i]:
        #     plt.axvline(time)
    
    if t_start != None and t_end != None:
        ax.set_xlim(t_start, t_end)
    
    ax.legend()

# plot traces
def plot_trace(timed_traces, neuron_ids, t_start=None, t_end=None):
    """
    plot the raster of neuron_ids from collected spikes.
    spikes: spike
    """
    if len(set(neuron_ids)) != len(neuron_ids):
        raise Exception("Duplicate neuron ids exist!")
    
    timestamps, trace_values = get_selected_traces(timed_traces, neuron_ids)

    ax = plt.subplot()
    for i in range(len(neuron_ids)):
        print(timestamps[i], trace_values[i])
        ax.plot(timestamps[i], trace_values[i], '.-', label=str(i)+': '+str(neuron_ids[i]))
    
    if t_start != None and t_end != None:
        ax.set_xlim(t_start, t_end)
    
    ax.legend()

# open DYNAP-SE1 board to get Dynapse1Model
device_name = "dynapse1"

# open with GUI
store, gui_process = ut.open_dynapse1(device_name)
# store = ut.open_dynapse1(device_name, gui=False, sender_port=12345, receiver_port=12346)

model = getattr(store, device_name)

# set parameters
paramGroup = gen_param_group()
paramGroup.param_map["PS_WEIGHT_EXC_S_N"].coarse_value = 0
paramGroup.param_map["PS_WEIGHT_EXC_S_N"].fine_value = 0
for chip in range(4):
    for core in range(4):
        model.update_parameter_group(paramGroup, chip, core)

# get Dynapse1 api from the model
api = model.get_dynapse1_api()

# ------------------- build network -------------------
net_gen = NetworkGenerator()

schip=0
score=0
sids = [1, 2, 3]
spikegen_group = NeuronGroup(schip,score,sids,True)

chip=1
core=0
pre_nids = [16, 17, 18]
post_nids = [32, 33, 34]
pre_neuron_group = NeuronGroup(chip,core,pre_nids)
post_neuron_group = NeuronGroup(chip,core,post_nids)

# connect spikegen_group to pre_neuron_group
syn = Synapses(spikegen_group, pre_neuron_group, dyn1.Dynapse1SynType.AMPA, conn_type='one2one')
add_synapses(net_gen, syn)
syn = Synapses(spikegen_group, post_neuron_group, dyn1.Dynapse1SynType.AMPA, conn_type='one2one')
add_synapses(net_gen, syn)

# print the network so you can double check (optional)
print(net_gen.network)

# make a dynapse1config using the network
new_config = net_gen.make_dynapse1_configuration()

# apply the configuration
model.apply_configuration(new_config)
# ------------------- build network -------------------

# set up Poisson spike generators
spikegen_ids = [(schip,score,x) for x in sids]
global_poisson_gen_ids = ut.get_global_id_list(spikegen_ids)
poisson_gen = model.get_poisson_gen()
poisson_gen.set_chip_id(chip)
poisson_gen.write_poisson_rate_hz(global_poisson_gen_ids[0], 50)
poisson_gen.write_poisson_rate_hz(global_poisson_gen_ids[1], 200)
poisson_gen.write_poisson_rate_hz(global_poisson_gen_ids[2], 50)

# check the configuration...
pre_neuron_ids = [(chip,core,x) for x in pre_nids]
post_neuron_ids = [(chip,core,x) for x in post_nids]

poisson_gen.start()

low_init_w = 0.1
w_plast = np.ones((len(pre_neuron_ids), len(post_neuron_ids)))*low_init_w

stdp = Stdp(model, net_gen, pre_neuron_ids, post_neuron_ids, w_plast, algorithm='triplet_stdp')

stdp.start_stdp()

time.sleep(60*20) # learn 20 min

stdp.stop_stdp()

ut.close_dynapse1(store, device_name, gui_process)