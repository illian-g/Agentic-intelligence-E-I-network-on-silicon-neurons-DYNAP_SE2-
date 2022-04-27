import numpy as np
import samna
import sys
sys.path.append("/home/jingyue/aa_projects/samna_projects/ctxctl_contrib/")
from dynapse1constants import MAX_NUM_CAMS

def create_stdp_graph(model, spike_sink_debug=False):
    """
    Create on pre and on post traces in which pre and post are the trigger neurons, respectively.
    Graph:
    
        source_node in model -> Dynapse1NeuronSelect filter_node
        -> Dynapse1NeuronTrace onpost and onpre trace filter_nodes
        -> onpost and onpre trace sink_nodes
    """  
    graph = samna.graph.EventFilterGraph()

    # create sink nodes
    onpost_trace_sink = samna.BasicSinkNode_dynapse1_dynapse1_trace()
    onpre_trace_sink = samna.BasicSinkNode_dynapse1_dynapse1_trace()

    _, spike_filter_node, onpre_trace_node, _ = graph.sequential([model.get_source_node(), "Dynapse1NeuronSelect", "Dynapse1NeuronTrace", onpre_trace_sink])
    _, onpost_trace_node, _ = graph.sequential([spike_filter_node, "Dynapse1NeuronTrace", onpost_trace_sink])


    nodes = {
        'spike_filter': spike_filter_node,
        'onpre_trace_filter': onpre_trace_node,
        'onpost_trace_filter': onpost_trace_node,
        'onpre_trace_sink': onpre_trace_sink,
        'onpost_trace_sink': onpost_trace_sink
    }

    if spike_sink_debug:
        """
        Dynapse1NeuronSelect filter_node above
        -> Dynapse1NeuronSelect pre and post spike filter_nodes
        -> pre and post spike sink_nodes
        """
        # create sink nodes
        pre_spike_sink = samna.BasicSinkNode_dynapse1_dynapse1_event()
        post_spike_sink = samna.BasicSinkNode_dynapse1_dynapse1_event()

        _, pre_spike_filter, _ = graph.sequential([spike_filter_node, "Dynapse1NeuronSelect", pre_spike_sink])
        _, post_spike_filter, _ = graph.sequential([spike_filter_node, "Dynapse1NeuronSelect", post_spike_sink])

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

def floatW2intW(float_w_plast, max_pre_count, rand_seed=None, unit=0.1):
    """
    Convert a float w_plast into a network.
    0.1 -> 1 connection
    """
    np.random.seed(rand_seed)
    int_w_plast = float_w_plast*(1/unit)
    int_w_plast = int_w_plast.astype(int)
    post_cam_counts = np.sum(int_w_plast, axis=0)

    for post in range(len(post_cam_counts)):
        if post_cam_counts[post] > max_pre_count:
            # number of cams that needs to be removed
            extra_cam_count = post_cam_counts[post]-max_pre_count

            pre_post_weights = int_w_plast[:,post]
            num_pres = len(pre_post_weights)

            # pruning of pre_post_weights: randomly remove extra_cam_count cams
            while(extra_cam_count>0):
                pre = np.random.randint(num_pres, size=1)
                if int_w_plast[pre,post] !=0:
                    int_w_plast[pre,post] -= 1
                    extra_cam_count -= 1

    np.random.seed(None)
    
    return int_w_plast