from numpy.core.defchararray import add
import samna
import samna.dynapse1 as dyn1

import time
import numpy as np

import sys
sys.path.append("/home/jingyue/aa_projects/samna_projects/ctxctl_contrib/")
import dynapse1utils as ut
from dynapse1constants import MAX_NUM_CAMS
from netgen import Neuron, NeuronGroup, Synapses, add_synapses, NetworkGenerator, weight_matrix2lists, remove_synapses
from params import gen_param_group

from stdp import Stdp
from stdp_utils import floatW2intW

if __name__ == "__main__":
    schip=0
    score=0
    sids = [1, 2, 3]
    rates = [0, 100, 0]

    chip=1
    core=0
    pre_nids = [16, 17, 18]
    post_nids = [32, 33, 34]

    pre_neuron_ids = [(chip,core,x) for x in pre_nids]
    post_neuron_ids = [(chip,core,x) for x in post_nids]

    low_init_w = 0.1
    w_plast = np.ones((len(pre_neuron_ids), len(post_neuron_ids)))*low_init_w
    max_pre_count = MAX_NUM_CAMS - 1
    int_w_plast = floatW2intW(w_plast, max_pre_count)

    num_samples = 10
    duration_per_sample = 500 # millisec
    duration_cool_down = 500 # millisec

    # open DYNAP-SE1 board to get Dynapse1Model
    device_name = "dynapse1"

    # open with GUI
    # store, gui_process = ut.open_dynapse1(device_name)
    store = ut.open_dynapse1(device_name, gui=False, sender_port=12345, receiver_port=13346)

    model = getattr(store, device_name)

    # set parameters
    paramGroup = gen_param_group()
    paramGroup.param_map["PS_WEIGHT_EXC_S_N"].coarse_value = 0
    paramGroup.param_map["PS_WEIGHT_EXC_S_N"].fine_value = 0
    for chip in range(4):
        for core in range(4):
            model.update_parameter_group(paramGroup, chip, core)

    # get Dynapse1 api from the model
    api = model.get_dynapse1_api()

    # ------------------- build network -------------------
    net_gen = NetworkGenerator()

    spikegen_group = NeuronGroup(schip,score,sids,True)

    pre_neuron_group = NeuronGroup(chip,core,pre_nids)
    post_neuron_group = NeuronGroup(chip,core,post_nids)

    # connect spikegen_group to pre_neuron_group
    connectivity = {
        'pre_gen2pre': Synapses(spikegen_group, pre_neuron_group, dyn1.Dynapse1SynType.AMPA, conn_type='one2one'),
        'post_gen2post': Synapses(spikegen_group, post_neuron_group, dyn1.Dynapse1SynType.AMPA, conn_type='one2one'),
        'pre2post': Synapses(pre_neuron_group, post_neuron_group, dyn1.Dynapse1SynType.NMDA, weight_matrix=int_w_plast)
    }

    for conn in connectivity:
        print(conn)
        add_synapses(net_gen, connectivity[conn])

    # print the network so you can double check (optional)
    print(net_gen.network)

    new_config = net_gen.make_dynapse1_configuration()
    model.apply_configuration(new_config)
    # ------------------- build network -------------------

    # set up Poisson spike generators
    spikegen_ids = [(schip,score,x) for x in sids]
    global_poisson_gen_ids = ut.get_global_id_list(spikegen_ids)
    poisson_gen = model.get_poisson_gen()
    poisson_gen.set_chip_id(chip)

    stdp = Stdp(model, net_gen, pre_neuron_ids, post_neuron_ids, w_plast, algorithm='triplet_stdp')

    stdp.start_stdp()

    for i in range(num_samples):
        # give new stimulation
        for i in range(len(global_poisson_gen_ids)):
            poisson_gen.write_poisson_rate_hz(global_poisson_gen_ids[i], rates[i])
        poisson_gen.start()

        # learn: w_plast being updated in another thread
        time.sleep(float(duration_per_sample/1e3))

        # remove the current pre post connections
        remove_synapses(net_gen, connectivity['pre2post'])

        # add new pre-post connections using the latest w_plast
        int_w_plast = floatW2intW(stdp.w_plast, max_pre_count)
        connectivity['pre2post'] = Synapses(pre_neuron_group, post_neuron_group, dyn1.Dynapse1SynType.NMDA, weight_matrix=int_w_plast)
        add_synapses(net_gen, connectivity['pre2post'])

        # print(stdp.w_plast)
        # print(int_w_plast)
        # print(net_gen.network)

        new_config = net_gen.make_dynapse1_configuration()
        model.apply_configuration(new_config)

        poisson_gen.stop()

        time.sleep(float(duration_cool_down/1e3))

    stdp.stop_stdp()

    # ut.close_dynapse1(store, device_name, gui_process)
    ut.close_dynapse1(store, device_name)