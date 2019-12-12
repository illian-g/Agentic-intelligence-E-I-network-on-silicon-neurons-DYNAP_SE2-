#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Apr  7 12:29:23 2019

The CtxctlController class is a wrapper around ctxctl python API that stores the
ctxctl model and handles the neuron connections.

@author: nrisi
"""
import numpy as np    
from ctxctl_contrib.CtxctlFPGA import CtxctlFPGA
from ctxctl_contrib.CtxctlCalibrator import CtxctlCalib

class CtxctlController(object):
    
    def __init__(self, 
                 backend='rpyc', 
                 path_bias=None,
                 path_rec=None,
                 path_fig=None,
                 path_calib=None,
                 verbose=False):
        """ This class is a wrapper around ctxctl functionalities. 
        Args:
            backend        (str): set it to 'ctxctl' if running in ctxctl console
                                set it to 'rpyc' if running with rpyc
            path_biases    (str): path to saved biases 
            path_rec       (str): path to output recordings
            verbose        (bool): if True more messages will be printed
        """
        self.verbose = verbose
        self.backend = backend
        
        self.path_bias = path_bias
        self.path_rec = path_rec
        self.path_fig = path_fig
        self.path_calib = path_calib
        
        self.NUM_NEURONS_PER_CORE = 256
        self.NUM_CORES_PER_CHIP = 4
        self.NUM_CHIPS_PER_BOARD = 4
        self.NUM_NEURONS_PER_CHIP = self.NUM_NEURONS_PER_CORE*self.NUM_CORES_PER_CHIP 
        self.NUM_NEURONS_PER_BOARD = self.NUM_NEURONS_PER_CHIP*self.NUM_CHIPS_PER_BOARD
        self.NUM_CAMS_PER_NEURON = 64
    
        if self.backend=='rpyc':
            from cortexcontrol.RpycConnector import RpycConnector
            self._c = RpycConnector().get_c()
            self._c.execute("import time")   
            self._c.execute("import numpy as np")     
            self.CtxDynapse = self._c.modules.CtxDynapse
            self._c.namespace['CtxDynapse'] = self.CtxDynapse
            self.CtxCtlTools = self._c.modules.CtxCtlTools
            self.NeuronNeuronConnector = self._c.modules.NeuronNeuronConnector
            self.SynType = self.CtxDynapse.DynapseCamType
            self.PyCtxUtils = self._c.modules.PyCtxUtils
        
        elif self.backend=='ctxctl':
            import NeuronNeuronConnector 
            import PyCtxUtils
            import CtxDynapse  
            import CtxCtlTools
            self._c = None
            self.CtxDynapse = CtxDynapse
            self.CtxCtlTools = CtxCtlTools
            self.NeuronNeuronConnector = NeuronNeuronConnector
            self.SynType = self.CtxDynapse.DynapseCamType           
            self.PyCtxUtils = PyCtxUtils 

        self._start_ctxctl()
        self.syn_type = {'PS_WEIGHT_EXC_F_N' : self.SynType.FAST_EXC,
                         'PS_WEIGHT_EXC_S_N' : self.SynType.SLOW_EXC,
                         'PS_WEIGHT_INH_F_N' : self.SynType.FAST_INH,
                         'PS_WEIGHT_INH_S_N' : self.SynType.SLOW_INH,
                    }
        
    def _reset_ctxctl(self):
        """ Reset cams, srams and model.
        """
        self.reset_cams()		
        self.reset_srams()		
        self.reset_model()		   
        
    def _start_ctxctl(self):
        # Reset cams, srams and model
        self._reset_ctxctl()
        self.groups = self.model.get_bias_groups()
        self.virtual_model = self.CtxDynapse.VirtualModel()
        self.virtual_neurons = self.virtual_model.get_neurons()
                
        # Ctxctl wrappers =====================================================
        self.fpga      = CtxctlFPGA(self.CtxDynapse)
        self.calibrator = CtxctlCalib(self.CtxDynapse, 
                                     self.PyCtxUtils, 
                                     self.fpga,
                                     rpyc_connection=self._c, 
                                     path_rec=self.path_rec, 
                                     path_bias=self.path_bias, 
                                     path_fig=self.path_fig,
                                     path_calib=self.path_calib)    
        #self.monitor   = CtxctlMonitor()
        
        print(self.__class__.__name__ + ' : Ctxctl initialized!') 

    def reset_model(self):		
        """ Reset the software model.		
        """		
        self.model = self.CtxDynapse.model		
        self.neurons = self.model.get_shadow_state_neurons()        		
        self.num_cams_used = {neuron_id_post : 0 for neuron_id_post in range(self.NUM_NEURONS_PER_BOARD)}		
        self.connector = self.NeuronNeuronConnector.DynapseConnector()		
        self.weights_lookup = {}
        self.synapse_lookup = {}     
                           
    def reset_cams(self):
        """ Reset all the cams for all the cores.
        """
        print(self.__class__.__name__+ ' : Clearing CAMs..')
        
        if self.backend=='ctxctl':
            for i in range(self.NUM_CHIPS_PER_BOARD):
                self.CtxDynapse.dynapse.clear_cam(i)
        elif self.backend=='rpyc':
            for i in range(self.NUM_CHIPS_PER_BOARD):
                self._c.namespace['i']=i
                self._c.execute('CtxDynapse.dynapse.clear_cam(i)')
        
        self.num_cams_used = {neuron_id_post : 0 for neuron_id_post in range(self.NUM_NEURONS_PER_BOARD)}
        print(self.__class__.__name__+ ' : done!')
                
    def reset_srams(self):
        """ Reset all srams for all the cores.
        """
        print(self.__class__.__name__+ ' : Clearing SRAMs..')
        
        if self.backend=='ctxctl':
            for i in range(self.NUM_CHIPS_PER_BOARD):
                self.CtxDynapse.dynapse.clear_sram(i)
                
        elif self.backend=='rpyc':
            for i in range(self.NUM_CHIPS_PER_BOARD):
                self._c.namespace['i']=i
                self._c.execute('CtxDynapse.dynapse.clear_sram(i)')
            
        print(self.__class__.__name__+ ' : done!')            

    def monitor(self, chip_id, neuron_id):
        """ Set which neuron to monitor with the oscilloscope.
        Args:
            chip_id (int): chip id
            neuron_id (int): neuron id within the chip [0:1024)
        """
        print(self.__class__.__name__+ ' : Monitoring neuron ' + str(neuron_id) +\
              ' in chip '+ str(chip_id))
        self.CtxDynapse.dynapse.monitor_neuron(chip_id,neuron_id)  
        print(self.__class__.__name__+ ' : Check trace on the oscilloscope! ')
        
    #TODO: Replace this with separate class
    def set_spikemonitor(self, neuron_ids):
        """ Initialize Ctxctl BufferedEventFilter with list of neuron ids to be 
        monitored.
        Args:
            neuron_ids (list): list of neuron ids in range [0:1024)
        """ 
        print(self.__class__.__name__+ ' : BufferEventFilter' )
        self.eventfilter = self.CtxDynapse.BufferedEventFilter(self.model, 
                                                               neuron_ids)        
        print(self.__class__.__name__+ ' : done!' )        
    
    #TODO: Remove this    
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
        chip = np.unique(np.array(pre) // self.NUM_NEURONS_PER_CHIP)
        assert len(chip)==1, "All pre neurons should be in one chip"
        
        print(self.name+'Setting SRAMs of chip '+str(chip[0]))
        self.CtxDynapse.dynapse.set_config_chip_id(chip[0])

        pre_core_id = np.unique(np.array(pre) // self.NUM_NEURONS_PER_CORE)
        assert len(pre_core_id)==1, "All pre neurons should be in one core"
        
        for idx_dyn in pre:
            pre_neuron_addr = idx_dyn % self.NUM_NEURONS_PER_CORE
            core_mask = 15
            self.CtxDynapse.dynapse.write_sram(pre_neuron_addr, sram_id, pre_core_id, sx, 
                                          dx, sy, dy, core_mask)     
        print(self.__class__.__name__ + ' : done!')
        
    
    def connect(self, pre, post, syn_type, syn_weight=1, connection_type='onchip', name=None):
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
        """
        if 0 in pre:
            raise Warning('Avoid using neuron id 0 as neuron pre')
            
        if self.backend=='ctxctl':
            if connection_type == 'virtual':
                for (pre_, post_) in zip(pre, post):
                    for n_cam in range(syn_weight):
                        neuron_pre = self.virtual_neurons[pre_]
                        neuron_pos = self.neurons[post_]
                        syn_type = syn_type
                        self.connector.add_virtual_connection(neuron_pre,neuron_pos, 
                                                              syn_type)
                        self.num_cams_used[post_] += 1
                print(self.__class__.__name__ + ' : Virtual connection created!')
                
            elif connection_type == 'onchip':
                neuron_pre = [self.neurons[idx] for idx in pre]
                neuron_pos = [self.neurons[idx] for idx in post]
                for post_ in post:
                    self.num_cams_used[post_] += 1
                self.connector.add_connection_from_list(neuron_pre, neuron_pos, 
                                                        [syn_type])
                print(self.__class__.__name__ + ' : Onchip connection created!')
                
            elif connection_type == 'offchip':   
                for i, (pre_id, pos_id) in enumerate(zip(pre, post)):
                    targetchip = post[i] // self.NUM_NEURONS_PER_CHIP   
                    self.CtxDynapse.dynapse.set_config_chip_id(targetchip)
                    for n_cam in range(syn_weight):
                        self.num_cams_used[pos_id] += 1
                        pre_id  = pre_id % self.NUM_NEURONS_PER_CHIP 
                        post_id = pos_id % self.NUM_NEURONS_PER_CHIP 
                        cam_id = self.num_cams_used[post_id]   
                        self.CtxDynapse.dynapse.write_cam(pre_id, pos_id, cam_id, 
                                                          syn_type)
                print(self.__class__.__name__ + ' : Offchip connection created!')
            else:
                raise ValueError
        
        elif self.backend=='rpyc':        
            self._c.namespace['connector'] = self.connector
            
            if connection_type == 'virtual':
                for (pre_, post_) in zip(pre, post):
                    for n_cam in range(syn_weight):
                        self._c.namespace['neuron_pre'] = self.virtual_neurons[pre_]
                        self._c.namespace['neuron_pos'] = self.neurons[post_]            
                        self._c.namespace['syn_type'] = syn_type 
                        self.num_cams_used[post_] += 1
                        self._c.execute("connector.add_virtual_connection(neuron_pre,neuron_pos, syn_type)")    
                print(self.__class__.__name__ + ' : Virtual connection created!')
            
            elif connection_type == 'onchip':
                neuron_pre = [self.neurons[idx] for idx in pre]
                neuron_pos = [self.neurons[idx] for idx in post]
                for post_ in post:
                    self.num_cams_used[post_] += 1      
                self._c.namespace['neuron_pre'] = neuron_pre
                self._c.namespace['neuron_pos'] = neuron_pos            
                self._c.namespace['syn_type'] = syn_type 
                self._c.execute("connector.add_connection_from_list(neuron_pre, neuron_pos, [syn_type])")         
                print(self.__class__.__name__ + ' : Onchip connection created!')
                    
            elif connection_type=='offchip':                 
                for i, (pre_id, pos_id) in enumerate(zip(pre, post)):
    
                    self._c.namespace['targetchip'] = post[i] // self.NUM_NEURONS_PER_CHIP   
                    self._c.execute("CtxDynapse.dynapse.set_config_chip_id(targetchip)")
                    for n_cam in range(syn_weight):
                        self.num_cams_used[pos_id] += 1
                        self._c.namespace['pre_id'] = pre_id % self.NUM_NEURONS_PER_CHIP 
                        self._c.namespace['pos_id'] = pos_id % self.NUM_NEURONS_PER_CHIP 
                        self._c.namespace['cam_id'] = self.num_cams_used[pos_id]   
                        self._c.namespace['syn_type'] = syn_type                          
                        self._c.execute("CtxDynapse.dynapse.write_cam(pre_id, pos_id, cam_id, syn_type)")
                print(self.__class__.__name__ + ' : Offchip connection created!')      
            else:
                raise ValueError
                        
        # Apply connections to the model:   
        self.model.apply_diff_state()
        
        # Update dictionary of weight matrices and synapse groups
        update_connections_lookup(self.weights_lookup, self.synapse_lookup, pre, post, name)

    def remove_connection(self, pre, post):
        """ Remove connections from list.
        This funcion expects as many pairs of pre post in the input list as the
        number of connections between pre and post. 
        Args:
            pre                           (list): neuron ids of neurons pre [0:4095)
            post                          (list): neuron ids of neurons post [0:4095)
            connection_type             (string): 'virtual' or 'onchip' or 'offchip'
        """ 
        print(self.__class__.__name__+ ' : Removing connections..' )
        if self.backend=='ctxctl':
            for (pre_, post_) in zip(pre, post):
                if self.neurons[pre_].is_virtual():
                    self.connector.remove_virtual_connection(self.virtual_neurons[pre_], 
                                                             self.neurons[post_])                                                            
                else:
                    self.connector.remove_connection(self.neurons[pre_], 
                                                     self.neurons[post_]) 
                self.num_cams_used[post_] -= 1
        
        elif self.backend=='rpyc':
            self._c.namespace['connector'] = self.connector
            for (pre_, post_) in zip(pre, post):
                self._c.namespace['neuron_post'] = self.neurons[post_]
                if self.neurons[pre_].is_virtual():
                    self._c.namespace['neuron_pre'] = self.virtual_neurons[pre_]
                    self._c.execute('connector.remove_virtual_connection(neuron_pre, neuron_post)')
                else:
                    self._c.namespace['neuron_pre'] = self.neurons[pre_]
                    self._c.execute('connector.remove_connection(neuron_pre, neuron_post)')
                self.num_cams_used[post_] -= 1            
            
        self.model.apply_diff_state()
        print(self.__class__.__name__+ ' : done!' )
        
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
        cams_id = [cams[cam_id].get_pre_neuron_id()+self.NUM_NEURONS_PER_CORE*cams[cam_id].get_pre_neuron_core_id() for cam_id in range(self.NUM_CAMS_PER_NEURON)]
        
        return cams_id
    
    def get_connectivity_matrix(self):
        """ Get connectivity board matrix
        """
        weight_matrix = np.zeros((self.NUM_NEURONS_PER_BOARD, self.NUM_NEURONS_PER_BOARD))
        for key in self.connector.receiving_connections_from.keys():
            nrn_id_post = key.get_neuron_id() + key.get_core_id()*self.NUM_NEURONS_PER_CORE + key.get_chip_id()*self.NUM_NEURONS_PER_CHIP 
            list_neurons_pre = self.connector.receiving_connections_from[key]
            list_neuron_ids = []
            for nrn in list_neurons_pre:
                list_neuron_ids.append(nrn.get_neuron_id() + nrn.get_core_id()*self.NUM_NEURONS_PER_CORE + nrn.get_chip_id()*self.NUM_NEURONS_PER_CHIP )
            weight_matrix[:, nrn_id_post] = np.bincount(list_neuron_ids, 
                        minlength=self.NUM_NEURONS_PER_BOARD) 
        
        return weight_matrix

def update_connections_lookup(dict_weights, dict_synapse, pre, post, synapse_name):
    """ This updates the dictionary of weights, synapse_gorups and neurons_tags
    (is_pre, is_post)
    """
    # Update dictionary of synapse groups
    if not(synapse_name in dict_synapse.keys()):
        dict_synapse[synapse_name] = (pre, post)
        
    # Update dictionary of weights
    for pre_, post_ in zip(pre, post):
        if (pre_, post_) in dict_weights.keys():
            dict_weights[(pre_, post_)][1] +=1
        else:
            dict_weights[(pre_, post_)] = (synapse_name, 1)
            