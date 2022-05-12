import matplotlib.pyplot as plt
import seaborn as sns; sns.set()
import numpy as np
import os
import time
import json
import samna.dynapse1 as d
import sys
sys.path.append("/home/jingyue/aa_projects/samna_projects/ctxctl_contrib/")
from dynapse1utils import get_selected_timestamps, get_selected_traces

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

def plot_raster(spikes, neuron_ids, t_start=None, t_end=None):
    """
    plot the raster of neuron_ids from collected spikes.
    spikes: spike
    """
    if len(set(neuron_ids)) != len(neuron_ids):
        raise Exception("Duplicate neuron ids exist!")
    
    timestamps = get_selected_timestamps(spikes, neuron_ids)

    ax = plt.subplot()
    for i in range(len(neuron_ids)):
        print(i, timestamps[i])
        ax.plot(timestamps[i], np.ones(len(timestamps[i]))*i, '.', label=str(i)+': '+str(neuron_ids[i]))
        # for time in timestamps[i]:
        #     plt.axvline(time)
    
    if t_start != None and t_end != None:
        ax.set_xlim(t_start, t_end)
    
    ax.legend()

def plot_trace(timed_traces, neuron_ids, t_start=None, t_end=None):
    """
    plot the raster of neuron_ids from collected spikes.
    spikes: spike
    """
    if len(set(neuron_ids)) != len(neuron_ids):
        raise Exception("Duplicate neuron ids exist!")
    
    timestamps, trace_values = get_selected_traces(timed_traces, neuron_ids)

    ax = plt.subplot()
    for i in range(len(neuron_ids)):
        print(timestamps[i], trace_values[i])
        ax.plot(timestamps[i], trace_values[i], '.-', label=str(i)+': '+str(neuron_ids[i]))
    
    if t_start != None and t_end != None:
        ax.set_xlim(t_start, t_end)
    
    ax.legend()

def save_samna_objects2file(objects, fname='./spikes.txt'):
    list_obj = []
    for obj in objects:
        list_obj.append(json.loads(obj.to_json()))
    
    with open(fname, 'w') as json_file:
        json.dump(list_obj, json_file, indent=4)

    # with open(fname, 'w') as json_file:
    #     for obj in objects:
    #         json.dump(obj.to_json(), json_file, indent=4)

def load_samna_objects_file(fname='./spikes.txt'):
    with open(fname) as json_file:
        list_obj_dict = json.load(json_file)
    
    list_obj = []
    for obj_dict in list_obj_dict:
        list_obj.append(convert_dict2samna_object(obj_dict))
    return list_obj

def convert_dict2samna_object(obj_dict):
    obj_dict = obj_dict['value0']
    # Dynapse1Trace
    if 'traceMap' in obj_dict.keys():
        trace_event = d.Dynapse1Trace()
        trace_event.timestamp = obj_dict['timestamp']
        trace_map_list = obj_dict['traceMap']
        trace_map = {}
        for trace_item in trace_map_list:
            neuron = (trace_item['key']['tuple_element0'], trace_item['key']
            ['tuple_element1'], trace_item['key']['tuple_element2'])
            trace_value = trace_item['value']
            trace_map.update({neuron:trace_value})
        trace_event.trace_map = trace_map
        trace_event.trigger_neuron = (obj_dict['triggerNeuron']['tuple_element0'],\
            obj_dict['triggerNeuron']['tuple_element1'],obj_dict['triggerNeuron']['tuple_element2'])
        return trace_event
    # spike
    elif 'timestamp' in obj_dict.keys() and 'neuronId' in obj_dict\
    .keys():
        spike = d.Spike()
        spike.timestamp = obj_dict['timestamp']
        spike.neuron_id = obj_dict['neuronId']
        spike.core_id = obj_dict['coreId']
        spike.chip_id = obj_dict['chipId']
        return spike
    else:
        raise Exception("Samna object type not supported by the conversion function.")