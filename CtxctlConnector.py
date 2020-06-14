#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb  6 10:51:59 2020

Wrapper around NeuronNeuronConnector class
@author: nrisi
"""

import numpy as np
from ctxctl_contrib.constants import NUM_NEURONS_PER_BOARD, NUM_CORES_PER_CHIP,\
                                    NUM_NEURONS_PER_CORE, NUM_NEURONS_PER_CHIP, \
                                    NUM_CAMS_PER_NEURON

class CtxcctlConnector(object):
    
    def __init__(self, CtxDynapse, CtxConnector, neurons, virtual_neurons, _c=None, 
                 verbose=False):
        """
        Args:
            CtxDynapse           low level class of dynapse model
            CtxConnector         Ctxctl NeuronNeuronConnector object
            neurons              Ctxctl neuron object
            vittual_neurons      Ctxctl virtual neurons
            _c                   (rpyc connection): if backend=ctxctl _c=None (default type)
        """
        self.name = self.__class__.__name__+' : __init__()'
        if verbose:
            print(self.__class__.__name__+' : __init__()')
        self.CtxDynapse = CtxDynapse
        self.model = self.CtxDynapse.model              

        self.neurons = neurons
        self.virtual_neurons = virtual_neurons
        self.CtxConnector = CtxConnector.DynapseConnector()
        self._c = _c
        
        self.num_cams_used = {neuron_id_post : 0 for neuron_id_post in range(NUM_NEURONS_PER_BOARD)}
        self.offchip_cams_id = {neuron_id_post : [] for neuron_id_post in range(NUM_NEURONS_PER_BOARD)}
        self.weights_lookup = {}
        self.synapse_lookup = {}
        
    def clash_checker(self, neuron_ids):
        """
        For every neuron, we check the CAMS, and then of those neurons we check the SRAMS

        Parameters:
            neuron_id (int) : neuron to analyze
        Returns:
            check (bool) : False if no cam clashes
        """
        check = False

        for neuron_id in neuron_ids:
            print(self.__class__.__name__ + ' : clash checker, checking neuron: {}' .format(neuron_id))

            #chip_id = int(neuron_id / 1024)
            #core_id = int((neuron_id - chip_id * 1024) / 256)
#            dpi_id = neuron_id % 256
            unique_connections = np.trim_zeros(self.get_cams(neuron_id))

            for unique_id in unique_connections:
                possible_cam_clashes = [unique_id, unique_id + NUM_NEURONS_PER_CHIP, unique_id + NUM_NEURONS_PER_CHIP * 2, unique_id + NUM_NEURONS_PER_CHIP * 3]
#                if (dpi_id in possible_cam_clashes):
#                    print(self.__class__.__name__ + ' : There could be a clash involving post neuron: {}!'.format(neuron_id))
#                    print(self.__class__.__name__ + ' : Two neurons with the same number but on different chips are connected to each other ')
#                    check = True
                neurons = []
                target_cores = []
                for neu in possible_cam_clashes:
                    target_chip, core_mask = self.get_srams(neu)
                    for pos, mask in enumerate((core_mask[1:4])):
                        if mask != 0: #one hot: not targeting any core
                            target_cores.append(list(core_mask_to_core_number(mask) +\
                             (NUM_CORES_PER_CHIP*target_chip[pos+1]))[0])
                            neurons.append(unique_id)
                compressed = list(zip(neurons, target_cores))
                unique_list = list(set(compressed))
                if len(compressed) != len(unique_list):
                    print(self.__class__.__name__ + " : There could be a clash involving post neuron: {}" .format(neuron_id))
                    print(self.__class__.__name__ + ' : Two neurons with the same number but on different chips are connected to the same neuron')
                    check = True
                    print(compressed)

        return check
        
    def get_connectivity_matrix(self):
        """ Get connectivity board matrix
        """
        weight_matrix = np.zeros((NUM_NEURONS_PER_BOARD, NUM_NEURONS_PER_BOARD))
        for key in self.CtxConnector.receiving_connections_from.keys():
            nrn_id_post = key.get_neuron_id() + key.get_core_id()*NUM_NEURONS_PER_CORE + key.get_chip_id()*NUM_NEURONS_PER_CHIP
            list_neurons_pre = self.CtxConnector.receiving_connections_from[key]
            list_neuron_ids = []
            for nrn in list_neurons_pre:
                list_neuron_ids.append(nrn.get_neuron_id() + nrn.get_core_id()*NUM_NEURONS_PER_CORE + nrn.get_chip_id()*NUM_NEURONS_PER_CHIP )
            weight_matrix[:, nrn_id_post] = np.bincount(list_neuron_ids,
                        minlength=NUM_NEURONS_PER_BOARD)

        return weight_matrix

    def write_sram(self, pre, sy, dy, sx, dx, sram_id=2):
        """ Write SRAM for a list of neurons.
        Args:
            pre (list): list of neuron ids (in the same chip!) that send out
            spikes [0:4096]
            sy, dy, sx, dx (int): see 6 bit header below
        NOTE:
            SRAM is a 20 bit string with:
                - 10-bit for the tag address
                        2-bit core id of pre (pre_core_id)
                        8-bit neuron id of pre (pre_neuron_addr)
                - 6 bit header:
                        2-bit: dx
                        2-bit: dy
                        1-bit: sx
                        1-bit: sy
                - 4 bit header:
                        4 bit: core_mask (target core)
        Every neuron can send spikes up to 3 different chips (1 of the 4 srams
        is used to send spikes to the fpga on the board)
        """

        #TODO: Add wrapper to this to be able to set srams of neurons from multiple
        # chips and multiple cores
        print(self.__class__.__name__ + ' : Writing SRAMs')
        chip = np.unique(np.array(pre) // NUM_NEURONS_PER_CHIP)
        assert len(chip)==1, "All pre neurons should be in one chip"

        print(self.name+'Setting SRAMs of chip '+str(chip[0]))
        self.CtxDynapse.dynapse.set_config_chip_id(chip[0])

        pre_core_id = np.unique(np.array(pre) // NUM_NEURONS_PER_CORE)
        assert len(pre_core_id)==1, "All pre neurons should be in one core"

        for idx_dyn in pre:
            pre_neuron_addr = idx_dyn % NUM_NEURONS_PER_CORE
            core_mask = 15
            self.CtxDynapse.dynapse.write_sram(pre_neuron_addr, sram_id, pre_core_id, sx,
                                          dx, sy, dy, core_mask)
        print(self.__class__.__name__ + ' : done!')
        
    def connect(self, pre, post, syn_type, syn_weight=1, connection_type='onchip', name=None, verbose=False):
        """ Connect neurons from list.
        Args:
            pre                           (list): neuron ids of neurons pre [0:4095)
            post                          (list): neuron ids of neurons post [0:4095)
            syn_type (CtxDynapse.DynapseCamType): Ctxctl synapse type
                                            (e.g. syn_type=FAST_EXC)
            syn_weight                     (int): number of cams per connection
            connection_type             (string): three options are supported.
                                            - 'virtual' : if neurons pre are on fpga
                                            - 'onchip'  : if neurons pre are on chip
                                            - 'offchip' : this uses the ctxctl low level
                                            functions to connect neurons (which is
                                            used for example to connect neurons on
                                            dynapse board to neurons on an external
                                            fpga or to connect chips on differernt
                                            boards.)
            name                           (str): synapse name
            verbose                        (bool): if True, a print with the connection 
                                            created will be shown
        """
        if verbose:
            print(self.__class__.__name__ + ' : creating connection ' + name )
        if not(name):
            num_syn_created=len(self.synapse_lookup.keys())
            name='Connection_'+str(num_syn_created)
            
        if 0 in pre:
            raise Warning('Avoid using neuron id 0 as neuron pre')

        if self._c:
            self._c.namespace['CtxConnector'] = self.CtxConnector

            if connection_type == 'virtual':
                for (pre_, post_) in zip(pre, post):
                    for n_cam in range(syn_weight):
                        self._c.namespace['neuron_pre'] = self.virtual_neurons[pre_]
                        self._c.namespace['neuron_pos'] = self.neurons[post_]
                        self._c.namespace['syn_type'] = syn_type
                        self.num_cams_used[post_] += 1
                        self._c.execute("CtxConnector.add_virtual_connection(neuron_pre,neuron_pos, syn_type)")
                print(self.__class__.__name__ + ' : Virtual connection created!')

            elif connection_type == 'onchip':
                neuron_pre = [self.neurons[idx] for idx in pre]
                neuron_pos = [self.neurons[idx] for idx in post]
                for post_ in post:
                    self.num_cams_used[post_] += 1
                self._c.namespace['neuron_pre'] = neuron_pre
                self._c.namespace['neuron_pos'] = neuron_pos
                self._c.namespace['syn_type'] = syn_type
                self._c.execute("CtxConnector.add_connection_from_list(neuron_pre, neuron_pos, [syn_type])")
                print(self.__class__.__name__ + ' : Onchip connection created!')

            elif connection_type=='offchip':
                for i, (pre_id, pos_id) in enumerate(zip(pre, post)):

                    self._c.namespace['targetchip'] = post[i] // NUM_NEURONS_PER_CHIP
                    self._c.execute("CtxDynapse.dynapse.set_config_chip_id(targetchip)")
                    for n_cam in range(syn_weight): 
                        self._c.namespace['post_cam_id'] = self.neurons[pos_id].get_cams()[self.num_cams_used[pos_id]]
                        self._c.namespace['pre_neuron_id'] = pre_id % NUM_NEURONS_PER_CORE
                        self._c.namespace['pre_core_id'] = pre_id // NUM_NEURONS_PER_CORE
                        self._c.execute("post_cam_id.set_pre_neuron_id(pre_neuron_id)")
                        self._c.execute("post_cam_id.set_pre_neuron_core_id(pre_core_id)")
                        self._c.namespace['syn_type'] = syn_type
                        self._c.execute("post_cam_id.set_type(syn_type)")
                        
                        self.num_cams_used[pos_id] += 1
                        self.offchip_cams_id[pos_id].append(pre_id)
                        
                print(self.__class__.__name__ + ' : Offchip connection created!')
            else:
                raise ValueError
        else:
            if connection_type == 'virtual':
                for (pre_, post_) in zip(pre, post):
                    for n_cam in range(syn_weight):
                        neuron_pre = self.virtual_neurons[pre_]
                        neuron_pos = self.neurons[post_]
                        syn_type = syn_type
                        self.CtxConnector.add_virtual_connection(neuron_pre,neuron_pos,
                                                              syn_type)
                        self.num_cams_used[post_] += 1
                print(self.__class__.__name__ + ' : Virtual connection created!')

            elif connection_type == 'onchip':
                neuron_pre = [self.neurons[idx] for idx in pre]
                neuron_pos = [self.neurons[idx] for idx in post]
                for post_ in post:
                    self.num_cams_used[post_] += 1
                self.CtxConnector.add_connection_from_list(neuron_pre, neuron_pos,
                                                        [syn_type])
                print(self.__class__.__name__ + ' : Onchip connection created!')

            elif connection_type == 'offchip':
                for i, (pre_id, pos_id) in enumerate(zip(pre, post)):
                    targetchip = post[i] // NUM_NEURONS_PER_CHIP
                    self.CtxDynapse.dynapse.set_config_chip_id(targetchip)
                    for n_cam in range(syn_weight):
                        post_cam_id = self.neurons[pos_id].get_cams()[self.num_cams_used[pos_id]]
                        pre_neuron_id = pre_id % NUM_NEURONS_PER_CORE
                        pre_core_id = pre_id // NUM_NEURONS_PER_CORE
                        post_cam_id.set_pre_neuron_id(pre_neuron_id)
                        post_cam_id.set_pre_neuron_core_id(pre_core_id)
                        syn_type = syn_type
                        post_cam_id.set_type(syn_type)
                        
                        self.num_cams_used[pos_id] += 1
                        self.offchip_cams_id[pos_id].append(pre_id)
                print(self.__class__.__name__ + ' : Offchip connection created!')
            else:
                raise ValueError
        
        # Apply connections to the model:
        self.model.apply_diff_state()

        # Update dictionary of weight matrices and synapse groups
        if connection_type=='onchip':
            update_connections_lookup('connect', self.weights_lookup, self.synapse_lookup, pre, post, name)

    def remove_connection(self, pre, post, verbose=False):
        """ Remove connections from list.
        This funcion expects as many pairs of pre post in the input list as the
        number of connections between pre and post.
        Args:
            pre                           (list): neuron ids of neurons pre [0:4095)
            post                          (list): neuron ids of neurons post [0:4095)
            connection_type             (string): 'virtual' or 'onchip' or 'offchip'
        """
        if self._c:
            self._c.namespace['CtxConnector'] = self.CtxConnector
            for (pre_, post_) in zip(pre, post):
                self._c.namespace['neuron_post'] = self.neurons[post_]
                if self.neurons[pre_].is_virtual():
                    self._c.namespace['neuron_pre'] = self.virtual_neurons[pre_]
                    self._c.execute('CtxConnector.remove_virtual_connection(neuron_pre, neuron_post)')
                else:
                    self._c.namespace['neuron_pre'] = self.neurons[pre_]
                    self._c.execute('CtxConnector.remove_connection(neuron_pre, neuron_post)')
                self.num_cams_used[post_] -= 1
        else:
            for (pre_, post_) in zip(pre, post):
                if self.neurons[pre_].is_virtual():
                    self.CtxConnector.remove_virtual_connection(self.virtual_neurons[pre_],
                                                             self.neurons[post_])
                else:
                    self.CtxConnector.remove_connection(self.neurons[pre_],
                                                     self.neurons[post_])
                self.num_cams_used[post_] -= 1
               
        self.model.apply_diff_state()
        
        try:
            # If this runs the connection must be onchip, otherwise it raises an
            # error since the pairs (pre, post) must be unique to avoid cam clash
            # And so if there is a pair pre, post it must be onchip and therefore
            # it can be correctly removed from the dictionary
            update_connections_lookup('remove', self.weights_lookup, self.synapse_lookup, pre, post)
        except:
            # For virtual or offchip connections there is no record kept in the 
            # dictionary
            pass
            
        print(self.__class__.__name__+ ' : Connection removed!' )        
        
    def get_cams(self, neuron_id):
        """ Returns the list of cams for the input neuron.
        Args:
            neuron_id (int): neuron id (in range [0:4096))
        Returns:
            list_cams (list): list of cams set for the selected neuron id.

        Note: cams are stored as a string of 10 bit (i.e. cam ids are in range
        [0:1024) ). Therefore, each cam id stores only the information about
        where the neuron pre is located within the chip but it does not contain
        the information about which chip the neuron pre (of the selected cam)
        belongs to.
        """
        cams = self.neurons[neuron_id].get_cams()
        cams_id = [cams[cam_id].get_pre_neuron_id()+NUM_NEURONS_PER_CORE*cams[cam_id].get_pre_neuron_core_id() for cam_id in range(NUM_CAMS_PER_NEURON)]

        return cams_id

    def get_srams(self, neuron_id):
        """
        This function checks the srams and returns the target chip and the mask
        representing the cores the events are broadcasted too.

        Parameters:
            Neuron_id (int) : Neuron id
        Returns:
            target_chip (list) : 0-4number of target chip
            core_mask (list) : 0-16 binary representation of the 4 cores on the chip

        """
        cms = self.neurons[neuron_id].get_srams()

        target_chip = []
        core_mask = []
        for i in range(len(cms)):
            target_chip = np.append(target_chip, (cms[i].get_target_chip_id()))
            core_mask = np.append(core_mask, (cms[i].get_core_mask()))

        target_chip = np.array(target_chip)
        core_mask = np.array(core_mask)

        return target_chip, core_mask        

#%% Utils:    
def update_connections_lookup(action_type, dict_weights, dict_synapse, pre, post, synapse_name=None):
    """ This updates the dictionary of weights, synapse_gorups and neurons_tags
    (is_pre, is_post)
    Args:
        action_type (str): 'connect' or 'remove'
        dict_weights (dict): dictionary with tuple of (pre, post) as keys and 
                            connection name and weight as values.
        pre,                     
    """
    if action_type=='connect':
        # Update dictionary of synapses:
        if synapse_name not in dict_synapse.keys():
            dict_synapse[synapse_name]=(pre, post)
        else:
            # append indices to existing synapse type:
            pre_ = dict_synapse[synapse_name][0].extend(pre)
            post_ = dict_synapse[synapse_name][0].extend(post)
            dict_synapse[synapse_name] = (pre_, post_)
            
        # Update dictionary of weights
        for pre_, post_ in zip(pre, post):
            if (pre_, post_) in dict_weights.keys():
                # Replace dict value with updated tuple
                dict_weights[(pre_, post_)] = (synapse_name, dict_weights[(pre_, post_)][1] + 1)
            else:
                dict_weights[(pre_, post_)] = (synapse_name, 1)
    
    elif action_type=='remove':        

        for pre_, post_ in zip(pre, post):
            
            
            if (pre_, post_) in dict_weights.keys(): # if there is a connection
                
                # Get synapse name:
                synapse_name = dict_weights[(pre_, post_)][0]
                
                # Update dictionary of weights: ================================
                if dict_weights[(pre_, post_)][1]>1:
                    
                    # Decrease number of connections
                    dict_weights[(pre_, post_)] = (synapse_name, dict_weights[(pre_, post_)][1] - 1)
                    
                else:
                    # remove pair pre post from dictionary key:
                    del dict_weights[(pre_, post_)]
                # ==============================================================
                
                # Update dictionary of synapses: ===============================
                list_current_pres = dict_synapse[synapse_name][0]
                list_current_posts = dict_synapse[synapse_name][1]
                list_current_pres.remove(pre_)
                list_current_posts.remove(post_)
                if not( list_current_pres and list_current_posts ): 
                    del dict_synapse[synapse_name]
                else:
                    dict_synapse[synapse_name] = (list_current_pres, list_current_posts)
                # ==============================================================

            else:
                # Connection not existing
                raise ValueError       
                
def core_mask_to_core_number(core_mask):
    """
    This function returns the core represented by the binary representation encoded in the SRAMS.
    """
    bin_mask = bin(int(core_mask))
    core_number = []
    try:
        if (bin_mask[-4] == '1'):
            core_number.append(3)
    except:
        pass
    try:
        if (bin_mask[-3] == '1'):
            core_number.append(2)
    except:
        pass

    try:
        if (bin_mask[-2] == '1'):
            core_number.append(1)
    except:
        pass

    try:
        if (bin_mask[-1] == '1'):
            core_number.append(0)
    except:
        pass
    return core_number