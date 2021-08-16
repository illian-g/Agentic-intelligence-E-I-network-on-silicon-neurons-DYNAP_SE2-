import samna
import samna.dynapse1 as dyn1

from params import gen_param_group as gen

def gen_param_group():

    paramGroup = gen()

    paramGroup.param_map["PS_WEIGHT_EXC_S_N"].coarse_value = 0
    paramGroup.param_map["PS_WEIGHT_EXC_S_N"].fine_value = 0

    return paramGroup