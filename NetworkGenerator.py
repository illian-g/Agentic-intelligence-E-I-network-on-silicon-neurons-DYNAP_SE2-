import samna.dynapse1 as dyn1
import collections
import random

import Dynapse1Utils as ut
from Dynapse1Constants import NUM_CHIPS, CORES_PER_CHIP, NEURONS_PER_CORE, MAX_NUM_CAMS
from NetworkGeneratorDetails import weight_matrix2lists, gen_one2one_lists, gen_all2all_lists, validate, convert_validated_network2dynapse1_configuration, find_neuron_in_dict, find_pre_in_post_incoming

def add_synapses(netgen, synapse):
    """Add a synapse group into a network generator"""
    netgen.add_connections_from_list(synapse.pre.neurons, synapse.post.neurons, synapse.synapse_type, pre_ids=synapse.pre_list, post_ids=synapse.post_list)

def add_wta_conns(netgen, wta_conns):
    """Add WTA connections for a WTA into a network generator"""
    add_synapses(netgen, wta_conns.ei)
    add_synapses(netgen, wta_conns.ie)
    if wta_conns.ee !=None:
        add_synapses(netgen, wta_conns.ee)

def remove_synapses(netgen, synapse):
    """Remove a synapse group into a network generator"""
    netgen.remove_connections_from_list(synapse.pre.neurons, synapse.post.neurons, synapse.synapse_type, pre_ids=synapse.pre_list, post_ids=synapse.post_list)

class Neuron:
    """
    Attribute:
        chip_id, core_id, neuron_id: int
        is_spike_gen: bool, if this neuron is a spike generator on the FPGA or a physical neuron on chip.
        incoming_connections: a dictionarty which stores the incoming_connections. Only starts to play a role after add_connection(pre, neuron).
            key: tuple, (pre.core_id,pre.neuron_id,synapse_type).
                Corresponds to cam. Divide the connections by its cam value for cam reuse.
            value: list, [(pre.chip_id, pre.is_spike_gen), (pre.chip_id, pre.is_spike_gen),...].
                To tell if the post neurons are the same neuron. get the connection weight.
    """
    def __init__(self, chip_id=0, core_id=0, neuron_id=0, is_spike_gen=False):
        if is_spike_gen:
            num_chips = 1
        else:
            num_chips = NUM_CHIPS
        if chip_id >= num_chips or chip_id < 0:
            raise Exception("chip id invalid!")
        if core_id >= CORES_PER_CHIP or core_id < 0:
            raise Exception("core id invalid!")
        if neuron_id >= NEURONS_PER_CORE or neuron_id < 0:
            raise Exception("neuron id invalid!")
        self.chip_id = chip_id
        self.core_id = core_id
        self.neuron_id = neuron_id
        self.is_spike_gen = is_spike_gen
        # (pre.core_id,pre.neuron_id,synapse_type): [(pre.chip_id, pre.is_spike_gen), (pre.chip_id, pre.is_spike_gen),...]
        self.incoming_connections = collections.defaultdict(list)
    
    def __repr__(self):
        if self.is_spike_gen:
            neur_str = 's'
        else:
            neur_str = 'n'

        return f"C{self.chip_id}c{self.core_id}{neur_str}{self.neuron_id}"
    
    def __eq__(self, other):
        """Only compares the ids. Consider a neuron as an individual neuron without any external connections (i.e. not in a Network)"""
        eq_flag1 = self.chip_id == other.chip_id and \
            self.core_id == other.core_id and \
            self.neuron_id == other.neuron_id and \
            self.is_spike_gen == other.is_spike_gen
        
        eq_flag2 = True
        for key in self.incoming_connections:
            eq_flag2 = eq_flag2 and (sorted(self.incoming_connections[key]) == sorted(other.incoming_connections[key]))

        return eq_flag1 and eq_flag2
    
    def __lt__(self, other):
        """	To get called on comparison using < operator. For sorting."""
        flag = False
        if self.chip_id < other.chip_id:
            flag = True
        elif self.chip_id == other.chip_id:
            if self.core_id < other.core_id:
                flag = True
            elif self.core_id == other.core_id:
                if self.neuron_id < other.neuron_id:
                    flag = True
        
        return flag
    
    def __hash__(self):

        h = hash("{}.{}.{}.{}.{}".format(self.chip_id,self.chip_id,
                                        self.neuron_id,self.is_spike_gen,
                                        self.incoming_connections))

        return h

class NeuronGroup:
    """
    Attributes
    ------------
    chip_id : int
        chip id
    core_id : int
        core id 
    neuron_ids: list[int]
        list of neuron ids
    is_spike_gen: bool 
        if this neuron group is a group of spike generators on the FPGA or silicon neurons on chip.
    """
    def __init__(self, chip_id=0, core_id=0, neuron_ids=None, is_spike_gen=False):
        if is_spike_gen:
            num_chips = 1
        else:
            num_chips = NUM_CHIPS

        if chip_id >= num_chips or chip_id < 0:
            raise Exception("chip id invalid!")
        if core_id >= CORES_PER_CHIP or core_id < 0:
            raise Exception("core id invalid!")
        for neuron_id in neuron_ids:
            if neuron_id == None or neuron_id >= NEURONS_PER_CORE or neuron_id < 0:
                raise Exception("neuron ids invalid!")
        
        # check if you use neuron0 of a chip
        if core_id == 0:
            for nid in neuron_ids:
                if nid == 0:
                    print("WARNING: be careful, you are using neuron 0 from a chip to construct a neuron group!")

        self.chip_id = chip_id
        self.core_id = core_id
        self.neuron_ids = neuron_ids
        self.is_spike_gen = is_spike_gen

    @property
    def neurons(self):
        """neurons getter: return a list of neurons given the current chip/core/neuron ids"""
        neurons = []
        for nid in self.neuron_ids:
            neurons.append(Neuron(self.chip_id,self.core_id,nid,self.is_spike_gen))
        return neurons
    
    def __eq__(self, other):
        """Only compares the ids. Consider a neuron group as an individual group without any external connections (i.e. not in a Network)"""
        return self.chip_id == other.chip_id and \
            self.core_id == other.core_id and \
            self.neuron_ids == other.neuron_ids and \
            self.is_spike_gen == other.is_spike_gen

class Synapses:
    """
    Connections from a pre NeuronGroup to a post NeuronGroup. Stores the information of the connectivity.
    """
    def __init__(self, pre_group, post_group, synapse_type, pre_list=None, post_list=None, conn_type=None, p=None, rand_seed=None, weight_matrix=None):
        self.pre = pre_group
        self.post = post_group
        self.synapse_type = synapse_type
        
        # if specify the conn_type, check 
        # 1) if the type is valid 2) if pre_list and post_list are None
        if conn_type != None:
            if (pre_list == None and post_list == None and weight_matrix==None) == False:
                raise Exception('pre_list, post_list or weight_matrix cannot be specified given connection type {conn_type}!')
            
            # generate the pre_list and post_list here, so that user can check which connections are created
            pre_neurons = pre_group.neurons
            post_neurons = post_group.neurons
            if conn_type == 'one2one':
                self.pre_list, self.post_list = gen_one2one_lists(pre_neurons, post_neurons)
            elif conn_type == 'all2all':
                if p == None:
                    p = 1
                self.pre_list, self.post_list = gen_all2all_lists(pre_neurons, post_neurons, p, rand_seed)
            else:
                raise Exception('Connection type not supported!')
            
            self.conn_type = conn_type
            self.p = p
            self.rand_seed = rand_seed
        
        else:
            if pre_list != None and post_list != None and weight_matrix == None:
                assert(len(pre_list)==len(post_list)), 'pre_list '+\
                ' and pre_list need to have the same length'
                self.pre_list, self.post_list = pre_list, post_list
            elif pre_list == None and post_list == None and weight_matrix.any() != None:
                # convert w to pre_list and post_list
                if weight_matrix.shape[0] == len(pre_group.neurons) and weight_matrix.shape[1] == len(post_group.neurons):
                    self.pre_list, self.post_list = weight_matrix2lists(weight_matrix, pre_group, post_group)
            else:
                raise Exception('Please give either (pre_list and post_list) or (weight_matrix)!')

            self.conn_type = None
            self.p = None
            self.rand_seed = None

class WTA_connections:
    """Define WTA EE EI IE connections of for an EXC and an INH population"""
    def __init__(self, exc_group, inh_group, syn_type_ei, syn_type_ie, syn_type_ee=None, p_ei=1, p_ie=1, ee_pres=None, ee_posts=None, rand_seed=None):
        self.ei = Synapses(exc_group, inh_group, syn_type_ei, conn_type='all2all', p=p_ei, rand_seed=rand_seed)
        self.ie = Synapses(inh_group, exc_group, syn_type_ie, conn_type='all2all', p=p_ie, rand_seed=rand_seed)

        if syn_type_ee != None:
            if ee_pres == None or ee_posts == None:
                raise Exception('ee_pres and ee_posts must be given to create EE connections')
            self.ee = Synapses(exc_group, exc_group, syn_type_ee, pre_list=ee_pres, post_list=ee_posts)
        else:
            self.ee = None

class Network:
    """
    Attribute:
        post_neuron_dict: a dictionary which stores all the post neurons (and their incoming connections).
            key: tuple, (post.chip_id, post.core_id).
                Divide the post neurons by its location (core) for aliasing check.
            value: list of neurons each of which has incoming connections.
    """
    def __init__(self):
        # only track onchip post neurons
        # all connection info already stored in post_neuron.incoming_connections
        self.post_neuron_dict = collections.defaultdict(list)
    
    def __repr__(self):
        """Create official string for class Network. print(Network), str(Network) can be used."""
        
        if len(self.post_neuron_dict.keys()) == 0:
            return f"The network is empty!"
        else:
            line0 = "Post neuron (ChipId,coreId,neuronId): incoming connections [(preNeuron,synapseType), ...]\n"

            result_str = line0            

            dictionary_items = self.post_neuron_dict.items()
            sorted_items = sorted(dictionary_items)
            for item in sorted_items:
                post_neurons = item[1]
                for post in post_neurons:
                    incoming_connections_list, incoming_connections_str_list = \
                        convert_incoming_conns_dict2list(post.incoming_connections)
                    result_str += str(post) +': ' + str(incoming_connections_str_list) + '\n'
            
            return f"{result_str}"
    
    def __eq__(self, other):
        """Compare 2 networks."""
        eq_flag = True
        for key in self.post_neuron_dict:
            eq_flag = eq_flag and (sorted(self.post_neuron_dict[key]) == sorted(other.post_neuron_dict[key]))

        return eq_flag

    def add_connection(self, pre, post, synapse_type):
        if post.is_spike_gen:
            raise Exception("post neuron cannot be a spike generator!")

        # onchip connections from left chips (i.e. 0,2) to right chips (i.e. 1,3) will make chips die
        if pre.is_spike_gen is False:
            left_chips = [0,2]
            right_chips = [1,3]
            if pre.chip_id in left_chips and post.chip_id in right_chips:
                # raise Exception("connections from left chips [0,2] to right chips [1,3] are forbidden!")
                print("WARNING: you are building connections from left chips [0,2] to right chips [1,3]!")
        
        # Neuron 0 warning. Please avoid neuron 0 of each chip
        if pre.core_id == 0 and pre.neuron_id == 0:
            print("WARNING: you are using neuron 0 of chip %i as a pre neuron!" % (pre.chip_id))
        if post.core_id == 0 and post.neuron_id == 0:
            print("WARNING: you are using neuron 0 of chip %i as a post neuron!" % (post.chip_id))

        post_key = (post.chip_id, post.core_id)
        # check if post neuron already in the dict
        # if not, add a post neuron with the pre in its incoming_connections;
        # if yes, only append the pre in post's incoming_connections
        nid_in_list = find_neuron_in_dict(post, self.post_neuron_dict)
        if nid_in_list == None:
            # add a new post neuron with the pre in incoming_conns to the dict
            post.incoming_connections.clear()
            post.incoming_connections[(pre.core_id, pre.neuron_id,
                synapse_type)].append((pre.chip_id, pre.is_spike_gen))
            self.post_neuron_dict[post_key].append(post)
        else:
            # only update the incoming_connections of the post neuron, add the new pre
            self.post_neuron_dict[post_key][nid_in_list].\
                incoming_connections[(pre.core_id, pre.neuron_id,
                synapse_type)].append((pre.chip_id, pre.is_spike_gen))

    def remove_connection(self, pre, post, synapse_type):
        if post.is_spike_gen:
            raise Exception("post neuron cannot be a spike generator!")

        # check if post neuron already in the dict
        post_id_in_list = find_neuron_in_dict(post, self.post_neuron_dict)
        if post_id_in_list == None:
            raise Exception("connection does not exist in the network!")
        else:
            # post neuron in the dict, check if pre in this post's incoming_connections
            post_key = (post.chip_id, post.core_id)
            post_in_dict = self.post_neuron_dict[post_key][post_id_in_list]
            pre_id = find_pre_in_post_incoming(pre, post_in_dict, synapse_type)
            if pre_id == None:
                raise Exception("connection does not exist in the network!")
            else:
                # remove the first pre from the incoming_connections of the post in the dict
                post_incoming_connections_dict = post_in_dict.incoming_connections
                pre_tag = (pre.core_id, pre.neuron_id, synapse_type)
                post_pre_tag_list = post_incoming_connections_dict[pre_tag]

                # remove the pre from the pre_tag list
                post_pre_tag_list.pop(pre_id)
                # self.post_neuron_dict[(post.chip_id, post.core_id)][post_id_in_list].\
                #     incoming_connections[(pre.core_id, pre.neuron_id,
                #     synapse_type)].pop(pre_id)

                # check if incoming_connections.pre_tag becomes empty
                # if empty, remove this pre_tag key from the incoming_connections dict
                if len(post_pre_tag_list) == 0:
                    # self.post_neuron_dict[(post.chip_id, post.core_id)][post_id_in_list].\
                    #     incoming_connections.pop((pre.core_id, pre.neuron_id,
                    #     synapse_type))
                    post_incoming_connections_dict.pop(pre_tag)

                    # check if the entire incoming_connections dict becomes empty
                    # if empty, the post neuron is not a post anymore, remove it from the post_dict[post_key] list
                    if len(post_incoming_connections_dict.keys()) == 0:
                        self.post_neuron_dict[post_key].pop(post_id_in_list)

                        # check if the post_neuron_dict[post_key] list becomes empty
                        # if empty, don't need this post_key anymore, remove this key from post_neuron_dict
                        if len(self.post_neuron_dict[post_key]) == 0:
                            self.post_neuron_dict.pop(post_key)

                            # check if post_neuron_dict becomes empty, send out a message
                            if len(self.post_neuron_dict.keys()) == 0:
                                print("Network cleared!")
    
    def add_connections_from_list(self, pre_neurons, post_neurons, synapse_type, pre_ids, post_ids):
        '''
        add multiple connections between 2 neuron groups.
        '''
        assert(len(pre_ids)==len(post_ids)), 'Pre neuron ids '+\
            ' and post neuron ids need to have the same length'
        
        for (i, j) in zip(pre_ids, post_ids):
            self.add_connection(pre_neurons[i], post_neurons[j], synapse_type)
    
    def remove_connections_from_list(self, pre_neurons, post_neurons, synapse_type, pre_ids, post_ids):
        '''
        remove multiple connections between 2 neuron groups.
        '''
        assert(len(pre_ids)==len(post_ids)), 'Pre neuron ids '+\
            ' and post neuron ids need to have the same length'
        
        for (i, j) in zip(pre_ids, post_ids):
            self.remove_connection(pre_neurons[i], post_neurons[j], synapse_type)

    def add_connections_from_type(self, pre_neurons, post_neurons, synapse_type, conn_type, p=1, rand_seed=None):
        '''
        add multiple connections between 2 neuron groups given connectivity type: 'one2one' or 'all2all'.
        '''
        print("Warning: this is an old way of creating connections which will not save pre_list and post_list as the connections. The preferable way is to create a Synapses object syn, then use add_synapses(net_gen, syn).")

        if conn_type == 'one2one':
            assert(len(pre_neurons)==len(post_neurons)), 'Pre neuron group '+\
            ' and post neuron group need to have the same length for one2one connections'
            for i in range(len(pre_neurons)):
                self.add_connection(pre_neurons[i], post_neurons[i], synapse_type)
        elif conn_type == 'all2all':
            random.seed(rand_seed)

            all2all_conns = []
            for pre in range(len(pre_neurons)):
                for post in range(len(post_neurons)):
                    all2all_conns.append((pre, post))
            num_conns = round(len(all2all_conns)*p)
            random_conns = random.sample(all2all_conns, num_conns)
            for pair in random_conns:
                pre_id = pair[0]
                post_id = pair[1]
                self.add_connection(pre_neurons[pre_id], post_neurons[post_id], synapse_type)
            
            random.seed(None)

class NetworkGenerator:
    """
    Whenever you want to change your network, you need to add/remove connections
    using the previous NeuronNeuronConnector from which you took the configuration
    and applied it using the model during your last modification of the network.
    Otherwise, you just create a new NeuronNeuronConnector and configuration
    from the scratch and apply it.
    """
    def __init__(self):
        self.config = dyn1.Dynapse1Configuration()
        self.network = Network()

    def add_connection(self, pre, post, synapse_type):
        self.network.add_connection(pre, post, synapse_type)

    def remove_connection(self, pre, post, synapse_type):
        self.network.remove_connection(pre, post, synapse_type)
    
    def add_connections_from_list(self, pre_neurons, post_neurons, synapse_type, pre_ids, post_ids):
        self.network.add_connections_from_list(pre_neurons, post_neurons, synapse_type, pre_ids, post_ids)
    
    def remove_connections_from_list(self, pre_neurons, post_neurons, synapse_type, pre_ids, post_ids):
        self.network.remove_connections_from_list(pre_neurons, post_neurons, synapse_type, pre_ids, post_ids)
    
    def add_connections_from_type(self, pre_neurons, post_neurons, synapse_type, conn_type, p=1, rand_seed=None):
        self.network.add_connections_from_type(pre_neurons, post_neurons, synapse_type, conn_type, p, rand_seed)

    def clear_network(self):
        self.network.post_neuron_dict.clear()

    def print_network(self):
        print("Warning: print_network is deprecated and will be removed in a future release, use print(NetworkGenerator.network). Note: str(NetworkGenerator.network) gives you the string format of a network.")

        print(self.network)

    def make_dynapse1_configuration(self):
        '''
        check if the self.network is valid or not.
        If valid: convert it to a configuration
        If not: raise exception
        '''
        is_valid, large_conn_weight_dict = validate(self.network, MAX_NUM_CAMS)

        self.config = convert_validated_network2dynapse1_configuration(self.network, large_conn_weight_dict)
        # print("Converted the validated network to a Dynapse1 configuration!")

        return self.config

    def make_dynapse1_configuration_in_chip(self, chip_id):
        # first check if the neurons in the network are all in the chip
        post_neuron_dict = self.network.post_neuron_dict
        for post_chip_core in post_neuron_dict:
            # check chip id of the post neuron
            if post_chip_core[0] != chip_id:
                raise Exception("ERROR: network has neuron(s) outside chip "+str(chip_id)+"!")

            # check the chip ids of all the pre neurons of the post neurons
            post_neurons = post_neuron_dict[post_chip_core]
            for post_neuron in post_neurons:
                for pre_tag in post_neuron.incoming_connections:
                    pre_chip_spikegens = post_neuron.incoming_connections[pre_tag]
                    for pre_chip_spikegen in pre_chip_spikegens:
                        if pre_chip_spikegen[1] == False and pre_chip_spikegen[0] != chip_id:
                            raise Exception("ERROR: network has neuron(s) outside chip "+str(chip_id)+"!")

        print("Neurons in the network are all located in chip "+str(chip_id)+".")

        config = self.make_dynapse1_configuration()
        return config

    def make_dynapse1_configuration_in_core(self, chip_id, core_id):
        # first check if the neurons in the network are all in the core
        post_neuron_dict = self.network.post_neuron_dict
        for post_chip_core in post_neuron_dict:
            # check core and chip id of the post neuron
            if post_chip_core[0] != chip_id or post_chip_core[1] != core_id:
                raise Exception("ERROR: network has neuron(s) outside chip "
                                +str(chip_id)+", core "+str(core_id)+"!")

            # check the core and chip ids of all the pre neurons of the post neurons
            post_neurons = post_neuron_dict[post_chip_core]
            for post_neuron in post_neurons:
                for pre_tag in post_neuron.incoming_connections:
                    pre_chip_spikegens = post_neuron.incoming_connections[pre_tag]
                    for pre_chip_spikegen in pre_chip_spikegens:
                        if pre_chip_spikegen[1] == False:
                            # for all the physical neurons, check their core and chip ids.
                            chip = pre_chip_spikegen[0]
                            core = pre_tag[0]
                            if chip != chip_id or core != core_id:
                                raise Exception("ERROR: network has neuron(s) outside chip "
                                                +str(chip_id)+", core "+str(core_id)+"!")

        print("Neurons in the network are all located in chip "+str(chip_id)+", core "+str(core_id)+".")

        config = self.make_dynapse1_configuration()
        return config

def convert_incoming_conns_dict2list(incoming_connections_dict):
    """
    Convert (pre.core_id,pre.neuron_id,synapse_type): [(pre.chip_id, pre.is_spike_gen), (pre.chip_id, pre.is_spike_gen),...]
    to
    [(preNeuron1,synapseType1), (preNeuron1,synapseType2), (preNeuron1,synapseType2), (preNeuron2,synapseType1),...]
    """
    incoming_connections_list = []
    incoming_connections_str_list = []

    for pre_tag in incoming_connections_dict:
        core = pre_tag[0]
        neuron = pre_tag[1]
        syn_type = pre_tag[2]
        if syn_type == dyn1.Dynapse1SynType.NMDA:
            syn_str = "NMDA"
        elif syn_type == dyn1.Dynapse1SynType.AMPA:
            syn_str = "AMPA"
        elif syn_type == dyn1.Dynapse1SynType.GABA_B:
            syn_str = "GABA_B"
        elif syn_type == dyn1.Dynapse1SynType.GABA_A:
            syn_str = "GABA_A"

        pre_neurons = incoming_connections_dict[pre_tag]
        
        for pre_neuron in pre_neurons:
            chip = pre_neuron[0]
            is_spike_gen = pre_neuron[1]
            pre_neuron = Neuron(chip,core,neuron,is_spike_gen)
            incoming_connections_list.append((pre_neuron,syn_type))
            incoming_connections_str_list.append((repr(pre_neuron),syn_str))

    return incoming_connections_list, incoming_connections_str_list
    
def print_post_neuron_dict(post_neuron_dict):
    if len(post_neuron_dict.keys()) == 0:
        print("The network is empty!")
    else:
        print("Post neuron (ChipId,coreId,neuronId): incoming connections [(preNeuron,synapseType), ...]")
        dictionary_items = post_neuron_dict.items()
        sorted_items = sorted(dictionary_items)
        for item in sorted_items:
            post_neurons = item[1]
            for post in post_neurons:
                incoming_connections_list, incoming_connections_str_list = \
                    convert_incoming_conns_dict2list(post.incoming_connections)
                print(post+":", incoming_connections_str_list)