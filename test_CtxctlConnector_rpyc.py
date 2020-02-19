#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Nov  3 12:41:13 2019

Unittest for class CtxctlController (backend: rpyc).

Run from the cortexcontrol parent folder.

@author: nrisi
"""

import unittest
from ctxctl_contrib.CtxctlController import CtxctlController
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import seaborn as sns
import os

SHOW_PLOTS_IN_TESTS = True

class TestCtxctlConnector(unittest.TestCase):
    
    def test___init__(self):
        print(self.__class__.__name__ + ' : __init__')
        print(self.__class__.__name__ + ' : Testing backend: rpyc')
    
    def test_connect(self):
        """ Test class function self.connect.
        Connect two cores and check created connections
        """
        print(self.__class__.__name__ + ' : test_connect')
        cc = CtxctlController(backend='rpyc')
        pre = list(range(1,256))
        post = list(range(257, 512))

        # *********************************************************************     
        cc.connector.connect(pre, post, syn_type=cc.SynType.FAST_EXC, 
                       syn_weight=1, 
                       connection_type='onchip')
        # *********************************************************************
        
        # Check that neuron pre ids are in stored in cams of neuron post
        cams_id = cc.connector.get_cams(post[0])
        self.assertIn(pre[0],cams_id)

        # Check attribute receiving connection from:
        self.assertIn(cc.neurons[pre[0]], 
                      cc.connector.CtxConnector.receiving_connections_from[cc.neurons[post[0]]])

        if SHOW_PLOTS_IN_TESTS:
            # Set binary colormap:
            sns.set()
            colors = ((0.0, 0.0, 0.0), (1, 1.0, 1.0))
            cmap = LinearSegmentedColormap.from_list('Custom', colors, len(colors))
            weight_matrix = cc.connector.get_connectivity_matrix()
            _ = plt.figure()
            ax = sns.heatmap(weight_matrix, cmap=cmap)
            colorbar = ax.collections[0].colorbar
            colorbar.set_ticks([0.25,0.75])
            colorbar.set_ticklabels(['0', '1'])
            plt.title('pre-post CAMs')
            plt.xlabel('post')
            plt.ylabel('pre')
            plt.axis('equal')            
        
    def test_remove_connection(self):              
        """ Test class funciton self.remove_connection()
        """
        print(self.__class__.__name__ + ' : test_remove_connection')
        cc = CtxctlController(backend='rpyc')
        pre = list(range(1025, 1025+256))
        post = list(range(1025+256, 1025+512))

        # Make sure that all previous connections have been removed correctly
        cams_id = cc.connector.get_cams(post[0])
        self.assertNotIn(pre[0],cams_id)
                
        # Create connections
        cc.connector.connect(pre, post, syn_type=cc.SynType.FAST_EXC, 
                          syn_weight=1, 
                          connection_type='onchip')

        # Tested function: Remove all connections        
        # *********************************************************************
        cc.connector.remove_connection(pre, post)
        # *********************************************************************
        
        # Cehck that neuron pre is no longer listed in neuron post cams
        cams_id = cc.connector.get_cams(post[0])
        self.assertNotIn(pre[0],cams_id)
        
    def test_clash_checker(self):
        '''
        Test clash_checker.
        '''
        print(self.__class__.__name__ + ' : test_clash_checker')
        cc = CtxctlController(backend='rpyc')

        pre= [2, 1026]
        post= [2000, 2000]
        cc.connector.connect(pre,
                       post,
                       syn_type=cc.SynType.FAST_EXC,
                       syn_weight=1,
                       connection_type='onchip')

        c = cc.connector.clash_checker([2000])
        self.assertEqual(c,True)
        cc.connector.remove_connection(pre, post)


        pre= [1]
        post= [1025]
        cc.connector.connect(pre,
                   post,
                   syn_type=cc.SynType.FAST_EXC,
                   syn_weight=1,
                   connection_type='onchip')

        c = cc.connector.clash_checker([1025])
        self.assertEqual(c,True)
        cc.connector.remove_connection(pre, post)


        pre= [10]
        post= [1022]
        cc.connector.connect(pre,
                   post,
                   syn_type=cc.SynType.FAST_EXC,
                   syn_weight=1,
                   connection_type='onchip')

        c = cc.connector.clash_checker([1022])
        self.assertEqual(c,False)
        cc.connector.remove_connection(pre, post)
        
if __name__ == '__main__':
    os.chdir('./cortexcontrol/')
    os.system('./cortexcontrol&')
    os.chdir('..')
    print('Start rpyc server by running in the console:')
    print('>>> import run_rpyc')
    print('Then press key to start the unittest')
    _ = input('>>> ')      
    unittest.main()
