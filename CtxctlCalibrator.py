#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Nov 17 10:30:43 2019

@author: nrisi
"""
from ctxctl_contrib.constants import NUM_NEURONS_PER_CORE, NUM_NEURONS_PER_CHIP
from datetime import datetime
import numpy as np
import time

class CtxctlCalib(object):
    
    def __init__(self, CtxDynapse, 
                 PyCtxUtils, 
                 SpikeGen,
                 rpyc_connection=None, 
                 path_rec=None,
                 path_bias=None, 
                 path_fig = None,
                 path_calib=None,
                 save_rec=True, 
                 verbose=False):
        """
        Args:
            CtxDynapse 
            bias_path  (str): path to bias file
        """
        self.name = self.__class__.__name__+' : '
        if verbose:
            print(self.__class__.__name__+' : __init__()')
        self.CtxDynapse       = CtxDynapse
        self.PyCtxUtils       = PyCtxUtils
        self.SpikeGen         = SpikeGen
        self.rpyc_connection  = rpyc_connection
        self.save_rec = save_rec     
        
        if path_bias:
            self.set_path_bias(path_bias)
        
        if path_rec:
            self.set_path_rec(path_rec)
	       
        if path_calib:		        
            self.set_path_calib(path_calib)            
        
        if path_fig:
            self.set_path_fig(path_fig)
            
        self.model      = self.CtxDynapse.model
        self.groups     = self.model.get_bias_groups()
        self.creation_time = datetime.now().strftime('%Y%m%d_%H%M%S')

        if self.rpyc_connection:		
            import matplotlib as mpl		
            self.plot = True		
            mpl.rc('text', usetex = True)		
            mpl.rcParams['text.latex.preamble'] = [r'\usepackage{amsmath}']		
            mpl.rc('font', family = 'serif')		
            mpl.rc('font', size=30)		
    
    def set_path_fig(self, path_fig):
        """ Set fig path
        """ 
        self.path_fig = path_fig
    
    def get_hot_nrn_ids(self, core_id):
        """ Get 'hot' neuron ids in core_id.
        Args:
            core_id (int): core id, from 0 to 15
        Return:
            hot_nrn_ids (list, int): list of neuron ids firing
            
        Use this function to find unexpectdly firing neurons with the
        currently set biases.
        See method 'silence_neurons' to silence them.
        """
        buf_evt_filter = self.CtxDynapse.BufferedEventFilter(self.CtxDynapse.model, 
                                                             np.arange(NUM_NEURONS_PER_CORE)+\
                                                             NUM_NEURONS_PER_CORE*core_id)
        evts = buf_evt_filter.get_events()
        time.sleep(5)
        evts = buf_evt_filter.get_events()
        buf_evt_filter.clear()
    
        hot_nrn_ids = []
        for evt in evts:
            global_nrn_id = evt.neuron.get_neuron_id() +\
                            NUM_NEURONS_PER_CORE*evt.neuron.get_core_id() +\
                            NUM_NEURONS_PER_CHIP*evt.neuron.get_chip_id()
            hot_nrn_ids.append(global_nrn_id)
        hot_nrn_ids = np.unique(hot_nrn_ids)
        
        return hot_nrn_ids
            
    def silence_nrn_ids(self, nrn_ids):
        """ Silence neuron ids in list by setting them to tau2 and increasing
        tau2. 
        Args: 
            list_nrn_ids (numpy array) : list of neuron ids to be silenced.
        """
        for nrn_id in nrn_ids:
            self.CtxDynapse.dynapse.set_tau_2(nrn_id//NUM_NEURONS_PER_CHIP,
                                              nrn_id%NUM_NEURONS_PER_CHIP)
            self.groups[nrn_id//NUM_NEURONS_PER_CORE].set_bias("IF_TAU2_N", 50, 7)
            
    def set_path_calib(self, path_calib):		
        """ Set calibration path
        """
        self.path_calib = path_calib		
        
    def set_path_bias(self, path_bias):
        """ Set bias path
        """
        self.path_bias = path_bias

    def set_path_rec(self, path_rec):
        """ Set bias path
        """
        self.path_rec = path_rec
        
    def save_biases(self, log_file=None):
        """ Save biases to file.
        Args:
            log_file (file id): write comment to log file.
        """
        filename = self.path_bias + datetime.now().strftime('%Y%m%d_%H%M%S') + '_DYNAPseBiases.py'
        self.PyCtxUtils.save_biases('../'+filename)
        print(self.name+'Biases saved to ' + filename)
        
        if log_file:
            try:
                timestr = time.strftime("%Y%m%d-%H%M%S")
                # Write message to log file:
                log = input('Enter comment: >>')
                log_file.write(timestr + ': save_biases \n')
                log_file.write('Log: '+ log + '\n')
                log_file.close()
            except:
                print('Log file not opened')
            
    def load_biases(self, filename):
        """ Load bias file.
        """
        if self.rpyc_connection:
            self.rpyc_connection.namespace['filename'] = '../'+self.path_bias+filename
            self.rpyc_connection.execute("exec(open(filename).read())")            
        else:
            filename = '../'+self.path_bias+filename
            exec(open(filename).read())            
        print(self.name+'Biases loaded form ' + filename)
    
    def ff_curve(self, input_nrn_ids_onfpga, list_nrn_ids_onchip, list_input_frequencies, plot_title=''):
        """ Measure ff curve in a range of neurons
        input_nrn_ids_onfpga     (list): list of neuron ids on fpga 
        list_nrn_ids_onchip      (list): list of neuron ids to be monitored
        list_input_frequencies   (list): list input frequencies [Hz]
        """

        # Note: need to connect input neurons on fpga to target neurons first
        self.matrix_firing_rates_per_nrn_id = np.zeros((len(list_nrn_ids_onchip)))
        if self.save_rec:
            filename = self.path_rec+self.creation_time+'_ffcurve_'+plot_title+'.txt'
        
        assert len(np.unique(np.array(list_nrn_ids_onchip)//1024))==1, 'Target neurons should be on the same chip'
        target_chip = list_nrn_ids_onchip[0]//1024
        # Init buffer event filter with neuron to be monitored
        buffer_event_filter = self.CtxDynapse.BufferedEventFilter(self.model, 
                                                                  list_nrn_ids_onchip)
        # Set input frequency
        self.SpikeGen.set_poissGen(list_input_frequencies, 
                                   input_nrn_ids_onfpga, 
                                   target_chip)
        
        _ = buffer_event_filter.get_events()        
        self.SpikeGen.poissGen.start()
        time.sleep(1)
        self.SpikeGen.poissGen.stop()
        rec_events = buffer_event_filter.get_events()
        # Sort recorded events by neuron id
        for evt in rec_events:
            pre_id = evt.neuron.get_neuron_id() + 256*evt.neuron.get_core_id() + 1024*evt.neuron.get_chip_id()
            self.matrix_firing_rates_per_nrn_id[list_nrn_ids_onchip.index(pre_id)] += 1
        
        if self.save_rec:
            for id_, nrn_id in enumerate(list_nrn_ids_onchip):
                f = open(filename, 'a')
                f.write(str(self.matrix_firing_rates_per_nrn_id[id_])+'\n')
                f.close()
                
    def ff_curve_vs_bias(self, list_input_frequencies,
                                     list_nrn_ids_fpga,
                                     list_nrn_ids_chip,
                                     list_bias_values, 
                                     name_bias_to_sweep='PS_WEIGHT_EXC_F_N',
                                     target_core=0,
                                     max_freq_for_fitting=100,
                                     linear_fit=True,
                                     save_data=True,
                                     verbose=True):
        
        print(self.name+'Select max frequency for linear fitting of ff curve')
        bias_weight_lookup = {}
        if max_freq_for_fitting:
            list_indices_used_for_fitting = np.where(np.array(list_input_frequencies)<max_freq_for_fitting)[0]
        start = time.time()
        if self.plot:
            import matplotlib.pyplot as plt
            fig = plt.figure()
            ax = fig.add_subplot(121)
            NUM_COLORS = len(list_bias_values)
            cm = plt.get_cmap('gist_rainbow')
        for i, linear_bias in enumerate(list_bias_values):    
            # Set bias value:
            self.groups[target_core].set_linear_bias(name_bias_to_sweep, linear_bias)
            print(self.name+'Bias value ' + str(linear_bias))
            plot_title = name_bias_to_sweep+'_'+str(linear_bias)
            self.ff_curve(list_nrn_ids_fpga, 
                          list_nrn_ids_chip, 
                          list_input_frequencies,
                          plot_title=plot_title)
            
            # Matrix rates:
            array_rates = np.loadtxt(self.path_rec+str(self.creation_time) + \
                                     '_ffcurve_'+ plot_title +'.txt')
            if self.plot:
                lines = ax.plot(list_input_frequencies, array_rates, '*')
                lines[0].set_color(cm(i//3*3.0/NUM_COLORS))
                plt.xlabel('Input frequency [Hz]')
                plt.ylabel('Output frequency [Hz]')
                plt.title('f-f curve')     

            # Linear fitting of linear region of ff curves:                
            if max_freq_for_fitting:
                x = np.array(list_input_frequencies)[list_indices_used_for_fitting]
                y = array_rates[list_indices_used_for_fitting]
                coeff = np.polyfit(x, y, 1)
                bias_weight_lookup[linear_bias] = coeff
                p = np.poly1d(coeff)
                if self.plot:
                    lines = ax.plot(x, p(x), '--', linewidth=2.0)    
                    lines[0].set_color(cm(i//3*3.0/NUM_COLORS)) 
                    
        end = time.time()
        time_to_run = end-start
        if verbose:
            print(self.name+'Time to run: '+str(time_to_run))
                
        if max_freq_for_fitting:
            # Save coefficients of linear fitting to file: =========================
            filename = self.path_calib + str(self.creation_time) + '_'+\
                        name_bias_to_sweep +'_biases_slopes'
            bias_value = [ key for key in bias_weight_lookup.keys()]
            slope   = [ bias_weight_lookup[key][0] for key in bias_weight_lookup.keys() ]
            offset  = [ bias_weight_lookup[key][1] for key in bias_weight_lookup.keys() ]
            lookup_bias2weights = np.vstack((bias_value, slope, offset))
            np.save(filename, lookup_bias2weights)        
                    
            # Plinomial fitting of the bias vs weight curve: =======================
            coeff, residuals, rank, singular_values, rcond = np.polyfit(list_bias_values, 
                                                                        slope, 
                                                                        deg=2, 
                                                                        full=True)
            p = np.poly1d(coeff) 
            if verbose:
                print(self.name+'Mapping bias to weight ')
                print(self.name+'coeff : ', coeff)
                print(self.name+'residuals : ', residuals)               
            if self.plot:
                ax = fig.add_subplot(122)
                for i, linear_bias in enumerate(list_bias_values):    
                    lines = ax.plot(list_bias_values[i], slope[i], '*')
                    lines[0].set_color(cm(i//3*3.0/NUM_COLORS))
                # Plot fitted cirve:
                plt.plot(list_bias_values, p(list_bias_values), 'k-')
                plt.xlabel('Linear bias value')
                plt.ylabel('Slope ff curve')
                fig.set_size_inches(20,20)     
                figure_name = self.path_fig + str(self.creation_time) + 'ff_curve_'+name_bias_to_sweep
                fig.savefig(figure_name+'.pdf', format='pdf') 
                fig.savefig(figure_name+'.svg', format='svg') 
                fig.savefig(figure_name+'.eps', format='eps', dpi=1000)            
    
                
            # Polinomial fitting of the inverse curve: weight to bias curve
            coeff, residuals, rank, singular_values, rcond = np.polyfit(slope, 
                                                                        list_bias_values, 
                                                                        deg=5, 
                                                                        full=True)
            p = np.poly1d(coeff) 
            filename = self.path_calib + str(self.creation_time) + '_'+\
                        name_bias_to_sweep +'_polyfit_weight2bias'
            np.save(filename, coeff)               
            if verbose:
                print(self.name+'Mapping weight to bias ')
                print(self.name+'coeff : ', coeff)
                print(self.name+'residuals : ', residuals)     
            if self.plot:        
                fig = plt.figure()
                ax = fig.add_subplot(111)
                for i, linear_bias in enumerate(list_bias_values):    
                    lines = ax.plot(slope[i], list_bias_values[i], '*')
                    lines[0].set_color(cm(i//3*3.0/NUM_COLORS))        
                # Plot fitted curve:
                plt.plot(slope, p(slope), 'k-')
                plt.xlabel('Slope ff curve')
                plt.ylabel('Linear bias value')
                fig.set_size_inches(13,13)     
                figure_name = self.path_fig + str(self.creation_time) + 'slope_vs_'+name_bias_to_sweep
                fig.savefig(figure_name+'.pdf', format='pdf') 
                fig.savefig(figure_name+'.svg', format='svg') 
                fig.savefig(figure_name+'.eps', format='eps', dpi=1000)     
            
    def set_core_frequency(self, 
                           target_core, 
                           target_frequency, 
                           start_bias_value=5000,
                           toll_delta=10):
        """ Set core firing frequency by increasing/decreasing DC bias
        This will bring the selected core to a mean firing frequency of
        target_frequency +- toll_delta
        Args:
            target_core        (int): core id 
            target_frequency (float): target frequency
            toll_delta       (float): tollerated delta frequency
        """
        name_bias_to_sweep = 'IF_DC_P'
        list_nrn_ids = list(np.arange(target_core*256, (target_core+1)*256))
        buffer_event_filter = self.CtxDynapse.BufferedEventFilter(self.model, 
                                                                  list_nrn_ids) 
        core_rate = self.get_rates(list_nrn_ids, buffer_event_filter)
        delta_rate = target_frequency-core_rate
        
        # Set starting point
        old_bias_value = int(self.groups[target_core].get_linear_bias(name_bias_to_sweep))               
        if old_bias_value < start_bias_value:
            self.groups[target_core].set_linear_bias(name_bias_to_sweep, start_bias_value)
            
        # Update DC current until the desired frequency is reached
        while ( np.abs(delta_rate) > toll_delta ):
                        
            old_bias_value = int(self.groups[target_core].get_linear_bias(name_bias_to_sweep))   
            
            # Compute gain: if overshoot the gain is negative and the bias decreases
            gain = 1 - core_rate/(target_frequency+toll_delta)
            
            # Set new DC current:
            new_bias_value = old_bias_value*(1+gain)
            self.groups[target_core].set_linear_bias(name_bias_to_sweep, new_bias_value)
            
            # Update rate:
            core_rate = self.get_rates(list_nrn_ids, buffer_event_filter)
            delta_rate = target_frequency-core_rate   
            print(self.name+'Core rate: '+str(core_rate))
            
        print(self.name+'Converged freqeuncy!')
    
    def get_rates(self, list_nrn_ids, buffer_event_filter=None, delta_t=1):
        """ Get rates of specified neuron ids.
        Args:
            list_nrn_ids (list): neuron id to monitor
            buffer_event_filter (ctxctl BufferEventFilter)
            delta_t (float): time interval in which spikes are recorded
        """
        array_rates = np.zeros((len(list_nrn_ids)))
        if not(buffer_event_filter):
            buffer_event_filter = self.CtxDynapse.BufferedEventFilter(self.model, 
                                                                      list_nrn_ids) 
        _ = buffer_event_filter.get_events()
        time.sleep(1)
        rec_events = buffer_event_filter.get_events()
        for evt in rec_events:
            pre_id = evt.neuron.get_neuron_id() + 256*evt.neuron.get_core_id() + 1024*evt.neuron.get_chip_id()
            array_rates[list_nrn_ids.index(pre_id)] += 1
        
        return np.mean(array_rates/delta_t)
    
    def reset_dc(self, target_core):
        """ Set DC current in target core to zero.
        """
        self.groups[target_core].set_linear_bias('IF_DC_P', 0)
        
    #TODO:
    def test_routing(self):
        """ Checks which directions of connections are allowed on the dynapse 
        board.
        """
        pass