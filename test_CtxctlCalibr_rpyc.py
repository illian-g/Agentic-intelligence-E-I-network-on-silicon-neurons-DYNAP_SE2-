#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Nov 17 12:07:43 2019

Example for class CtxctlFPGA (backend: rpyc).
Check the expected stimulus with the oscilloscope.

Run from the cortexcontrol parent folder.

@author: nrisi
"""

import unittest
from ctxctl_contrib.CtxctlController import CtxctlController
import numpy as np
import matplotlib.pyplot as plt
import os

SHOW_PLOTS_IN_TESTS = True

class TestCtxctlCalbr(unittest.TestCase):
    
    def test___init__(self):
        print(self.__class__.__name__ + ' : __init__')
        print(self.__class__.__name__ + ' : Testing backend: rpyc')
    
    def test_ffcurve(self):
        print(self.__class__.__name__ + ' : test__ffcurve')
        
        cc = CtxctlController(backend='rpyc', 
                              path_bias='./relationalnet_onchip/biases/',
                              path_rec='./relationalnet_onchip/rec/')
        # Load biases:
        cc.calibrator.load_biases('20191105_170010_DYNAPseBiases.py')

        # Connect neurons to input neurons on FPGA with one to one connections        
        nrn_id_fpga = np.arange(1,256) 
        pre = list(nrn_id_fpga)
        post = list(nrn_id_fpga)
        min_freq = 20
        max_freq = 500
        list_input_frequencies = list(np.linspace(min_freq, max_freq, len(pre)))
        
        # Connect neurons
        cc.connect(pre, 
                   post, 
                   syn_type=cc.SynType.FAST_EXC, 
                   syn_weight=1, 
                   connection_type='virtual')        
        
        # Run ff curve:
        cc.calibrator.ff_curve(pre, 
                              post, 
                              list_input_frequencies)
        
        if SHOW_PLOTS_IN_TESTS:
            array_rates = np.loadtxt(cc.path_rec+str(cc.calibrator.creation_time) + '_ffcurve_.txt')
            plt.figure()
            plt.plot(list_input_frequencies, array_rates, '*')
            plt.xlabel('Input frequency [Hz]')
            plt.ylabel('Output frequency [Hz]')
            plt.title('f-f curve')
            
if __name__ == '__main__':
    os.chdir('./cortexcontrol/')
    os.system('./cortexcontrol&')
    os.chdir('..')
    print('Start rpyc server by running in the console:')
    print('>>> import run_rpyc')
    print('Then press key to start the unittest')
    _ = input('>>> ')      
    unittest.main()