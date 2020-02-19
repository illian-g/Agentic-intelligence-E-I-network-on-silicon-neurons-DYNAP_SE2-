#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov  7 14:42:48 2019

Unittest for class CtxctlController (backend: ctxctl).

To run the test open ctxctl gui. 
And exectute:
    >>> import os
    >>> os.chdir('..')
    >>> import ctxctl_contrib.test_CtxctlConnector_ctxctl as tc
    >>> os.chdir('./cortexcontrol')
    >>> test = tc.TestCtxctlConnector()
    
@author: nrisi
"""

import time
from ctxctl_contrib.CtxctlController import CtxctlController

class TestCtxctlConnector(object):
    
    def __init__(self):
        print(self.__class__.__name__ + ' : __init__')
        print(self.__class__.__name__ + ' : Testing backend: ctxctl')
        start = time.time()            
        
        # Test to run:
        self.test_connect()
        self.test_remove_connection()
        self.test_clash_checker()
        
        end = time.time()    
        print('Ran 3 tests in {} s'.format(end-start))
        print('OK')        
        
    def test_connect(self):
        """ Test class function self.connect.
        Connect two cores and check created connections
        """
        print(self.__class__.__name__ + ' : test_connect')
        cc = CtxctlController(backend='ctxctl')
        pre = list(range(1,256))
        post = list(range(257, 512))
        
        # Tested function: Create connections
        # *********************************************************************        
        cc.connector.connect(pre, post, syn_type=cc.SynType.FAST_EXC, 
                             syn_weight=1, 
                             connection_type='onchip')
        # *********************************************************************
        
        # Check that neuron pre ids are in stored in cams of neuron post
        cams_id = cc.connector.get_cams(post[0])
        assert(pre[0] in cams_id), 'Neuron pre not listed in CAMs'

        # Check attribute receiving connection from:
        assert(cc.neurons[pre[0]] in 
               cc.connector.CtxConnector.receiving_connections_from[cc.neurons[post[0]]]), \
               'Neuron pre not listed in dictionary of connections'
        print(self.__class__.__name__ + ' : OK!')

    def test_remove_connection(self):              
        """ Test class funciton self.remove_connection()
        """
        print(self.__class__.__name__ + ' : test_remove_connection')
        cc = CtxctlController(backend='ctxctl')
        pre = list(range(1025, 1025+256))
        post = list(range(1025+256, 1025+512))

        # Make sure that all previous connections have been removed correctly
        cams_id = cc.connector.get_cams(post[0])
        assert(not(pre[0] in cams_id)), 'Neuron pre already stored in cams'
                
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
        assert(not(pre[0] in cams_id)), 'Neuron pre not removed from cams'
        print(self.__class__.__name__ + ' : OK!')        
        
    def test_clash_checker(self):
        '''
        Test clash_checker.
        '''
        print(self.__class__.__name__ + ' : test_clash_checker')
        cc = CtxctlController(backend='ctxctl')

        pre= [2, 1026]
        post= [2000, 2000]
        cc.connector.connect(pre,
                       post,
                       syn_type=cc.SynType.FAST_EXC,
                       syn_weight=1,
                       connection_type='onchip')

        c = cc.connector.clash_checker([2000])
        assert(c==True)
        cc.connector.remove_connection(pre, post)


        pre= [1]
        post= [1025]
        cc.connector.connect(pre,
                   post,
                   syn_type=cc.SynType.FAST_EXC,
                   syn_weight=1,
                   connection_type='onchip')

        c = cc.connector.clash_checker([1025])
        assert(c==True)
        cc.connector.remove_connection(pre, post)


        pre= [10]
        post= [1022]
        cc.connector.connect(pre,
                   post,
                   syn_type=cc.SynType.FAST_EXC,
                   syn_weight=1,
                   connection_type='onchip')

        c = cc.connector.clash_checker([1022])
        assert(c==False)
        cc.connector.remove_connection(pre, post)
        print(self.__class__.__name__ + ' : OK!')        