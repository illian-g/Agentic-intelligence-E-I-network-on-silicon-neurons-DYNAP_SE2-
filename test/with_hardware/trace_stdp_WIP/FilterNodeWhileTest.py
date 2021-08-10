import samna
import samna.dynapse1 as dyn1

import time
import _thread
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns; sns.set()

from stdp import stdp

import sys
# Note: change the path to where your lib files are
sys.path.append("/home/jingyue/aa_projects/samna_projects/ctxctl_contrib/")
import Dynapse1Utils as ut
from NetworkGenerator import Neuron, NeuronGroup, Synapses, add_synapses, NetworkGenerator

def gen_param_group_1core():
    paramGroup = dyn1.Dynapse1ParameterGroup()
    # THR
    # ok
    paramGroup.param_map["IF_THR_N"].coarse_value = 5
    paramGroup.param_map["IF_THR_N"].fine_value = 80

    # refactory period
    paramGroup.param_map["IF_RFR_N"].coarse_value = 4
    paramGroup.param_map["IF_RFR_N"].fine_value = 128

    # leakage
    paramGroup.param_map["IF_TAU1_N"].coarse_value = 4
    paramGroup.param_map["IF_TAU1_N"].fine_value = 80

    paramGroup.param_map["IF_TAU2_N"].coarse_value = 7
    paramGroup.param_map["IF_TAU2_N"].fine_value = 255

    paramGroup.param_map["IF_DC_P"].coarse_value = 2
    paramGroup.param_map["IF_DC_P"].fine_value = 150

    paramGroup.param_map["NPDPIE_TAU_F_P"].coarse_value = 4
    paramGroup.param_map["NPDPIE_TAU_F_P"].fine_value = 80

    paramGroup.param_map["NPDPIE_THR_F_P"].coarse_value = 4
    paramGroup.param_map["NPDPIE_THR_F_P"].fine_value = 80

    paramGroup.param_map["PS_WEIGHT_EXC_F_N"].coarse_value = 0
    paramGroup.param_map["PS_WEIGHT_EXC_F_N"].fine_value = 0

    paramGroup.param_map["NPDPIE_TAU_S_P"].coarse_value = 4
    paramGroup.param_map["NPDPIE_TAU_S_P"].fine_value = 80

    paramGroup.param_map["NPDPIE_THR_S_P"].coarse_value = 4
    paramGroup.param_map["NPDPIE_THR_S_P"].fine_value = 80

    paramGroup.param_map["PS_WEIGHT_EXC_S_N"].coarse_value = 0
    paramGroup.param_map["PS_WEIGHT_EXC_S_N"].fine_value = 0

    paramGroup.param_map["IF_NMDA_N"].coarse_value = 0
    paramGroup.param_map["IF_NMDA_N"].fine_value = 0

    paramGroup.param_map["NPDPII_TAU_F_P"].coarse_value = 4
    paramGroup.param_map["NPDPII_TAU_F_P"].fine_value = 80

    paramGroup.param_map["NPDPII_THR_F_P"].coarse_value = 0
    paramGroup.param_map["NPDPII_THR_F_P"].fine_value = 0

    paramGroup.param_map["PS_WEIGHT_INH_F_N"].coarse_value = 0
    paramGroup.param_map["PS_WEIGHT_INH_F_N"].fine_value = 0

    paramGroup.param_map["NPDPII_TAU_S_P"].coarse_value = 4
    paramGroup.param_map["NPDPII_TAU_S_P"].fine_value = 80

    paramGroup.param_map["NPDPII_THR_S_P"].coarse_value = 0
    paramGroup.param_map["NPDPII_THR_S_P"].fine_value = 0

    paramGroup.param_map["PS_WEIGHT_INH_S_N"].coarse_value = 0
    paramGroup.param_map["PS_WEIGHT_INH_S_N"].fine_value = 0

    paramGroup.param_map["IF_AHTAU_N"].coarse_value = 4
    paramGroup.param_map["IF_AHTAU_N"].fine_value = 80

    paramGroup.param_map["IF_AHTHR_N"].coarse_value = 0
    paramGroup.param_map["IF_AHTHR_N"].fine_value = 0

    paramGroup.param_map["IF_AHW_P"].coarse_value = 0
    paramGroup.param_map["IF_AHW_P"].fine_value = 0

    paramGroup.param_map["IF_CASC_N"].coarse_value = 0
    paramGroup.param_map["IF_CASC_N"].fine_value = 0

    paramGroup.param_map["PULSE_PWLK_P"].coarse_value = 4
    paramGroup.param_map["PULSE_PWLK_P"].fine_value = 106

    paramGroup.param_map["R2R_P"].coarse_value = 3
    paramGroup.param_map["R2R_P"].fine_value = 85

    paramGroup.param_map["IF_BUF_P"].coarse_value = 3
    paramGroup.param_map["IF_BUF_P"].fine_value = 80

    return paramGroup

if __name__ == "__main__":
    # open DYNAP-SE1 board to get Dynapse1Model
    device_name = "dynapse1"

    # open with GUI
    # store, gui_process = ut.open_dynapse1(device_name)
    store = ut.open_dynapse1(device_name, gui=False, sender_port=12345, receiver_port=12346)

    model = getattr(store, device_name)

    # set parameters
    paramGroup = gen_param_group_1core()
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