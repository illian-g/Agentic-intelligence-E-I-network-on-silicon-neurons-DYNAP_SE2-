import time
import random
import os
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns; sns.set()

import samna

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

def stdp(model, net_gen, pre_neuron_ids, post_neuron_ids, w_plast):
    """
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
    
    method = "increase_to" # increase_by increase_to
    trace_max = 1

    pre_tau = int(20*1e3) # in microsec
    post1_tau = int(40*1e3) # in microsec
    post2_tau = int(40*1e3) # in microsec
    nuEEpre = 0.005
    nuEEpost = 0.025
    wmaxEE = 1
    expEEpre = 0.2 # presynaptic weight dependence
    expEEpost = 0.2

    graph, spike_filter_node, \
    onpre_trace_node, onpost_trace_node, \
    onpre_trace_sink, onpost_trace_sink = create_stdp_graph(model)

    # configure filter nodes: which neurons to filter?
    spike_filter_node.set_neurons(pre_neuron_ids+post_neuron_ids)

    # on post: pre and post2 traces
    onpost_tau_list = [pre_tau for pre in pre_neuron_ids] + [post2_tau for post in post_neuron_ids]
    onpost_trace_node.set_neurons(pre_neuron_ids+post_neuron_ids, post_neuron_ids, onpost_tau_list)

    # on pre: post1 trace
    onpost_tau_list = [post1_tau for post in post_neuron_ids]
    onpre_trace_node.set_neurons(post_neuron_ids, pre_neuron_ids, onpost_tau_list)

    onpost_trace_node.set_trace_parameters(method, trace_max)
    onpre_trace_node.set_trace_parameters(method, trace_max)

    print("get_value_only_at_trigger ", onpost_trace_node.get_value_only_at_trigger())

    # start the graph
    graph.start()
    
    t0 = int(round(time.time() * 1e6)) # in microsec
    t1 = t0
    with open("./times.txt", mode='w', encoding='utf-8') as file_obj:
        file_obj.write(str(t1)+'\n')
    num = 0
    while(True):
        onpre_traces = onpre_trace_sink.get_events()
        onpost_traces = onpost_trace_sink.get_events()

        # on pre, contains post1 trace
        for onpre_trace in onpre_traces:
            # for each pre spike timestamp
            pre_neuron = onpre_trace.trigger_neuron
            i = pre_neuron_ids.index(pre_neuron)

            # check all its posts, update w_plast[i][j]
            for j in range(len(post_neuron_ids)):
                post_neuron = post_neuron_ids[j]
                post1 = onpre_trace.trace_map[post_neuron]

                delta_w = nuEEpre * post1 * w_plast[i][j]**expEEpre
                w_plast[i][j] -= delta_w
        
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

                delta_w = nuEEpost * pre * post2 * (wmaxEE - w_plast[i][j])**expEEpost
                w_plast[i][j] += delta_w
        
        # plot_w(w_plast)

        t2 = int(round(time.time() * 1e6)) # in us
        if t2-t1 >= 10*1e3:
            with open("./times.txt", mode='a', encoding='utf-8') as file_obj:
                file_obj.write(str(t2-t0)+','+str(num)+':'+str(t2-t1)+','+str((t2-t0)/num)+'\n')
        t1 = t2
        num += 1

        # convert w_plast to connections


    print("done")