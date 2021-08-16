import time
import random
import os
import _thread
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns; sns.set()

import samna

import triplet_stdp_details as trip

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

def plot_w(w_plast, figpath="./w"):
    isExists=os.path.exists(figpath)
    if not isExists:
        os.makedirs(figpath)
        
    fig = plt.figure(figsize=(14,12))
    sns.heatmap(w_plast)
    plt.title("w_plast")
    plt.xlabel("post")
    plt.ylabel("pre")
    fig.savefig(figpath+"/w"+str(int(round(time.time() * 1000))))
    del fig

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

def bad_traces(onpre_traces, onpost_traces):
    """
    To handle the abnormal traces after restart of stdp.
    Bad traces should be dropped, not processed anymore.
    Traces are bad if
        1) not synchronized: time difference between the traces are too large.
        2) too many traces received which will take too long to process.
    """

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

    def stop_stdp(self):
        # terminate the stdp thread while loop
        self.stdp_on = False

        # self.graph.stop()
        
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
            num_pre_traces = len(onpre_traces)
            num_post_traces = len(onpost_traces)
            if num_pre_traces:
                if num_pre_traces>10 or (onpre_traces[-1].timestamp-onpre_traces[0].timestamp) > 3*1e5:
                    with open(filename, mode='a', encoding='utf-8') as file_obj:
                        file_obj.write('pre'+str(num_pre_traces)+','+str(onpre_traces[0].timestamp)+','+str(onpre_traces[-1].timestamp)+','+str(onpre_traces[-1].timestamp-onpre_traces[0].timestamp)+'|')
                    with open(filename, mode='a', encoding='utf-8') as file_obj:
                        file_obj.write(str(t2-t1)+','+str(int((t2-t0)/num))+'\n')
            if num_post_traces:
                if num_post_traces>10 or (onpost_traces[-1].timestamp-onpost_traces[0].timestamp) > 3*1e5:
                    with open(filename, mode='a', encoding='utf-8') as file_obj:
                        file_obj.write('post'+str(num_post_traces)+','+str(onpost_traces[0].timestamp)+','+str(onpost_traces[-1].timestamp)+','+str(onpost_traces[-1].timestamp-onpost_traces[0].timestamp)+'|')
                    with open(filename, mode='a', encoding='utf-8') as file_obj:
                            file_obj.write(str(t2-t1)+','+str(int((t2-t0)/num))+'\n')

            # if (t2-t1)/1e3 >= 10: # > 10ms
            #     with open(filename, mode='a', encoding='utf-8') as file_obj:
            #         file_obj.write(str(num)+':'+str(num_traces)+','+str(t2-t1)+','+str(int((t2-t0)/num))+'\n')
            t1 = t2