import samna
import samna.dynapse1 as dyn1

import time
import numpy as np

import sys
# Note: change the path to where your lib files are
sys.path.append("/home/jingyue/aa_projects/samna_projects/ctxctl_contrib/")
import Dynapse1Utils as ut
from NetworkGenerator import Neuron, NeuronGroup, Synapses, add_synapses, NetworkGenerator
from params import gen_param_group

from stdp import Stdp

if __name__ == "__main__":

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

    schip=0
    score=0
    sids = [1, 2, 3]
    spikegen_group = NeuronGroup(schip,score,sids,True)

    chip=1
    core=0
    pre_nids = [16, 17, 18]
    post_nids = [32, 33, 34]
    pre_neuron_group = NeuronGroup(chip,core,pre_nids)
    post_neuron_group = NeuronGroup(chip,core,post_nids)

    # connect spikegen_group to pre_neuron_group
    syn = Synapses(spikegen_group, pre_neuron_group, dyn1.Dynapse1SynType.AMPA, conn_type='one2one')
    add_synapses(net_gen, syn)
    syn = Synapses(spikegen_group, post_neuron_group, dyn1.Dynapse1SynType.AMPA, conn_type='one2one')
    add_synapses(net_gen, syn)

    # print the network so you can double check (optional)
    print(net_gen.network)

    # make a dynapse1config using the network
    new_config = net_gen.make_dynapse1_configuration()

    # apply the configuration
    model.apply_configuration(new_config)
    # ------------------- build network -------------------

    # set up Poisson spike generators
    spikegen_ids = [(schip,score,x) for x in sids]
    global_poisson_gen_ids = ut.get_global_id_list(spikegen_ids)
    poisson_gen = model.get_poisson_gen()
    poisson_gen.set_chip_id(chip)
    poisson_gen.write_poisson_rate_hz(global_poisson_gen_ids[0], 50)
    poisson_gen.write_poisson_rate_hz(global_poisson_gen_ids[1], 200)
    poisson_gen.write_poisson_rate_hz(global_poisson_gen_ids[2], 50)

    pre_neuron_ids = [(chip,core,x) for x in pre_nids]
    post_neuron_ids = [(chip,core,x) for x in post_nids]

    poisson_gen.start()

    low_init_w = 0.1
    w_plast = np.ones((len(pre_neuron_ids), len(post_neuron_ids)))*low_init_w

    stdp = Stdp(model, net_gen, pre_neuron_ids, post_neuron_ids, w_plast, algorithm='triplet_stdp')

    stdp.start_stdp()

    time.sleep(60*20) # learn 20 min

    stdp.stop_stdp()

    # ut.close_dynapse1(store, device_name, gui_process)
    ut.close_dynapse1(store, device_name)