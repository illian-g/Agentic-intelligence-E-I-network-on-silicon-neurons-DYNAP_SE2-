import numpy as np
import samna
import sys
sys.path.append("/home/jingyue/aa_projects/samna_projects/ctxctl_contrib/")
from dynapse1constants import MAX_NUM_CAMS

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

def get_trace_value(traces, timestamp):
    """
    Get 1 single trace value from a list of Dynapse1Traces
    """
    for trace in traces:
        if trace.timestamp == timestamp:
            return trace
    
    if timestamp < traces[0].timestamp:
        print("Timestamp%i not found, < list start %i." % (timestamp, traces[0].timestamp))
    if timestamp > traces[-1].timestamp:
        print("Timestamp %i not found, > list end %i." % (timestamp, traces[-1].timestamp))
    return None

def create_stdp_graph(model):
    """
    Create on pre and on post traces in which pre and post are the trigger neurons, respectively.
    """  
    graph = samna.graph.EventFilterGraph()

    # create and add filter nodes to graph
    # pre+post spike filter
    spike_filter_node_id = graph.add_filter_node("Dynapse1NeuronSelect")
    spike_filter_node = graph.get_node(spike_filter_node_id)

    onpost_trace_node_id = graph.add_filter_node("Dynapse1NeuronTrace")
    onpost_trace_node = graph.get_node(onpost_trace_node_id)

    onpre_trace_node_id = graph.add_filter_node("Dynapse1NeuronTrace")
    onpre_trace_node = graph.get_node(onpre_trace_node_id)

    # create sink nodes
    onpost_trace_sink = samna.BufferSinkNode_dynapse1_dynapse1_trace()
    onpre_trace_sink = samna.BufferSinkNode_dynapse1_dynapse1_trace()

    # connect source node to spike filter node
    model.get_source_node().add_destination(graph.get_node_input(spike_filter_node_id))

    # connect spike filter to 2 trace nodes
    graph.add_destination(spike_filter_node_id, graph.get_node_input(onpost_trace_node_id))
    graph.add_destination(spike_filter_node_id, graph.get_node_input(onpre_trace_node_id))

    # connect 2 trace nodes to 2 sink nodes
    graph.add_destination(onpost_trace_node_id, onpost_trace_sink.get_input_channel())
    graph.add_destination(onpre_trace_node_id, onpre_trace_sink.get_input_channel())

    return graph, spike_filter_node, onpre_trace_node, onpost_trace_node, onpre_trace_sink, onpost_trace_sink

def bad_traces(onpre_traces, onpost_traces, max_num=10, max_time_interval=3*1e5):
    """
    To handle the abnormal traces after restart of stdp.
    Bad traces should be dropped, not processed anymore.
    Traces are bad if
        1) not synchronized: time difference between the traces is too large.
        2) too many traces received which will take too long to process.
    
    Parameters:
        max_num: int
        max_time_interval: int, in microsecond
    """
    if len(onpre_traces)>max_num or len(onpost_traces)>max_num:
        return True

    start_times = []
    end_times = []
    if len(onpre_traces):
        start_times.append(onpre_traces[0].timestamp)
        end_times.append(onpre_traces[-1].timestamp)
    if len(onpost_traces):
        start_times.append(onpost_traces[0].timestamp)
        end_times.append(onpost_traces[-1].timestamp)

    for start in start_times:
        for end in end_times:
            if (end-start)>max_time_interval:
                return True

    return False

def floatW2intW(float_w_plast, max_pre_count, unit=0.1):
    """
    Convert a float w_plast into a network.
    0.1 -> 1 connection
    """
    int_w_plast = float_w_plast*(1/unit)
    int_w_plast = int_w_plast.astype(int)
    post_cam_counts = np.sum(int_w_plast, axis=0)

    for post in range(len(post_cam_counts)):
        if post_cam_counts[post] > max_pre_count:
            pre_post_weights = int_w_plast[:,post]
            max_pre = np.argmax(pre_post_weights)

            # punish the largest weight pre,post connection
            int_w_plast[max_pre][post] = min(int_w_plast[max_pre][post]-1, max_pre_count) 

    return int_w_plast