import time
import random
import os
import _thread
import numpy as np

import samna

from stdp_algorithms.triplet_stdp_details import TripletStdp
from stdp_utils import create_stdp_graph, bad_traces

class Stdp:
    """A class which implements "realtime, onchip" learning algorithm between
    a pre and a post neuron population.

    Args:

    Attributes:
    
    """
    def __init__(self, model, net_gen, pre_neuron_ids, post_neuron_ids, w_plast, param_file, algorithm='triplet_stdp', new_thread = True, remove_bad_traces=False, stop_graph=False, spike_sink_debug=False, max_trace_num=10, max_time_interval=3*1e5):
        self.model = model
        self.net_gen = net_gen
        self.pre_neuron_ids = pre_neuron_ids
        self.post_neuron_ids = post_neuron_ids
        self.w_plast = w_plast
        self.algorithm = algorithm

        self.new_thread = new_thread
        self.stop_graph = stop_graph
        self.remove_bad_traces = remove_bad_traces
        if remove_bad_traces:
            self.max_trace_num = max_trace_num
            self.max_time_interval = max_time_interval
        self.spike_sink_debug = spike_sink_debug

        self.graph, self.nodes = create_stdp_graph(model, spike_sink_debug)

        # set trace graph for the required traces
        if self.algorithm == 'triplet_stdp':
            self.trip = TripletStdp(param_file)
            self.trip.set_triplet_stdp_graph(self.nodes['spike_filter'], self.nodes['onpre_trace_filter'], self.nodes['onpost_trace_filter'], self.pre_neuron_ids, self.post_neuron_ids)

            if self.spike_sink_debug:
                self.nodes['pre_spike_filter'].set_neurons(pre_neuron_ids)
                self.nodes['post_spike_filter'].set_neurons(post_neuron_ids)

        else:
            print("Wrong algorithm name. Learning setup failed.")

        self.stdp_on = False
    
    def start_stdp(self):
        if not self.stdp_on:
            self.graph.start()
            
            self.stdp_on = True

            if self.new_thread:
                _thread.start_new_thread(self.__run_stdp, ())
            else:
                self.__run_stdp()

    def stop_stdp(self):
        # terminate the stdp thread while loop
        self.stdp_on = False

        if self.stop_graph:
            self.graph.stop()
    
    def get_traces(self):
        onpre_traces = self.nodes['onpre_trace_sink'].get_events()
        onpost_traces = self.nodes['onpost_trace_sink'].get_events()
        return onpre_traces, onpost_traces
    
    def get_spikes_debug(self):
        if self.spike_sink_debug:
            pre_spikes = self.nodes['pre_spike_sink'].get_events()
            post_spikes = self.nodes['post_spike_sink'].get_events()
            return pre_spikes, post_spikes
        else:
            return False
        
    def __run_stdp(self):
        # empty the buffer
        onpre_traces, onpost_traces = self.get_traces()

        while(self.stdp_on):
            onpre_traces, onpost_traces = self.get_traces()

            # drop bad traces, do not touch w_plast using them
            if self.remove_bad_traces and bad_traces(onpre_traces, onpost_traces, self.max_trace_num, self.max_time_interval):
                continue
            
            if len(onpre_traces) or len(onpost_traces):
                # update w_plast using a specific learning algorithm
                if self.algorithm == 'triplet_stdp':
                    self.trip.triplet_stdp_algorithm(self.w_plast, onpre_traces, onpost_traces, self.pre_neuron_ids, self.post_neuron_ids)
                else:
                    print("Wrong algorithm name. Learning setup failed.")