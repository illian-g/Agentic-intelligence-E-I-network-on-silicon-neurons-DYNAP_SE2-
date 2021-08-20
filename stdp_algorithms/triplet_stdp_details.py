import numpy as np

class TripletStdp:
    """
    All to all plastic connections between pre and post population.

    Triplet STDP is implemented, but can be replaced with other Hebbian-like learning algorithms

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
    """ 
    def __init__(self,
                 method = "increase_to", # increase_by increase_to
                 trace_max = 1, 
                 pre_tau = int(20*1e3), # in microsec
                 post1_tau = int(40*1e3), # in microsec
                 post2_tau = int(40*1e3), # in microsec
                 nuEEpre = 0.005, 
                 nuEEpost = 0.025, 
                 wmaxEE = 1, 
                 expEEpre = 0.2, # presynaptic weight dependence
                 expEEpost = 0.2):

        self.method = method
        self.trace_max = trace_max

        self.pre_tau = pre_tau
        self.post1_tau = post1_tau
        self.post2_tau = post2_tau
        self.nuEEpre = nuEEpre
        self.nuEEpost = nuEEpost
        self.wmaxEE = wmaxEE
        self.expEEpre = expEEpre
        self.expEEpost = expEEpost

    def triplet_stdp_algorithm(self, w_plast, onpre_traces, onpost_traces, pre_neuron_ids, post_neuron_ids):
        # print(len(onpre_traces), len(onpost_traces))
        # on pre, contains post1 trace
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
        
        # on post, contains pre and post2 trace
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
        # configure filter nodes: which neurons to filter?
        spike_filter_node.set_neurons(pre_neuron_ids+post_neuron_ids)

        # on post: pre and post2 traces
        onpost_tau_list = [self.pre_tau for pre in pre_neuron_ids] + [self.post2_tau for post in post_neuron_ids]
        onpost_trace_node.set_neurons(pre_neuron_ids+post_neuron_ids, post_neuron_ids, onpost_tau_list)

        # on pre: post1 trace
        onpost_tau_list = [self.post1_tau for post in post_neuron_ids]
        onpre_trace_node.set_neurons(post_neuron_ids, pre_neuron_ids, onpost_tau_list)

        onpost_trace_node.set_trace_parameters(self.method, self.trace_max)
        onpre_trace_node.set_trace_parameters(self.method, self.trace_max)