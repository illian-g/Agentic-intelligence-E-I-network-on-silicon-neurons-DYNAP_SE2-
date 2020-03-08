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
from ctxctl_contrib.CtxctlConnector import CtxcctlConnector
from ctxctl_contrib.constants import *

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
        if verbose:
            print(self.__class__.__name__+' : __init__()')
        self.backend = backend
        self.ctxctl_started=False
        
        self.path_bias = path_bias
        self.path_rec = path_rec
        self.path_fig = path_fig
        self.path_calib = path_calib

        if self.backend=='rpyc':
            from ctxctl_contrib.RpycConnector import RpycConnector
            self._c = RpycConnector().get_c()
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

    def reset_model(self):
        """ Reset the software model.
        """
        self.model = self.CtxDynapse.model
        self.neurons = self.model.get_shadow_state_neurons()
        if self.ctxctl_started:
            self.connector.num_cams_used = {neuron_id_post : 0 for neuron_id_post in range(NUM_NEURONS_PER_BOARD)}
            self.connector.weights_lookup = {}
            self.connector.synapse_lookup = {}

    def reset_cams(self):
        """ Reset all the cams for all the cores.
        """
        print(self.__class__.__name__+ ' : Clearing CAMs..')

        if self.backend=='ctxctl':
            for i in range(NUM_CHIPS_PER_BOARD):
                self.CtxDynapse.dynapse.clear_cam(i)
        elif self.backend=='rpyc':
            for i in range(NUM_CHIPS_PER_BOARD):
                self._c.namespace['i']=i
                self._c.execute('CtxDynapse.dynapse.clear_cam(i)')
            
        print(self.__class__.__name__+ ' : done!')

    def reset_srams(self):
        """ Reset all srams for all the cores.
        """
        print(self.__class__.__name__+ ' : Clearing SRAMs..')

        if self.backend=='ctxctl':
            for i in range(NUM_CHIPS_PER_BOARD):
                self.CtxDynapse.dynapse.clear_sram(i)

        elif self.backend=='rpyc':
            for i in range(NUM_CHIPS_PER_BOARD):
                self._c.namespace['i']=i
                self._c.execute('CtxDynapse.dynapse.clear_sram(i)')
        print(self.__class__.__name__+ ' : done!') 
               
    def _reset_ctxctl(self):
        """ Reset cams, srams and model.
        """
        print(self.__class__.__name__+ ' : Reset')
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
        self.fpga      = CtxctlFPGA(self.CtxDynapse,
                                    verbose=self.verbose)
        self.calibrator = CtxctlCalib(self.CtxDynapse,
                                     self.PyCtxUtils,
                                     self.fpga,
                                     rpyc_connection=self._c,
                                     path_rec=self.path_rec,
                                     path_bias=self.path_bias,
                                     path_fig=self.path_fig,
                                     path_calib=self.path_calib, 
                                     verbose=self.verbose)
        self.connector = CtxcctlConnector(self.CtxDynapse, 
                                          self.NeuronNeuronConnector,
                                          self.neurons, 
                                          self.virtual_neurons,
                                          _c=self._c, 
                                          verbose=self.verbose)
        
        #self.monitor   = CtxctlMonitor()
        self.ctxctl_started=True
        print(self.__class__.__name__ + ' : Ctxctl initialized!')

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