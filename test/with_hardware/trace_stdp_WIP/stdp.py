import time
import random
import os
import _thread
import numpy as np

import samna

import triplet_stdp_details as trip
from stdp_utils import create_stdp_graph, bad_traces

max_trace_num=10
max_time_interval=3*1e5

class Stdp:
    """
    A class which implements "realtime, onchip" STDP learning algorithm between a pre and a post neuron population.
    """
    def __init__(self, model, net_gen, pre_neuron_ids, post_neuron_ids, w_plast, algorithm='triplet_stdp'):
        self.model = model
        self.net_gen = net_gen
        self.pre_neuron_ids = pre_neuron_ids
        self.post_neuron_ids = post_neuron_ids
        self.w_plast = w_plast

        # create trace graph
        self.graph, self.spike_filter_node, \
        self.onpre_trace_node, self.onpost_trace_node, \
        self.onpre_trace_sink, self.onpost_trace_sink = create_stdp_graph(model)

        self.algorithm = algorithm

        # set trace graph for the required traces
        if self.algorithm == 'triplet_stdp':
            trip.set_triplet_stdp_graph(self.spike_filter_node, self.onpre_trace_node, self.onpost_trace_node, self.pre_neuron_ids, self.post_neuron_ids)
        else:
            print("Wrong algorithm name. Learning setup failed.")

        self.stdp_on = False
    
    def start_stdp(self):
        if not self.stdp_on:
            self.graph.start()
            
            self.stdp_on = True

            _thread.start_new_thread(self.__run_stdp, ())

    def stop_stdp(self, stop_graph=False):
        # terminate the stdp thread while loop
        self.stdp_on = False

        if stop_graph:
            self.graph.stop()
        
    def __run_stdp(self):
        # empty the buffer
        onpre_traces = self.onpre_trace_sink.get_events()
        onpost_traces = self.onpost_trace_sink.get_events()

        while(self.stdp_on):
            onpre_traces = self.onpre_trace_sink.get_events()
            onpost_traces = self.onpost_trace_sink.get_events()

            # drop bad traces, do not touch w_plast using them
            if bad_traces(onpre_traces, onpost_traces, max_trace_num, max_time_interval):
                continue
            
            # update w_plast using a specific learning algorithm
            if self.algorithm == 'triplet_stdp':
                self.w_plast = trip.triplet_stdp_algorithm(self.w_plast, onpre_traces, onpost_traces, self.pre_neuron_ids, self.post_neuron_ids)
            else:
                print("Wrong algorithm name. Learning setup failed.")
            
            # TODO: change the connections on chip using w_plast