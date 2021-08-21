import numpy as np
import samna
import sys
sys.path.append("/home/jingyue/aa_projects/samna_projects/ctxctl_contrib/")
from dynapse1constants import MAX_NUM_CAMS

def create_stdp_graph(model, spike_sink_debug=False):
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

    nodes = {
        'spike_filter': spike_filter_node,
        'onpre_trace_filter': onpre_trace_node,
        'onpost_trace_filter': onpost_trace_node,
        'onpre_trace_sink': onpre_trace_sink,
        'onpost_trace_sink': onpost_trace_sink
    }

    if spike_sink_debug:
        # pre and post spike filter
        pre_spike_filter_id = graph.add_filter_node("Dynapse1NeuronSelect")
        pre_spike_filter = graph.get_node(pre_spike_filter_id)
        post_spike_filter_id = graph.add_filter_node("Dynapse1NeuronSelect")
        post_spike_filter = graph.get_node(post_spike_filter_id)

        # create sink nodes
        pre_spike_sink = samna.BufferSinkNode_dynapse1_dynapse1_event()
        post_spike_sink = samna.BufferSinkNode_dynapse1_dynapse1_event()
        
        # connect spike filter to 2 pre and post spike filters
        graph.add_destination(spike_filter_node_id, graph.get_node_input(pre_spike_filter_id))
        graph.add_destination(spike_filter_node_id, graph.get_node_input(post_spike_filter_id))

        # connect filter to sink nodes
        graph.add_destination(pre_spike_filter_id, pre_spike_sink.get_input_channel())
        graph.add_destination(post_spike_filter_id, post_spike_sink.get_input_channel())

        spike_nodes = {
            'pre_spike_filter': pre_spike_filter,
            'post_spike_filter': post_spike_filter,
            'pre_spike_sink': pre_spike_sink,
            'post_spike_sink': post_spike_sink
        }
        nodes.update(spike_nodes)

    return graph, nodes

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