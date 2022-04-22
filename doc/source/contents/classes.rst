Classes and methods
======================

Higher-level APIs
-------------------------

Open and close device
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The implementation of the higher-level mothods are in files NetworkGenerator.py and Dynapse1Utils.py.

.. py:method:: Dynapse1Utils.open_dynapse1(device_name, gui=True, sender_port=33336, receiver_port=33335)

    Open DYNAP-SE1 board with or without GUI.

    :param string device_name: give name to the DYNAP-SE1 board you want to open.
    :param bool gui: to open GUI or not.
    :param bool sender_port: samnaNode's sending port. Should be 33336 if gui=True, otherwise you can use a 5-digits port number.
    :param int receiver_port: samnaNode's receiving port. Should be 33335 if gui=True, otherwise you can use a 5-digits port number which is different from sender_port.

    :returns: store: samna store which contains Dynapse1Model.
        gui_process: the gui process handler, if gui=True.
    
    :rtype: samna.device_node.
        Process.

.. py:method:: Dynapse1Utils.close_dynapse1(store, device_name, gui_process='')

    Close DYNAP-SE1 board with or without GUI.

    :param samna.device_node store: the device_node you get when you :func:`open_dynapse1 <Dynapse1Utils.open_dynapse1>`.

    :param string device_name: the name you gave to the DYNAP-SE1 board when you :func:`open_dynapse1 <Dynapse1Utils.open_dynapse1>`.
    :param Process gui_process: the GUI process you created when you :func:`open_dynapse1 <Dynapse1Utils.open_dynapse1>`.

Neuron event filter
^^^^^^^^^^^^^^^^^^^^^^^

.. py:method:: Dynapse1Utils.create_neuron_select_graph(model, global_neuron_ids)

    Create a graph: source_node in model -> filter_node in graph -> sink_node to get events.
    Only filter_node is in the graph. Source and sink nodes are outside graph.
    To use the graph, first graph.start().
    To get events, sink_node.get_buf().
    If you graph.stop(), for now the graph actually won't stop, all events are still
    streamed into the buffer of sink_node. This is work in progess.
    Thus to get events for 1 second, you need to first clear the buffer of sink_node using get_buf(). i.e.,  

        sink_node.get_buf()

        sleep(1)

        events = sink_node.get_buf()

    :param Dynapse1Model model: model.
    :param list[int] global_neuron_ids: global neuron ids of selected neurons. The id should be in the range of [0, 4096).

    :returns: graph: samna graph.

        filter_node: filter_node that filters the events of selected neurons.
        
        sink_node: sink_node that receives the events from the filter_node.
    
    :rtype: samna.graph.EventFilterGraph.
        samna.graph.nodes.Dynapse1NeuronSelect_dynapse1_dynapse1_event
        BufferSinkNode_dynapse1_dynapse1_event.

NetworkGenerator
^^^^^^^^^^^^^^^^^^^^

.. py:class:: NetworkGenerator.NetworkGenerator()

    NetworkGenerator maintains a Network and a corresponding Dynapse1Configuration.

    .. py:attribute:: network

        Network that keeps the topology information.

        :type: NetworkGenerator.Network
    
    .. py:attribute:: config

        Dynapse1Configuration converted from the Network, which can be applied to the board.

        :type: samna.dynapse1.Dynapse1Configuration

    .. py:method:: add_connection(pre, post, synapse_type)

        Add a connection between the pre and post neuron with type "synapse_type" into the network.

        :param NetworkGenerator.Neuron pre: pre neuron.
        :param NetworkGenerator.Neuron post: post neuron.
        :param samna.dynapse1.Dynapse1SynType synapse_type: synapse_type.

    .. py:method:: remove_connection(pre, post, synapse_type)

        Remove a connection between the pre and post neuron with type "synapse_type" into the network.

        :param NetworkGenerator.Neuron pre: pre neuron.
        :param NetworkGenerator.Neuron post: post neuron.
        :param samna.dynapse1.Dynapse1SynType synapse_type: synapse_type.

    .. py:method:: clear_network()

        Clear all neurons and connections in the network.

    .. py:method:: print_network()

        Print the network connections. The printing format is "Post neuron (ChipId,coreId,neuronId): incoming connections [(preNeuron,synapseType), ...]".

    .. py:method:: make_dynapse1_configuration()

        Make a Dynapse1Configuration out of the current network. It will first check if the network meets the hardware specific constraints and throw error or warnings if the network is invalid.

    .. py:method:: make_dynapse1_configuration_in_chip(chip_id)

        This function should be followed by :func:`apply_configuration_by_chip() <Dynapse1Model.apply_configuration_by_chip>` which applies the new configuration only to a single chip of the DYNAP-SE1 board. 
        NOTE: be careful if you use this method because this is specifically designed for the user who only does experiments in a single chip. If you have network components in other chips, you will get an error. 

        :param int chip_id: chip_id, [0,4).

    .. py:method:: make_dynapse1_configuration_in_core(chip_id, core_id)

        This function should be followed by :func:`apply_configuration_by_core() <Dynapse1Model.apply_configuration_by_core>` which applies the new configuration only to a single chip of the DYNAP-SE1 board.
        NOTE: be careful if you use this method because this is specifically designed for the user who only does experiments in a single core. If you have network components in other core, you will get an error.  

        :param int chip_id: chip_id, [0,4).
        :param int core_id: core_id, [0,4).

.. py:class:: NetworkGenerator.Neuron(chip_id=0, core_id=0, neuron_id=0, is_spike_gen=False)

    Neuron that only keeps topology information.

    :param int chip_id: chip_id, [0,4).
    :param int core_id: core_id, [0,4).
    :param int neuron_id: neuron_id, [0,256).
    :param bool is_spike_gen: specify if this neuron is a spike generator or a real neuron.

    .. py:attribute:: chip_id
        :type: int
    .. py:attribute:: core_id
        :type: int
    .. py:attribute:: neuron_id
        :type: int
    .. py:attribute:: is_spike_gen
        :type: bool
    .. py:attribute:: incoming_connections 

        A dictionarty which stores the incoming_connections.
        key: tuple, (pre.core_id,pre.neuron_id,synapse_type).
        Corresponds to cam. Divide the connections by its cam value for cam reuse.
        value: list, [(pre.chip_id, pre.is_spike_gen), (pre.chip_id, pre.is_spike_gen),...].
        To tell if the post neurons are the same neuron. get the connection weight.

        :type: dict{tuple[int, int, samna.dynapse1.Dynapse1SynType], list[(int, bool)]}

.. py:class:: NetworkGenerator.Network()

    Network that maintains the topology information.

    .. py:attribute:: post_neuron_dict 

        A dictionary which stores all the post neurons (and their incoming connections).
        key: tuple, (post.chip_id, post.core_id).
        Divide the post neurons by its location (core) for aliasing check.
        value: list of neurons each of which has incoming connections.

        :type: dict{tuple[int, int], list[NetworkGenerator.Neuron]}


Set up FPGASpikeGen
^^^^^^^^^^^^^^^^^^^^^^^^

.. py:method:: Dynapse1Utils.set_fpga_spike_gen(fpga_spike_gen, spike_times, indices, target_chips, isi_base, repeat_mode=False)

        Author: Nicoletta Risi. Adapted by Jingyue Zhao.

        This function sets the FPGASpikeGenerator object given a list of spike times, in second, correspondent spike generator ids and the target chips, i.e. the chip destination of each input event.

        About  `isi_base`:
        Given a list of spike times (in sec) a list of isi (Inter Stimulus Interval) 
        is generated. Given a list of isi, the resulting list of isi set from the 
        FPGA will be:
        
            isi*unit_fpga
            
            with             
            unit_fpga = isi_base/90 * us    
            
        Thus, given a list of spike_times in sec:
            - first the spike times are converted in us
            - then a list of isi (in us) is generated
            - then the list of isi is divided by the unit_fpga (so that the resulting list of isi set on FPGA will have the correct unit given the input isi_base)        
        E.g.: if isi_base=900 the list of generated isi will be multiplied on FPGA by 900/90 us = 10 us

        :param Dynapse1FpgaSpikeGen fpga_spike_gen: Dynapse1FpgaSpikeGen retrieved from Dynapse1Model.
        :param list[float] spike_times: list of input spike times, in second.
        :param list[int] indices: list of FPGA spike generator ids sorted according to time of spike.
        :param list[int] target_chip: list of target chip to which each event will be sent.
        :param int isi_base: 90 or 900 (see above).
        :param bool repeat_mode: If repeat is True, the spike generator will loop from the beginning when it reaches the end of the stimulus.


Parameters related methods
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. py:method:: Dynapse1Utils.get_parameters(config, chip, core)

    Get a list of Dynapse1Parameter (25 in total) of a specific core.

    :param Dynapse1Configuration config: Dynapse1Configuration retrieved from Dynapse1Model.
    :param int chip: chip ID, [0,4).
    :param int core: core ID, [0,4).

    :returns: current parameter setup of the core.
    :rtype: list[samna.dynapse1.Dynapse1Parameter].

.. py:method:: Dynapse1Utils.save_parameters2json_file(config, filename="./dynapse_parameters.json")

    Save the parameters of 16 cores into a JSON file.

    :param Dynapse1Configuration config: Dynapse1Configuration retrieved from Dynapse1Model.
    :param string filename: the path and filename of the output paramter file.

.. py:method:: Dynapse1Utils.set_parameters_in_json_file(model, filename="./dynapse_parameters.json")

    Load the parameters in a JSON file to DYNAP-SE1 board.

    :param Dynapse1Model model: Dynapse1Model.
    :param string filename: the path and filename of the input paramter file.

.. py:method:: Dynapse1Utils.save_parameters2txt_file(config, filename="./dynapse_parameters.txt")

    Save the parameters of 16 cores into a txt file.

    :param Dynapse1Configuration config: Dynapse1Configuration retrieved from Dynapse1Model.
    :param string filename: the path and filename of the output paramter file.

.. py:method:: Dynapse1Utils.set_parameters_in_txt_file(model, filename="./dynapse_parameters.txt")

    Load the parameters in a txt file to DYNAP-SE1 board.

    :param Dynapse1Model model: Dynapse1Model.
    :param string filename: the path and filename of the input paramter file.


Get the serial number of the opened DYNAP-SE1 board
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. py:method:: Dynapse1Utils.get_serial_number(store, device_name)

    Get the serial number of the opened DYNAP-SE1 board.

    :param samna.device_node store: the device_node you get when you :func:`open_dynapse1 <Dynapse1Utils.open_dynapse1>`.

    :param string device_name: the name you gave to the DYNAP-SE1 board when you :func:`open_dynapse1 <Dynapse1Utils.open_dynapse1>`.

    :returns: serial_number, serial number of the opened board.
    :rtype: int.



Get TimestampWrapEvent
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. py:method:: Dynapse1Utils.get_time_wrap_events(model)

    DYNAP-SE1 sends out 2 types of events: spike and timeWrapEvent. timeWrapEvent occurs when the 32 bit timestamp wraps around. This happens every ~37(?) minutes. With the graph created by this method, you can monitor if any timeWrapEvent is generated effectively with the C++ backend.

    :param Dynapse1Model model: Dynapse1Model.

    :returns: graph: samna graph.

            sink_node: sink_node that receives the events from the filter_node.
    
    :rtype: samna.graph.EventFilterGraph.
        BufferSinkNode_dynapse1_dynapse1_event.
    

Other helper functions in Dynapse1Utils
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. py:method:: Dynapse1Utils.get_neuron_from_config(config, global_neuron_id)

    Get a neuron by its global_neuron_id from a configuration.

    :param Dynapse1Configuration config: Dynapse1Configuration. 
    :param int global_neuron_id: global neuron id, [0,4096).

    :returns: Dynapse1Neuron.
    :rtype: samna.dynapse1.Dynapse1Neuron().

.. py:method:: Dynapse1Utils.gen_synapse_string(synapse)

    Print a Dynapse1Synapse in the format: c<listen_core_id>n<listen_neuron_id><synapse_type>. e.g., c1n25NMDA means this synapse listens to core 1 neuron 25 with type NMDA.

    :param Dynapse1Synapse synapse: synapse. 

.. py:method:: Dynapse1Utils.print_neuron_synapses(neuron, synapse_id_list=range(MAX_NUM_CAMS))

    Print the synapses of the neuron given the synapse id list.

    :param Dynapse1Neuron neuron: neuron.
    :param list[int] synapse_id_list: synapse IDs you want to print out.

.. py:method:: Dynapse1Utils.gen_destination_string(destination)

    Print a Dynapse1Destination in the format: C<target_chip_id>c<core_mask><in_use>. e.g., C2c1True means this Dynapse1Destination has target_chip_id=2, core_mask=1 and it's occupied.

    :param Dynapse1Destination destination: destination.

.. py:method:: Dynapse1Utils.print_neuron_destinations(neuron, destination_id_list=range(4))

    Print the destinations of the neuron given the destination id list. 

    :param Dynapse1Neuron neuron: neuron.
    :param list[int] destination_id_list: destination IDs you want to print out.

.. py:method:: Dynapse1Utils.get_global_id(chip, core, neuron)

    Conveniently generate the corresponding global neuron ID given chip, core, neuron IDs.

    :param int chip: chip ID, [0,4).
    :param int core: core ID, [0,4) for physical neurons, [0,1) for spike generators on the FPGA.
    :param int neuron: neuron ID, [0,256).

    :returns: global_neuron_id.
    :rtype: int.

.. py:method:: Dynapse1Utils.get_global_id_list(tuple_list)

    Conveniently generate a list of global neuron IDs given a list of [chip, core, neuron ID] tuples.

    :param list[[int,int,int]] tuple_list: a list of global neuron IDs.

    :returns: global_neuron_ids.
    :rtype: list[int].

.. py:method:: Dynapse1Utils.print_dynapse1_spike(event)

    Print the Spike in the following format: "(timestamp, global_neuron_id),".

    :param samna.dynapse1.Spike event: spike.


Lower-level APIs
-------------------------

The lower-level APIs are implemented in C++ and bound to Python, so that you cannot find the implementation of the Python methods directly like the higher-level APIs.

Dynapse1Model
^^^^^^^^^^^^^^^^^^^^^

.. py:class:: Dynapse1Model

    You cannot create a Dynapse1Model by yourself in Python script, instead you can only get the model from the samna store because Dynapse1Model is bound to the hardware. Below are the Python methods you can call using the model you get from the store.

    .. py:method:: get_configuration()

        Get the current configuration of the DYNAP-SE1 board.

        :returns: Dynapse1Configuration: current configuration of the board.


    .. py:method:: apply_configuration(new_config)

        Apply new configuration to the DYNAP-SE1 board.

        :param Dynapse1Configuration new_config: new configuration.

    
    .. py:method:: apply_configuration_by_chip(new_config, chip_id)

        Apply new configuration only to a single chip of the DYNAP-SE1 board. NOTE: be careful if you use this method because this is specifically designed for the user who only does experiments in a single chip. If you have network components in other chips, please don NOT use this method.

        :param Dynapse1Configuration newConfig: new configuration.
        :param int chip_id: the chip you want to change, [0,4).


    .. py:method:: apply_configuration_by_core(new_config, core_id)

        Apply new configuration only to a single core of the DYNAP-SE1 board. NOTE: be careful if you use this method because this is specifically designed for the user who only does experiments in a single core. If you have network components in other cores, please don NOT use this method.

        :param Dynapse1Configuration newConfig: new configuration.

        :param int chip_id: the chip you want to change.

    
    .. py:method:: update_parameter_group(parameter_group, chip_id, core_id)

        Update the parameters of a specific core.

        :param Dynapse1ParameterGroup parameter_group: Dynapse1ParameterGroup object.

        :param int chip_id: chip_id, [0,4).
        :param int core_id: core_id, [0,4).


    .. py:method:: update_single_parameter(parameter, chip_id, core_id)

        Update a single parameter of a specific core.

        :param Dynapse1Parameter parameter: Dynapse1Parameter object.

        :param int chip_id: chip_id, [0,4).
        :param int core_id: core_id, [0,4).


    .. py:method:: get_source_node()

        Get the source node in the Dynapse1Model which sends spikes out.

        :param Dynapse1Parameter parameter: Dynapse1Parameter object.

        :param int chip_id: chip_id, [0,4).

        :returns: graph::nodes::BasicSourceNode<Dynapse1Event>: BasicSourceNode with the event type Dynapse1Event.

    
    .. py:method:: get_dynapse1_api()

        Get Dynapse1Interface which can do monitor_neuron, reset_timestamp, reset_tau_1, reset_tau_2, set_tau_2.

        :returns: Dynapse1Interface: Dynapse1Interface.


    .. py:method:: get_poisson_gen()

        Get Dynapse1PoissonGen.

        :returns: Dynapse1PoissonGen: Dynapse1PoissonGen.


    .. py:method:: get_fpga_spike_gen()

        Get Dynapse1FpgaSpikeGen.

        :returns: Dynapse1FpgaSpikeGen: Dynapse1FpgaSpikeGen.


Dynapse1Interface
^^^^^^^^^^^^^^^^^^^^^^^^

.. py:class:: Dynapse1Interface

    You cannot create a Dynapse1Interface by yourself in Python script, instead you can only get the API from a Dynapse1Model in the store.

    
    .. py:method:: monitor_neuron(chip_id, neuron_id)

        Select the neuron you want to monitor using oscilloscope. You can only monitor one neuron per core.

        :param int chip_id: chip_id, [0,4).
        :param int neuron_id: neuron id in the chip, [0,1023).


    .. py:method:: reset_timestamp()

        Reset the time counter on the FPGA. Called automatically in the init of Dynapse1Model every time you open the board.


    .. py:method:: reset_tau_1(chip_id, core_id)

        Switch a specific core to use tau1.

        :param int chip_id: chip_id, [0,4).
        :param int core_id: core_id, [0,4).

    
    .. py:method:: reset_tau_2(chip_id, core_id)

        Switch a specific core to use tau2.

        :param int chip_id: chip_id, [0,4).
        :param int core_id: core_id, [0,4).


    .. py:method:: set_tau_2(chip_id, neuron_id)

        Switch a specific neuron to use tau2.

        :param int chip_id: chip_id, [0,4).
        :param int neuron_id: neuron id in the chip, [0,1023).


Dynapse1PoissonGen
^^^^^^^^^^^^^^^^^^^^^^^^
.. py:class:: Dynapse1PoissonGen

    You cannot create a Dynapse1PoissonGen by yourself in Python script, instead you can only get the Dynapse1PoissonGen from a Dynapse1Model in the store.
    
    .. py:method:: set_chip_id(chip_id)

        Set the target chip where the stimulated neurons are located.
        
        :param int chip_id: chip_id.


    .. py:method:: write_poisson_rate_hz(neuron_id, rate_hz)

        Set the firing rate of a specific Poisson generator.

        :param int neuron_id: neuron_id, [0,1023).
        :param float rate_hz: rate_hz.


    .. py:method:: write_poisson_rates_hz(rates)

        Set the firing rates of 1024 Poisson generators.

        :param list[float] rates: rate list.


    .. py:method:: get_poisson_rate_hz(neuron_id)

        Get the firing rate of a specific Poisson generator.

        :param int neuron_id

        :returns: rates: rate of a specific Poisson generator.
        :rtype: float.

    .. py:method:: get_poisson_rates_hz()

        Get the firing rates of 1024 Poisson generators.

        :returns: rates: rate of a specific Poisson generator.
        :rtype: list[float].

    .. py:method:: start()

        Start the Poisson generator(s). If it's already on, will do nothing.

    .. py:method:: stop()

        Stop the Poisson generator(s). If it's already off, will do nothing.

    .. py:method:: is_running()

        Check if the Poisson generator(s) are on.

        :returns: run_status: if the Dynapse1PoissonGen is on.
        :rtype: bool.


    .. py:method:: get_module_type()

        WRONG for now. Do NOT call it.. Need to bind FpgaModuleType to Python...

        :returns: FpgaModuleType: FpgaModuleType.


Dynapse1FpgaSpikeGen
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. py:class:: Dynapse1FpgaSpikeGen

    You cannot create a Dynapse1FpgaSpikeGen by yourself in Python script, instead you can only get the Dynapse1FpgaSpikeGen from a Dynapse1Model in the store.

    .. py:method:: preload_stimulus(events)

        :param list[samna.dynapse1.FpgaSpikeEvent] events: FpgaSpikeEvents to be loaded.

    .. py:method:: start()

        Start the FPGA spike generator(s). If it's already on, will do nothing.

    .. py:method:: stop()

        stop the FPGA spike generator(s). If it's already off, will do nothing.

    .. py:method:: is_running()

        Check if the FPGA spike generator(s) are on.

        :returns: run_status: if the Dynapse1PoissonGen is on.
        :rtype: bool.

    .. py:method:: set_repeat_mode(repeat)

        If repeat is true, the pre loaded stimulus will be played repeatedly.

        :param bool repeat: repeat.
    
    .. py:method:: get_repeat_mode()

        Check if the repeat mode is on or not.

        :returns: repeat.
        :rtype: bool.
    
    .. py:method:: set_isi(isi)

        Set inter-spike interval.
        
        :param int isi: isi.

    .. py:method:: get_isi(isi)

        Get inter-spike interval.

        :returns: isi.
        :rtype: int.

    .. py:method:: set_isi_multiplier(multiplier)

        :param int multiplier: isi base.

    .. py:method:: get_isi_multiplier()

        :returns: isi_multiplier.
        :rtype: int.

    .. py:method:: set_base_addr(base_addr)

        :param int base_addr: base_addr.

    .. py:method:: get_base_addr()

        :returns: base_addr.
        :rtype: int.
    
    .. py:method:: set_stim_count(stim_count)

        :param int stim_count: stim_count.
    
    .. py:method:: get_stim_count()
    
        :returns: stim_count.
        :rtype: int.

    .. py:method:: set_variable_isi_mode(enabled)

        :param bool enabled: enabled.

    .. py:method:: get_module_type()

        WRONG for now. Do NOT call it.. Need to bind FpgaModuleType to Python...

        :returns: FpgaModuleType: FpgaModuleType.

FpgaSpikeEvent
^^^^^^^^^^^^^^^^
.. py:class:: samna.dynapse1.FpgaSpikeEvent(core_mask, neuron_id, target_chip, isi)

    :param int core_mask: 4-bits binary core mask specifying the target cores. e.g. 15 (i.e. 1111) means to target all 4 cores off the target chip.
    :param int neuron_id: target neuron id.
    :param int target_chip: target chip.
    :param int isi: isi.

    .. py:attribute:: core_mask
    .. py:attribute:: neuron_id
    .. py:attribute:: target_chip
    .. py:attribute:: isi

Spike
^^^^^^^^^^^^^^^^
.. py:class:: samna.dynapse1.Spike(chip_id, core_id, neuron_id, timestamp)

    :param int chip_id: chip_id, [0,4).
    :param int core_id: core_id, [0,4).
    :param int neuron_id: neuron_id, [0,256).
    :param int timestamp: timestamp, in microsecond, 1e-6 second.

    .. py:attribute:: chip_id
    .. py:attribute:: core_id
    .. py:attribute:: neuron_id
    .. py:attribute:: timestamp

TimestampWrapEvent
^^^^^^^^^^^^^^^^^^^^^^^^^^
.. py:class:: samna.dynapse1.TimestampWrapEvent(timestamp)

    :param int timestamp: timestamp.

    .. py:attribute:: timestamp, in microsecond, 1e-6 second.

.. py:class:: samna.dynapse1.Dynapse1Event()

    TODO. variant including Spike and TimestampWrapEvent.


Dynapse1Synapse
^^^^^^^^^^^^^^^^^^^^^^^^^^
.. py:class:: samna.dynapse1.Dynapse1Synapse(syn_type, listen_neuron_id, listen_core_id)

    :param samna.dynapse1.Dynapse1SynType syn_type: synapse type.
    :param int listen_neuron_id: listened pre neuron id .
    :param int listen_core_id: listened pre core id.

    .. py:attribute:: syn_type
        :type: samna.dynapse1.Dynapse1SynType
    .. py:attribute:: listen_neuron_id
    .. py:attribute:: listen_core_id

Dynapse1SynType
^^^^^^^^^^^^^^^^^^^^^^^^^^
.. py:class:: samna.dynapse1.Dynapse1SynType

    .. py:attribute:: samna.dynapse1.Dynapse1SynType.AMPA
    
        Fast excitatory synapse. Old FAST_EXC synapse.

    .. py:attribute:: samna.dynapse1.Dynapse1SynType.NMDA

        Slow excitatory synapse. Old SLOW_EXC synapse.

    .. py:attribute:: samna.dynapse1.Dynapse1SynType.GABA_B

        Slow inhibitory synapse. Old SLOW_INH synapse.

    .. py:attribute:: samna.dynapse1.Dynapse1SynType.GABA_A

        Shunting inhibitory synapse. Old FAST_INH synapse.

Dynapse1Destination
^^^^^^^^^^^^^^^^^^^^^^^^
.. py:class:: samna.dynapse1.Dynapse1Destination(target_chip_id, in_use, virtual_core_id, core_mask, sx, sy, dx, dy)

    :param int target_chip_id: target post chip id.
    :param bool in_use: if this destination is occupied or not.
    :param int virtual_core_id: virtual_coreId.
    :param int core_mask: target core mask.
    :param int sx: sx.
    :param int sy: sy.
    :param int dx: dx .
    :param int dy: dy.

    .. py:attribute:: target_chip_id
    .. py:attribute:: in_use
    .. py:attribute:: virtual_core_id
    .. py:attribute:: core_mask
    .. py:attribute:: sx
    .. py:attribute:: sy
    .. py:attribute:: dx
    .. py:attribute:: dy
    

Dynapse1Neuron
^^^^^^^^^^^^^^^^^^^^^^^^
.. py:class:: samna.dynapse1.Dynapse1Neuron(chip_id, core_id, neuron_id)

    :param int chip_id: chip_id, [0,4).
    :param int core_id: core_id, [0,4).
    :param int neuron_id: neuron_id, [0,256).

    .. py:attribute:: chip_id
        :type: int
    .. py:attribute:: core_id
        :type: int
    .. py:attribute:: neuron_id
        :type: int
    .. py:attribute:: synapses
        :type: list[samna.dynapse1.Dynapse1Synapse]
    .. py:attribute:: destinations
        :type: list[samna.dynapse1.Dynapse1Destination]

Dynapse1Core
^^^^^^^^^^^^^^^^^^^^^^^^
.. py:class:: samna.dynapse1.Dynapse1Core(chip_id, core_id)

    :param int chip_id: chip_id, [0,4).
    :param int core_id: core_id, [0,4).

    .. py:attribute:: chip_id
        :type: int
    .. py:attribute:: core_id
        :type: int
    .. py:attribute:: neurons

        256 neurons in this core.

        :type: list[samna.dynapse1.Dynapse1Neuron]
    .. py:attribute:: parameter_group

        Parameter group of this core.

        :type: samna.dynapse1.Dynapse1ParameterGroup

Dynapse1ParameterGroup
^^^^^^^^^^^^^^^^^^^^^^^^
.. py:class:: samna.dynapse1.Dynapse1ParameterGroup()

    .. py:attribute:: param_map

        Parameters in this parameter group.

        :type: dict[string, samna.dynapse1.Dynapse1Parameter]

    .. py:attribute:: chip_id
        :type: int

    .. py:attribute:: core_id
        :type: int

    ..py:method:: get_parameter_by_name(param_name)

        Get a Dynapse1Parameter from the parameter group given the parameter name.

        :param string param_name: parameter name.


    ..py:method:: get_linear_parameter(param_name)

        Get a Dynapse1Parameter from the parameter group given the parameter name.

        :param string param_name: parameter name.
        :returns: linear_param_value
        :rtype: float


Dynapse1Parameter
^^^^^^^^^^^^^^^^^^^^^^^^
.. py:class:: samna.dynapse1.Dynapse1Parameter(param_name, coarse_value, fine_value)

    :param string param_name: parameter name.
    :param int coarse_value: parameter coarse value, [0, 8).
    :param int fine_value: parameter fine value, [0, 256).

    .. py:attribute:: param_name
        :type: string

    .. py:attribute:: coarse_value
        :type: int

    .. py:attribute:: fine_value
        :type: int

    .. py:attribute:: type

        Parameter type in one of the following names:

        .. code-block:: 

            "IF_THR_N", "PS_WEIGHT_INH_S_N", "PS_WEIGHT_INH_F_N", "PS_WEIGHT_EXC_S_N",
            "PS_WEIGHT_EXC_F_N", "IF_RFR_N", "IF_TAU1_N", "IF_AHTAU_N", "IF_CASC_N", "IF_TAU2_N", "IF_BUF_P",
            "IF_AHTHR_N", "NPDPIE_THR_S_P", "NPDPIE_THR_F_P", "NPDPII_THR_F_P", "NPDPII_THR_S_P",
            "IF_NMDA_N", "IF_DC_P", "IF_AHW_P", "NPDPII_TAU_S_P", "NPDPII_TAU_F_P", "NPDPIE_TAU_F_P",
            "NPDPIE_TAU_S_P", "R2R_P", "PULSE_PWLK_P".

        :type: string

Dynapse1Chip
^^^^^^^^^^^^^^^^^^^^^^^
.. py:class:: samna.dynapse1.Dynapse1Chip()

    .. py:attribute:: chip_id
        
        Range: [0,4)

        :type: int
    
    .. py:attribute:: cores

        4 cores of the chip.

        :type: list[samna.dynapse1.Dynapse1Core]

Dynapse1Configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. py:class:: samna.dynapse1.Dynapse1Configuration()

    .. py:attribute:: chips

        4 chips of the configuration.

        :type: list[samna.dynapse1.Dynapse1Chip]