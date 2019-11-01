#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Dec 16 19:32:07 2018

@author: dzenn
"""

# - Import and start RPyC service

print('Starting')

import rpyc.utils.classic
c = rpyc.utils.classic.SlaveService()
from rpyc.utils.server import OneShotServer
t = OneShotServer(c, port=1300)

print('Created RPyC service')
t.start()