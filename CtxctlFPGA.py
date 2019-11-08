#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov  7 16:02:57 2019

The CtxctlFPGA class is a wrapper around ctxctl python API that handles the 
inputs from FPGA (Poisson or SpikeGenerator).

@author: nrisi
"""

import numpy as np

class CtxctlFPGA(object):
    
    def __init__(self, dynapse, neurons_pre=[]):
        """
        Args:
            dynapse              low level class of dynapse
            neurons_pre             (list): list of input neuron ids (in range [0:1023])
        """
        print(self.__class__.__name__ + ' __init__()')
        
        self.dynapse = dynapse
        self.neurons_pre = neurons_pre
        self.model = self.dynapse.model
        
        # Set FPGA constraints
        ADDR_NUM_BITS = 15
        ISI_NUM_BITS = 16
        self.max_fpga_len = 2**ADDR_NUM_BITS-1
        self.max_isi = 2**ISI_NUM_BITS-1 
        self.fpgaModules = self.model.get_fpga_modules()
        self.poissGen = self.fpgaModules[0]
        self.spikeGen = self.fpgaModules[1]
    
    def set_spikeGen(self, spike_times, neuron_ids, target_chips, isi_base, 
                     repeat_mode=False):
        """
        This sets the FpgaSpikeGen object.
        Args:
            spike_times    (list): list of input spike times, in sec
            neuron_ids     (list): list of input neuron ids sorted according to 
                                time of spike
            target_chip    (list): list of target chip to which each event will be
                                sent.
            isi_base        (int): 90 or 900 (See below)
            repeat_mode    (bool): If repeat is True, the spike generator will 
                                loop from the beginning when it reaches the end 
                                of the stimulus.                    
        This function sets the SpikeGenerator object given a list of spike times, 
        in sec, correspondent input neuron ids and the target chips, i.e. the
        chip destination of each input event. 
        
        About  **** isi_base ****:
        Given a list of spike times (in sec) a list of isi (Inter Stimulus Interval) 
        is generated. Given a list of isi, the resulting list of isi set from the 
        FPGA will be:
            isi*unit_fpga
        with             
            unit_fpga = isi_base/90 * us    
            
        Thus, given a list of spike_times in sec:
            - first the spike times are converted in us
            - then a list of isi (in us) is generated
            - then the list of isi is divided by the unit_fpga (so that the
               resulting list of isi set on FPGA will have the correct unit
               given the input isi_base)        
        E.g.: if isi_base=900 the list of generated isi will be multiplied on
        FPGA by 900/90 us = 10 us
        
        """
        assert all(np.sort(spike_times)==(spike_times)), 'Spike times must be sorted!'
        assert(len(neuron_ids)==len(spike_times)==len(target_chips)), 'Spike times '+\
            ' and neuron ids need to have the same length'
        
        unit_fpga = isi_base/90 #us
        spike_times_us = np.array(spike_times)*1e6
        spike_times_unit_fpga = spike_times_us / unit_fpga
        
        fpga_isi = np.array([0]+list(np.diff(spike_times_unit_fpga)), dtype=int)
        fpga_nrn_ids = np.array(neuron_ids)
        fpga_target_chips = np.array(target_chips)
        
        fpga_events = []
        for idx_isi, isi in enumerate(fpga_isi):
            fpga_event = self.dynapse.FpgaSpikeEvent()
            fpga_event.core_mask = 15
            fpga_event.target_chip = fpga_target_chips[idx_isi]
            fpga_event.neuron_id = fpga_nrn_ids[idx_isi]
            fpga_event.isi = isi
            fpga_events.append(fpga_event)
            
        assert all(np.asarray(fpga_isi) < self.max_isi), 'isi is too large for'+\
                'the specified isi_base!'
        assert len(fpga_isi) < self.max_fpga_len , 'Input stimulus is too long!'
        
        # Set spikeGen:
        self.spikeGen.set_variable_isi(True)
        self.spikeGen.preload_stimulus(fpga_events)
        self.spikeGen.set_isi_multiplier(isi_base)
        self.spikeGen.set_repeat_mode(repeat_mode)       

        print(self.__class__.__name__ + ': FpgaSpikeGen set')
        print(self.__class__.__name__ + ': To start: self.spikeGen.start()')
        print(self.__class__.__name__ + ': To stop: self.spikeGen.stop()')
        
    def set_poissGen(self, poisson_rates_hz, neuron_ids, target_chip, reset=True):
        """
        This sets the PoissonGen object.
        Args:
            poisson_rates_hz (list): list of poisson mean firing rate
            neuron_ids       (list): list of input neuron ids
            target_chip       (int): chip id that the PoissonSpikeGen will target
        """
        self.poissGen.set_chip_id(target_chip)  
        
        assert(len(poisson_rates_hz)==len(neuron_ids)), 'Input lists need to have the same length'
        
        if reset:
        # Reset to zero neurons for which the poisson mean firing rate
        # is not explicitely set.
            non_defined_neurons = set(self.neurons_pre)-set(neuron_ids)
            if non_defined_neurons:
                print(self.__class__.__name__ + ': Setting to 0 Hz non specified neurons')
                for nrn_id in non_defined_neurons:
                    self.poissGen.write_poisson_rate_hz(nrn_id, 0)
        
        # Set mean poisson firing rate of selected neurons
        for nrn_id, rateHz in zip(neuron_ids, poisson_rates_hz):
            self.poissGen.write_poisson_rate_hz(nrn_id, rateHz)
        
        print(self.__class__.__name__ + ': PoissonGen set')
        print(self.__class__.__name__ + ': To start: self.poissGen.start()')            
        print(self.__class__.__name__ + ': To start: self.poissGen.stop()')       
        
