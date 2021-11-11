import numpy as np
import json

class TripletStdp:
    """
    Implementation of all to all plastic connections between pre and post population, including trace graph setup and algorithm implementation with retrieved traces. http://arxiv.org/abs/1608.08267.

    Triplet STDP is implemented, but can be replaced with other Hebbian-like learning algorithms

    Algorithm:
        On pre: neuron select node of pre -> pre timestamps
            update post_trace1: post_trace1 values at pre timestamps

            pre = 1.0
            delta_w = nuEEpre * post1 * w_plast**expEEpre
            w_plast = clip(w_plast - delta_w, 0, wmaxEE)

        On post: neuron select node of post -> post timestamps
            update pre_trace: pre_trace values at post timestamps
            update post_trace2: post_trace2 values at post timestamps.

            post2before = post2
            delta_w = nuEEpost * pre * post2before * (wmaxEE - w_plast)**expEEpost
            w_plast = clip(w_plast + delta_w, 0, wmaxEE)
            post1 = 1.0
            post2 = 1.0
    
    Parameters:
        method = "increase_to", # "increase_by",  "increase_to"
        trace_max = 1, # maximum trace value
        pre_tau = 20, # time constant of trace pre, millisec in JSON file
        post1_tau = 40, # time constant of trace post1, millisec in JSON file
        post2_tau = 40, # time constant of trace post2, millisec in JSON file
        nuEEpre = 0.005, # presynaptic spike learning rate
        nuEEpost = 0.025, # postsynaptic spike learning rate
        wmaxEE = 1, # maximum weight
        expEEpre = 0.2, # presynaptic weight dependence
        expEEpost = 0.2 # postsynaptic weight dependence
    """ 
    def __init__(self,
                 param_file):

        with open(param_file) as json_file:
            data = json.load(json_file)

        self.method = data["method"]
        self.trace_max = data["trace_max"]

        self.pre_tau = int(data["pre_tau"] * 1e3) # millisec to microsec
        self.post1_tau = int(data["post1_tau"] * 1e3)
        self.post2_tau = int(data["post2_tau"] * 1e3)
        self.nuEEpre = data["nuEEpre"]
        self.nuEEpost = data["nuEEpost"]
        self.wmaxEE = data["wmaxEE"]
        self.expEEpre = data["expEEpre"]
        self.expEEpost = data["expEEpost"]

    def triplet_stdp_algorithm(self, w_plast, onpre_traces, onpost_traces, pre_neuron_ids, post_neuron_ids):
        """
        The implementation of triplet stdp algorithm given Dynapse1traces retrieved from the trace graph.
        """
        # on pre, LTD, contains post1 trace
        for onpre_trace in onpre_traces:
            # for each pre spike timestamp
            pre_neuron = onpre_trace.trigger_neuron
            i = pre_neuron_ids.index(pre_neuron)

            # check all its posts, update w_plast[i][j]
            for j in range(len(post_neuron_ids)):
                post_neuron = post_neuron_ids[j]
                post1 = onpre_trace.trace_map[post_neuron]

                delta_w = self.nuEEpre * post1 * w_plast[i][j]**self.expEEpre
                w_plast[i][j] = np.clip(w_plast[i][j]-delta_w, 0, self.wmaxEE)
        
        # on post, LTP, contains pre and post2 trace
        for onpost_trace in onpost_traces:
            # for each post spike timestamp
            post_neuron = onpost_trace.trigger_neuron
            j = post_neuron_ids.index(post_neuron)

            # get post2 trace of this post neuron
            post2 = onpost_trace.trace_map[post_neuron]

            # check all its pre traces, update w_plast[i][j]
            for i in range(len(pre_neuron_ids)):
                pre_neuron = pre_neuron_ids[i]
                pre = onpost_trace.trace_map[pre_neuron]

                delta_w = self.nuEEpost * pre * post2 * (self.wmaxEE - w_plast[i][j])**self.expEEpost
                w_plast[i][j] = np.clip(w_plast[i][j]+delta_w, 0, self.wmaxEE)

        return w_plast
        
    def set_triplet_stdp_graph(self, spike_filter_node, onpre_trace_node, onpost_trace_node, pre_neuron_ids, post_neuron_ids):
        """
        Set up trace graph to calculate the traces for selected neurons.
        """
        # configure filter nodes: which neurons to filter
        spike_filter_node.set_neurons(pre_neuron_ids+post_neuron_ids)

        # on post: pre and post2 traces
        onpost_tau_list = [self.pre_tau for pre in pre_neuron_ids] + [self.post2_tau for post in post_neuron_ids]
        onpost_trace_node.set_neurons(pre_neuron_ids+post_neuron_ids, post_neuron_ids, onpost_tau_list)

        # on pre: post1 trace
        onpost_tau_list = [self.post1_tau for post in post_neuron_ids]
        onpre_trace_node.set_neurons(post_neuron_ids, pre_neuron_ids, onpost_tau_list)

        onpost_trace_node.set_trace_parameters(self.method, self.trace_max)
        onpre_trace_node.set_trace_parameters(self.method, self.trace_max)