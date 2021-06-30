import samna.dynapse1 as dyn1
import sys
# Note: change the path to where your lib files are
sys.path.append("/home/jingyue/aa_projects/samna_projects/ctxctl_contrib/")
from NetworkGenerator import Neuron, NeuronGroup, NetworkGenerator

if __name__ == "__main__":
    """This is an example of how to use NeuronGroup and add_connections* functions to create network and the corresponding Dynapse1Configuration using NetworkGenerator."""
    # define 2 neuron groups
    chip1 = 0
    core1 = 0
    nids1 = [101,102,103]
    pop1 = NeuronGroup(chip1,core1,nids1,True)
    print('pop1',pop1.chip_id, pop1.core_id, pop1.neuron_ids,pop1.neurons)

    chip2 = 0
    core2 = 1
    nids2 = [14,15,16]
    pop2 = NeuronGroup(chip2,core2,nids2)
    print('pop2',pop2.chip_id, pop2.core_id, pop2.neuron_ids,pop2.neurons)

    # define 2 neuron groups
    print('When chip_id changes, neurons follow the change!')
    pop2.chip_id = 2
    print('pop2',pop2.chip_id, pop2.core_id, pop2.neuron_ids,pop2.neurons)

    net_gen = NetworkGenerator()

    print('\nadd_connections_from_list')
    net_gen.add_connections_from_list(pop1.neurons, pop2.neurons, dyn1.Dynapse1SynType.AMPA, [0,1,2,0], [2,1,0,2])

    print(net_gen.network)
    
    print('remove_connections_from_list')
    net_gen.remove_connections_from_list(pop1.neurons, pop2.neurons, dyn1.Dynapse1SynType.AMPA, [0,1,2,0], [2,1,0,2])

    print(net_gen.network)

    print('\nadd_connections_from_type, one2one')
    net_gen.add_connections_from_type(pop1.neurons, pop2.neurons, dyn1.Dynapse1SynType.AMPA, 'one2one')

    print(net_gen.network)

    net_gen.clear_network()

    print('add_connections_from_type, all2all')
    net_gen.add_connections_from_type(pop1.neurons, pop2.neurons, dyn1.Dynapse1SynType.AMPA, conn_type='all2all', p=0.8, rand_seed=56)

    print(net_gen.network)

    new_config = net_gen.make_dynapse1_configuration()