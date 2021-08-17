import time
import random
import os
import _thread
import numpy as np

import samna

import triplet_stdp_details as trip
from stdp_utils import create_stdp_graph, bad_traces

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

        t0 = int(round(time.time() * 1e6)) # in microsec
        t1 = t0
        filename = './results/start_graph_times.txt'
        with open(filename, mode='w', encoding='utf-8') as file_obj:
            file_obj.write('Unit: micsec. List all rounds that take longer than 10 millisec.\n'+\
                'No.: num_traces, single_duration, average_single_duration\n')
        num = 0
        
        while(self.stdp_on):
            onpre_traces = self.onpre_trace_sink.get_events()
            onpost_traces = self.onpost_trace_sink.get_events()

            # handle exception: the time difference between the min and max trace timestamp

            if self.algorithm == 'triplet_stdp':
                self.w_plast = trip.triplet_stdp_algorithm(self.w_plast, onpre_traces, onpost_traces, self.pre_neuron_ids, self.post_neuron_ids)
            else:
                print("Wrong algorithm name. Learning setup failed.")

            t2 = int(round(time.time() * 1e6)) # in us
            num += 1

            if bad_traces(onpre_traces, onpost_traces, max_num=12, max_time_interval=3*1e5):
                with open(filename, mode='a', encoding='utf-8') as file_obj:
                    file_obj.write('pre '+str(len(onpre_traces))+','+str(onpre_traces[0].timestamp)+','+str(onpre_traces[-1].timestamp)+','+str(onpre_traces[-1].timestamp-onpre_traces[0].timestamp)+'; ')
                        
                    file_obj.write('post '+str(len(onpost_traces))+','+str(onpost_traces[0].timestamp)+','+str(onpost_traces[-1].timestamp)+','+str(onpost_traces[-1].timestamp-onpost_traces[0].timestamp)+'|')

                    file_obj.write(str(t2-t1)+','+str(int((t2-t0)/num))+'\n')

            # if (t2-t1)/1e3 >= 10: # > 10ms
            #     with open(filename, mode='a', encoding='utf-8') as file_obj:
            #         file_obj.write(str(num)+':'+str(num_traces)+','+str(t2-t1)+','+str(int((t2-t0)/num))+'\n')
            t1 = t2