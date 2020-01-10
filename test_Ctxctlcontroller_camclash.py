#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan  8 10:51:49 2020

@author: matteo

open cortexcontrol, run:

import run_rpyc
"""

import os
import unittest
import numpy as np
from ctxctl_contrib.CtxctlController import CtxctlController



class TestCtxctlCamclash(unittest.TestCase):

    def test___init__(self):
        print(self.__class__.__name__ + ' : __init__')
        print(self.__class__.__name__ + ' : Testing Cam clash')

    def test_clash_checker(self):
        '''
        Test clash_checker.
        '''
        cc = CtxctlController(backend='rpyc')

        pre= [2, 1026]
        post= [2000, 2000]
        cc.connect(pre,
                   post,
                   syn_type=cc.SynType.FAST_EXC,
                   syn_weight=1,
                   connection_type='onchip')

        c = cc.clash_checker([2000])
        self.assertEqual(c,True)
        cc.remove_connection(pre, post)


        pre= [1]
        post= [1025]
        cc.connect(pre,
                   post,
                   syn_type=cc.SynType.FAST_EXC,
                   syn_weight=1,
                   connection_type='onchip')

        c = cc.clash_checker([1025])
        self.assertEqual(c,True)
        cc.remove_connection(pre, post)


        pre= [10]
        post= [1022]
        cc.connect(pre,
                   post,
                   syn_type=cc.SynType.FAST_EXC,
                   syn_weight=1,
                   connection_type='onchip')

        c = cc.clash_checker([1022])
        self.assertEqual(c,False)
        cc.remove_connection(pre, post)




if __name__ == '__main__':
    os.chdir('./cortexcontrol/')
    os.system(' ./cortexcontrol&')
    os.chdir('..')
    print('Start rpyc server by running in the console:')
    print('>>> import run_rpyc')
    print('Then press key to start the unittest')
    _ = input('>>> ')
    unittest.main()
