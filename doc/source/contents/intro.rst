About DYNAP-SE1
=======================

A DYNAP-SE1 board has 4 :func:`chips <samna.dynapse1.Dynapse1Chip>` and each chip contains 4 
:func:`cores <samna.dynapse1.Dynapse1Core>` featuring 256 silicon :func:`neurons <samna.dynapse1.Dynapse1Neuron>`. 
We call the state of the 4 chips a :func:`configuration <samna.dynapse1.Dynapse1Configuration>`. 
Each silicon neuron has 64 :func:`synapses <samna.dynapse1.Dynapse1Synapse>` to receive the incoming connections of its presynaptic neurons. 
Each core holds a :func:`parameter group  <samna.dynapse1.Dynapse1ParameterGroup>` to store the neuronal and synaptic parameters for its 256 neurons and their incoming synapses. 
The neurons in the same core share the same parameter values. 
There are 4 types of synapses: AMPA, NMDA, GABA_A, and GABA_B. 
1024 spike generators are available implemented on the FPGA. 
Each of the spike generator can be used as a :func:`Poisson spike generator <Dynapse1PoissonGen>` or a :func:`normal FPGA spike generator <Dynapse1FpgaSpikeGen>`.

To use DYNAP-SE1, we recommend a utilities `library <https://gitlab.com/neuroinf/ctxctl_contrib/-/tree/samna-dynapse1>`_ based on Samna, developed primarily by the `NCS 
group <https://www.ini.uzh.ch/en/research/groups/ncs.html>`_ of `INI <https://www.ini.uzh.ch/en.html>`_. 
This Python repository adds more features to Samna for DYNAP-SE1, which wraps around the plain Samna classes and functions to provide more user-friendly and convenient Python APIs 
for constructing networks, configuring hardware parameters, monitoring neurons activity, implementing learning algorithms, etc.

To get started, choose a directory and do the following to download the library:

.. code-block:: bash

    git clone git@gitlab.com:neuroinf/ctxctl_contrib.git
    cd ctxctl_contrib
    git checkout samna-dynapse1