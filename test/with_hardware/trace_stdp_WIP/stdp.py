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
    
    # print("Dynapse1Trace with timestamp not found in the trace list.")
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

def stdp(model, net_gen, pre_neuron_ids, post_neuron_ids, w_plast):
    
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

    # ---------------- create a graph ----------------
    # create a graph: source node to 2 filter nodes, one neuron select, one neuron trace.
    graph = samna.graph.EventFilterGraph()

    # create and add filter nodes to graph
    # pre+post spike filter
    spike_filter_node_id = graph.add_filter_node("Dynapse1NeuronSelect")
    spike_filter_node = graph.get_node(spike_filter_node_id)

    # pre trace
    pre_trace_node_id = graph.add_filter_node("Dynapse1NeuronTrace")
    pre_trace_node = graph.get_node(pre_trace_node_id)

    # post1 trace
    post1_trace_node_id = graph.add_filter_node("Dynapse1NeuronTrace")
    post1_trace_node = graph.get_node(post1_trace_node_id)

    # post2 trace
    post2_trace_node_id = graph.add_filter_node("Dynapse1NeuronTrace")
    post2_trace_node = graph.get_node(post2_trace_node_id)

    # create sink nodes
    pre_trace_sink = samna.BufferSinkNode_dynapse1_dynapse1_trace()
    post1_trace_sink = samna.BufferSinkNode_dynapse1_dynapse1_trace()
    post2_trace_sink = samna.BufferSinkNode_dynapse1_dynapse1_trace()

    # connect source node to spike filter node
    model.get_source_node().add_destination(graph.get_node_input(spike_filter_node_id))

    # connect spike filter to 3 trace nodes
    graph.add_destination(spike_filter_node_id, graph.get_node_input(pre_trace_node_id))
    graph.add_destination(spike_filter_node_id, graph.get_node_input(post1_trace_node_id))
    graph.add_destination(spike_filter_node_id, graph.get_node_input(post2_trace_node_id))

    # connect 3 trace nodes to 3 sink nodes
    graph.add_destination(pre_trace_node_id, pre_trace_sink.get_input_channel())
    graph.add_destination(post1_trace_node_id, post1_trace_sink.get_input_channel())
    graph.add_destination(post2_trace_node_id, post2_trace_sink.get_input_channel())

    # configure filter nodes: which neurons to filter?
    spike_filter_node.set_neurons(pre_neuron_ids+post_neuron_ids)

    pre_trace_node.set_neurons(pre_neuron_ids, post_neuron_ids)
    post1_trace_node.set_neurons(post_neuron_ids, pre_neuron_ids)
    post2_trace_node.set_neurons(post_neuron_ids, post_neuron_ids)

    pre_trace_node.set_trace_parameters(pre_tau, method, trace_max)
    post1_trace_node.set_trace_parameters(post1_tau, method, trace_max)
    post2_trace_node.set_trace_parameters(post2_tau, method, trace_max)

    # ---------------- create a graph ----------------

    # start the graph
    graph.start()
    
    with open("./w/times.txt", mode='w', encoding='utf-8') as file_obj:
        file_obj.write('\n')

    t1 = int(round(time.time() * 1000)) # in ms
    while(True):
        post1_traces = post1_trace_sink.get_events()
        post2_traces = post2_trace_sink.get_events()
        pre_traces = pre_trace_sink.get_events()

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

        # on pre, use post1 trace
        for post1_trace in post1_traces:
            # for each pre
            pre_neuron = post1_trace.trigger_neuron
            i = pre_neuron_ids.index(pre_neuron)

            # check all its posts, update w_plast[i][j]
            for j in range(len(post_neuron_ids)):
                post_neuron = post_neuron_ids[j]
                post1 = post1_trace.trace_map[post_neuron]

                delta_w = nuEEpre * post1 * w_plast[i][j]**expEEpre
                w_plast[i][j] -= delta_w
        
        # on post, use pre and post2 trace
        for pre_trace in pre_traces:
            # for each post
            post_neuron = pre_trace.trigger_neuron
            j = post_neuron_ids.index(post_neuron)
            timestamp = pre_trace.timestamp

            # get post2 trace
            post2_trace = get_trace_value(post2_traces, timestamp)
            if post2_trace == None:
                # print("post2_trace is None, use a random value")
                post2 = random.random()
            else:
                post2 = post2_trace.trace_map[post_neuron]

            # check all its pre traces, update w_plast[i][j]
            for i in range(len(pre_neuron_ids)):
                pre_neuron = pre_neuron_ids[i]
                pre = pre_trace.trace_map[pre_neuron]

                delta_w = nuEEpost * pre * post2 * (wmaxEE - w_plast[i][j])**expEEpost
                w_plast[i][j] += delta_w
        
        t2 = int(round(time.time() * 1000)) # in ms
        with open("./w/times.txt", mode='a', encoding='utf-8') as file_obj:
            file_obj.write(str(t2-t1)+'\n')
        t1 = t2
        
        # time.sleep(1) # sleep 100 ms
        # plot_w(w_plast)
    print("done")