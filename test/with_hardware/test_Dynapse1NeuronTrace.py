import time

import samna
import samna.dynapse1 as dyn1
import matplotlib.pyplot as plt
import numpy as np

import sys
# Note: change the path to where your lib files are
sys.path.append("/home/jingyue/aa_projects/samna_projects/ctxctl_contrib/")
import Dynapse1Utils as ut
from NetworkGenerator import Neuron, NeuronGroup, Synapses, add_synapses, NetworkGenerator

from params import gen_param_group_1core

# get the timestamps of some specific neurons
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

# get the timestamps of some specific neurons
def get_selected_traces(timed_traces, neuron_ids):
    """
    Filter out traces of selected neuron_ids.

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
            try:
                trace_value = trace_map[neuron_id]
                trace_values[i].append(trace_value)
                timestamps[i].append(timestamp)
            except ValueError as err:
                print(err, 'could be neuron is not in trace map.')
    
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
        ax.plot(timestamps[i], np.ones(len(timestamps[i]))*i, '.')
        for time in timestamps[i]:
            plt.axvline(time)
    
    if t_start != None and t_end != None:
        ax.set_xlim(t_start, t_end)

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
        ax.plot(timestamps[i], trace_values[i], '.-', label=str(i))
    
    if t_start != None and t_end != None:
        ax.set_xlim(t_start, t_end)

# open DYNAP-SE1 board to get Dynapse1Model
device_name = "dynapse1"

# open with GUI
store, gui_process = ut.open_dynapse1(device_name)

model = getattr(store, device_name)

# get Dynapse1 api from the model
api = model.get_dynapse1_api()

# ------------------- build network -------------------
net_gen = NetworkGenerator()

schip=0
score=0
sids = [1, 2]
spikegen_group = NeuronGroup(schip,score,sids,True)

chip=1
core=0
nids = [16, 17]
neuron_group = NeuronGroup(chip,core,nids)

# connect spikegen_group to neuron_group
syn = Synapses(spikegen_group, neuron_group, dyn1.Dynapse1SynType.AMPA, conn_type='one2one')
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
rate = 200
poisson_gen = model.get_poisson_gen()
poisson_gen.set_chip_id(chip)
poisson_gen.write_poisson_rate_hz(global_poisson_gen_ids[0], rate)

# check the configuration...
neuron_ids = [(chip,core,x) for x in nids]
config = model.get_configuration()
for nid in neuron_ids:
    neuron = ut.get_neuron_from_config(config, nid[0], nid[1], nid[2])
    print("------------Neuron", nid,"------------")
    print("Cams:")
    ut.print_neuron_synapses(neuron, range(12))
    print("Srams:")
    ut.print_neuron_destinations(neuron)

# set parameters
paramGroup = gen_param_group_1core()
for chip in range(4):
    for core in range(4):
        model.update_parameter_group(paramGroup, chip, core)

# ---------------- create a graph ----------------
# create a graph: source node to 2 filter nodes, one neuron select, one neuron trace.
graph = samna.graph.EventFilterGraph()

# create sink nodes
spike_sink_node = samna.BufferSinkNode_dynapse1_dynapse1_event()
trace_sink_node = samna.BufferSinkNode_dynapse1_dynapse1_trace()

# create and add filter nodes to graph
spike_filter_node_id = graph.add_filter_node("Dynapse1NeuronSelect")
trace_filter_node_id = graph.add_filter_node("Dynapse1NeuronTrace")
spike_filter_node = graph.get_node(spike_filter_node_id)
trace_filter_node = graph.get_node(trace_filter_node_id)

# connect source node to filter nodes
model.get_source_node().add_destination(graph.get_node_input(spike_filter_node_id))
model.get_source_node().add_destination(graph.get_node_input(trace_filter_node_id))

# connect filter nodes to sink nodes
graph.add_destination(spike_filter_node_id, spike_sink_node.get_input_channel())
graph.add_destination(trace_filter_node_id, trace_sink_node.get_input_channel())

# configure filter node: which neurons to filter?
spike_filter_node.set_neurons(neuron_ids)
trace_filter_node.set_neurons(neuron_ids)
tau = int(200*1e3) # 50*1e3 in microsec
method = "increase_by_1" # increase_by_1 increase_to_1
trace_filter_node.set_trace_parameters(tau, method)
# ---------------- create a graph ----------------

# start the poisson gen
poisson_gen.start()
# start the graph
graph.start()

print(trace_filter_node.get_tau(), trace_filter_node.get_method())

api.reset_timestamp()
# clear the buffer
spike_sink_node.get_events()
trace_sink_node.get_events()

# get spikes every 2 seconds
time.sleep(2)
spikes = spike_sink_node.get_events()
timed_traces = trace_sink_node.get_events()

fig = plt.figure()
plot_raster(spikes, neuron_ids)
plot_trace(timed_traces, [neuron_ids[0]])
plt.show()


graph.stop()
poisson_gen.stop()

print("Example finished")

# close Dynapse1

# close with GUI
ut.close_dynapse1(store, device_name, gui_process)