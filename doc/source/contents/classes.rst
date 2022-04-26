Classes and methods
======================

Higher-level APIs
-------------------------

Open and close device
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The implementation of the higher-level mothods are in files NetworkGenerator.py and Dynapse1Utils.py.


Neuron event filter
^^^^^^^^^^^^^^^^^^^^^^^



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
