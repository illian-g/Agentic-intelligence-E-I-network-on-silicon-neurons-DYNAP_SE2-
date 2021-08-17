- The documentation of Samna for DYNAP-SE1 is at https://code.ini.uzh.ch/jzhao/samna-dynapse1-doc.

- Installation:

    - To get the latest version, you can do:
        
        ```pip install samna [--upgrade] --index-url https://gitlab.com/api/v4/projects/27423070/packages/pypi/simple```
        
        ```--upgrade``` is needed if you already installed Samna.

    - To get a specific version, e.g. 0.7.19, you can do:
        
        ```pip install samna==0.7.19 -i https://gitlab.com/api/v4/projects/27423070/packages/pypi/simple```

    - Please note that we do not release on pypi anymore, which means you cannot see any releases after 0.7.13.0 on pypi webpage https://pypi.org/project/samna/#history.

- monitor_neuron() error should be fixed in version 0.7.19.

- We added some new features to the Python libs (mainly in NetworkGenerator.py), e.g. NeuronGroup, several add_connections* functions to create connections between 2 neuron groups, more convenient printing for Neuron and Network, etc. Specifically, this example (https://gitlab.com/neuroinf/ctxctl_contrib/-/blob/samna-dynapse1/example/example_neuronGroup.py) shows you a more convenient way of creating a network.

- Dynapse1TraceNode goes into version 0.8.22.0 which can be used to do STDP-like learning.

- Issue: the GUI and matplotlib.pyplot may not work depending on your system.
  - If you get the error below, please `open_dynapse1` without GUI.
    > samna.open_remote_node(visualizer_id, viz_name)
    RuntimeError: Store with ID: 3 timed out on content request

  - If you get the error below, please avoid using `matplotlib.pyplot`.
    > free(): invalid pointer
    [1]    18258 abort (core dumped)