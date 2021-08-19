import samna
import samna.dynapse1 as dyn1

from params import gen_param_group as gen

def gen_param_group():

    paramGroup = gen()

    paramGroup.param_map["IF_TAU1_N"].coarse_value = 3
    paramGroup.param_map["IF_TAU1_N"].fine_value = 80

    paramGroup.param_map["IF_THR_N"].coarse_value = 5
    paramGroup.param_map["IF_THR_N"].fine_value = 80

    # NMDA, pre to post neurons
    paramGroup.param_map["PS_WEIGHT_EXC_S_N"].coarse_value = 7
    paramGroup.param_map["PS_WEIGHT_EXC_S_N"].fine_value = 80

    # AMPA, spikegen to neurons
    paramGroup.param_map["PS_WEIGHT_EXC_F_N"].coarse_value = 6
    paramGroup.param_map["PS_WEIGHT_EXC_F_N"].fine_value = 80

    return paramGroup

def set_params(model):
    paramGroup = gen_param_group()
    for chip in range(4):
        for core in range(4):
            model.update_parameter_group(paramGroup, chip, core)