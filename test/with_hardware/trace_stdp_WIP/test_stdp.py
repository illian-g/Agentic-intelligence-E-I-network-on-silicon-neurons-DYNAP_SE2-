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

from stdp import Stdp
from stdp_utils import floatW2intW
from stdp_params import set_params

if __name__ == "__main__":
    schip=0
    score=0
    sids = [1, 2, 3]
    rates = [0, 200, 0]

    chip=1
    core=0
    pre_nids = [16, 17, 18]
    post_nids = [32, 33, 34]

    mux_conn_spikegen = 5

    pre_neuron_ids = [(chip,core,x) for x in pre_nids]
    post_neuron_ids = [(chip,core,x) for x in post_nids]

    algorithm='triplet_stdp'
    stdp_new_thread = True # True False
    remove_bad_traces = False
    spike_sink_debug = False

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

    set_params(model)

    # ------------------- build network -------------------
    net_gen = NetworkGenerator()

    spikegen_group = NeuronGroup(schip,score,sids,True)

    pre_neuron_group = NeuronGroup(chip,core,pre_nids)
    post_neuron_group = NeuronGroup(chip,core,post_nids)

    # connect spikegen_group to pre_neuron_group
    connectivity = {
        'pre_gen2pre': Synapses(spikegen_group, pre_neuron_group, dyn1.Dynapse1SynType.NMDA, conn_type='one2one', mux_conn=mux_conn_spikegen),
        'post_gen2post': Synapses(spikegen_group, post_neuron_group, dyn1.Dynapse1SynType.NMDA, conn_type='one2one', mux_conn=mux_conn_spikegen),
        'pre2post': Synapses(pre_neuron_group, post_neuron_group, dyn1.Dynapse1SynType.AMPA, weight_matrix=int_w_plast)
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

    # set 1st sample
    for i in range(len(global_poisson_gen_ids)):
        poisson_gen.write_poisson_rate_hz(global_poisson_gen_ids[i], rates[i])
    poisson_gen.start()

    stdp = Stdp(model, net_gen, pre_neuron_ids, post_neuron_ids, w_plast, algorithm=algorithm, new_thread=stdp_new_thread, remove_bad_traces=remove_bad_traces, spike_sink_debug=spike_sink_debug)

    print(w_plast)
    print(int_w_plast)
    print('Learning starts!')

    stdp.start_stdp()

    for sample in range(num_samples):
        # give new stimulation
        for i in range(len(global_poisson_gen_ids)):
            poisson_gen.write_poisson_rate_hz(global_poisson_gen_ids[i], rates[i])
        poisson_gen.start()

        # learn: w_plast being updated in another thread
        time.sleep(float(duration_per_sample/1e3))

        # remove the current pre post connections
        remove_synapses(net_gen, connectivity['pre2post'])

        # add new pre-post connections using the latest w_plast
        current_w_plast = stdp.w_plast
        int_w_plast = floatW2intW(current_w_plast, max_pre_count)
        connectivity['pre2post'] = Synapses(pre_neuron_group, post_neuron_group, dyn1.Dynapse1SynType.AMPA, weight_matrix=int_w_plast)
        add_synapses(net_gen, connectivity['pre2post'])

        print(current_w_plast)
        print(int_w_plast)
        # print(net_gen.network)

        new_config = net_gen.make_dynapse1_configuration()
        model.apply_configuration(new_config)

        poisson_gen.stop()

        time.sleep(float(duration_cool_down/1e3))

    stdp.stop_stdp()

    # ut.close_dynapse1(store, device_name, gui_process)
    ut.close_dynapse1(store, device_name)