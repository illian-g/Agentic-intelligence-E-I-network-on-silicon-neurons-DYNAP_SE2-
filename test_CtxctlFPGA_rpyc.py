#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov  7 17:46:24 2019

Example for class CtxctlFPGA (backend: rpyc).
Check the expected stimulus with the oscilloscope.

@author: nrisi
"""

import unittest
from ctxctl_contrib.CtxctlController import CtxctlController
import os
import time
import numpy as np

SHOW_PLOTS_IN_TESTS = True

class TestCtxctlFPGA(unittest.TestCase):
    
    def test___init__(self):
        print(self.__class__.__name__ + ' : __init__')
        print(self.__class__.__name__ + ' : Testing backend: rpyc')
    
    def test_spikeGen(self):
        print(self.__class__.__name__ + ' : test_spikeGen')
        cc = CtxctlController(backend='rpyc')
        pre = list(range(1,256))
        post = list(range(1, 256))

        # Connect neurons to input neurons on FPGA with one to one connections
        cc.connect(pre, post, syn_type=cc.SynType.FAST_EXC, 
                   syn_weight=1, 
                   connection_type='virtual')
        
        # Load biases
        #TODO: Replace this with functions from calibrator
        for target_core in range(16):
            cc.CtxDynapse.dynapse.set_tau_2(target_core//4,0) # silence neuron 0
            cc.groups[target_core].set_bias("IF_DC_P", 0, 0)  
            cc.groups[target_core].set_bias("IF_AHTAU_N", 255, 7)
            cc.groups[target_core].set_bias("IF_AHTHR_N", 80, 3)
            cc.groups[target_core].set_bias("IF_AHW_P", 0, 0)
            cc.groups[target_core].set_bias("IF_BUF_P", 80, 4)
            cc.groups[target_core].set_bias("IF_CASC_N", 0, 0)
            cc.groups[target_core].set_bias("IF_DC_P", 0, 0)
            cc.groups[target_core].set_bias("IF_NMDA_N", 0, 0)
            cc.groups[target_core].set_bias("IF_RFR_N", 140, 3)
            cc.groups[target_core].set_bias("IF_TAU1_N", 95, 5)
            cc.groups[target_core].set_bias("IF_TAU2_N", 35, 7)
            cc.groups[target_core].set_bias("IF_THR_N", 30, 2)
            cc.groups[target_core].set_bias("NPDPIE_TAU_F_P", 20, 2)
            cc.groups[target_core].set_bias("NPDPIE_TAU_F_P", 20, 2)
            cc.groups[target_core].set_bias("NPDPIE_TAU_S_P", 20, 2)
            cc.groups[target_core].set_bias("NPDPIE_THR_F_P", 115, 2)
            cc.groups[target_core].set_bias("NPDPIE_THR_S_P", 115, 2)
            cc.groups[target_core].set_bias("NPDPII_TAU_F_P", 20, 2)
            cc.groups[target_core].set_bias("NPDPII_TAU_S_P", 20, 2)
            cc.groups[target_core].set_bias("NPDPII_THR_F_P", 115, 2)
            cc.groups[target_core].set_bias("NPDPII_THR_S_P", 115, 2)
            cc.groups[target_core].set_bias("PS_WEIGHT_EXC_F_N", 255, 7)
            cc.groups[target_core].set_bias("PS_WEIGHT_EXC_S_N", 0, 0)
            cc.groups[target_core].set_bias("PS_WEIGHT_INH_F_N", 0, 0)
            cc.groups[target_core].set_bias("PS_WEIGHT_INH_S_N", 0, 0)
            cc.groups[target_core].set_bias("PULSE_PWLK_P", 86, 2)
            cc.groups[target_core].set_bias("R2R_P", 85, 3)
        
        # =====================================================================
        cc.fpga.neurons = pre
        # Create a spike train from 0 to 3 sec with 16 neurons firing one at 
        # a time.
        spike_times = np.linspace(0, 3, 16)
        neuron_ids = pre[0:16]
        # All neurons post are in chip 0
        target_chips = [0]*len(neuron_ids)
        isi_base = 900 
        cc.fpga.set_spikeGen(spike_times, neuron_ids, target_chips, isi_base)
        
        print(self.__class__.__name__ + ' : Check spikes in core 0')
        cc.fpga.spikeGen.start()
        time.sleep(3)
        cc.fpga.spikeGen.stop()
        # =====================================================================
        
#    def test_poissGen(self):              
#        print(self.__class__.__name__ + ' : test_poissonGen')
#        cc = CtxctlController(backend='rpyc')
#        pre = list(range(256,256+256))
#        post = list(range(256, 256+256))
#
#        # Connect neurons to input neurons on FPGA with one to one connections
#        cc.connect(pre, post, syn_type=cc.SynType.FAST_EXC, 
#                   syn_weight=1, 
#                   connection_type='virtual')
#        
#        # Load biases
#        #TODO: Replace this with functions from calibrator
#        for target_core in range(16):
#            cc.CtxDynapse.dynapse.set_tau_2(target_core//4,0) # silence neuron 0
#            cc.groups[target_core].set_bias("IF_DC_P", 0, 0)  
#            cc.groups[target_core].set_bias("IF_AHTAU_N", 255, 7)
#            cc.groups[target_core].set_bias("IF_AHTHR_N", 80, 3)
#            cc.groups[target_core].set_bias("IF_AHW_P", 0, 0)
#            cc.groups[target_core].set_bias("IF_BUF_P", 80, 4)
#            cc.groups[target_core].set_bias("IF_CASC_N", 0, 0)
#            cc.groups[target_core].set_bias("IF_DC_P", 0, 0)
#            cc.groups[target_core].set_bias("IF_NMDA_N", 0, 0)
#            cc.groups[target_core].set_bias("IF_RFR_N", 140, 3)
#            cc.groups[target_core].set_bias("IF_TAU1_N", 95, 5)
#            cc.groups[target_core].set_bias("IF_TAU2_N", 35, 7)
#            cc.groups[target_core].set_bias("IF_THR_N", 30, 2)
#            cc.groups[target_core].set_bias("NPDPIE_TAU_F_P", 20, 2)
#            cc.groups[target_core].set_bias("NPDPIE_TAU_F_P", 20, 2)
#            cc.groups[target_core].set_bias("NPDPIE_TAU_S_P", 20, 2)
#            cc.groups[target_core].set_bias("NPDPIE_THR_F_P", 115, 2)
#            cc.groups[target_core].set_bias("NPDPIE_THR_S_P", 115, 2)
#            cc.groups[target_core].set_bias("NPDPII_TAU_F_P", 20, 2)
#            cc.groups[target_core].set_bias("NPDPII_TAU_S_P", 20, 2)
#            cc.groups[target_core].set_bias("NPDPII_THR_F_P", 115, 2)
#            cc.groups[target_core].set_bias("NPDPII_THR_S_P", 115, 2)
#            cc.groups[target_core].set_bias("PS_WEIGHT_EXC_F_N", 255, 7)
#            cc.groups[target_core].set_bias("PS_WEIGHT_EXC_S_N", 0, 0)
#            cc.groups[target_core].set_bias("PS_WEIGHT_INH_F_N", 0, 0)
#            cc.groups[target_core].set_bias("PS_WEIGHT_INH_S_N", 0, 0)
#            cc.groups[target_core].set_bias("PULSE_PWLK_P", 86, 2)
#            cc.groups[target_core].set_bias("R2R_P", 85, 3)
# 
#        # =====================================================================
#        # Stimulate core 1 with 10 neurons from FPGA with average Poisson 
#        # firing rate of 50 Hz. Stimulate for 4 sec
#        n_input_neurons = 10
#        poisson_rates_hz = [50]*n_input_neurons
#        neuron_ids = pre[0:n_input_neurons]
#        target_chip = 0 # neurons post are in chip 0
#        
#        cc.fpga.set_poissGen(poisson_rates_hz, neuron_ids, target_chip)
#
#        print(self.__class__.__name__ + ' : Check spikes in core 1')        
#        cc.fpga.poissGen.start()
#        time.sleep(4)
#        cc.fpga.poissGen.stop()
#        # =====================================================================
        
if __name__ == '__main__':
    os.chdir('./cortexcontrol/')
    os.system('./cortexcontrol&')
    os.chdir('..')
    print('Start rpyc server by running in the console:')
    print('>>> import run_rpyc')
    print('Then press key to start the unittest')
    _ = input('>>> ')      
    unittest.main()