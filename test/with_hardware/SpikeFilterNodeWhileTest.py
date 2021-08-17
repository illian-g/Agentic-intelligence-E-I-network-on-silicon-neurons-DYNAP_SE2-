import samna
import samna.dynapse1 as dyn1

import time
import _thread
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns; sns.set()

import sys
# Note: change the path to where your lib files are
sys.path.append("/home/jingyue/aa_projects/samna_projects/ctxctl_contrib/")
import Dynapse1Utils as ut
from NetworkGenerator import Neuron, NeuronGroup, Synapses, add_synapses, NetworkGenerator

from params import gen_dc_params

if __name__ == "__main__":
    # open DYNAP-SE1 board to get Dynapse1Model
    device_name = "dynapse1"

    # open with GUI
    # store, gui_process = ut.open_dynapse1(device_name)
    store = ut.open_dynapse1(device_name, gui=False, sender_port=12345, receiver_port=12346)

    model = getattr(store, device_name)

    # set parameters
    paramGroup = gen_dc_params()
    for chip in range(4):
        for core in range(4):
            model.update_parameter_group(paramGroup, chip, core)

    # get Dynapse1 api from the model
    api = model.get_dynapse1_api()

    graph, filter_node, sink_node = ut.create_neuron_select_graph(model, [(0,0,2)])
    graph.start()
    while(True):
        t1 = time.time()
        evts = sink_node.get_events()
        t2 = time.time()
        print(t2-t1)