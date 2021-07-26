- The documentation of Samna for DYNAP-SE1 is at https://code.ini.uzh.ch/jzhao/samna-dynapse1-doc.

- monitor_neuron() error should be fixed in the new Samna release, version 0.7.19. To get the new version, you can do:
  
    ```pip install samna [--upgrade] --index-url https://gitlab.com/api/v4/projects/27423070/packages/pypi/simple```

    ```--upgrade``` is needed if you already installed Samna.

    Please note that we do not release on pypi anymore.

- We added some new features to the Python libs (mainly in NetworkGenerator.py), e.g. NeuronGroup, several add_connections* functions to create connections between 2 neuron groups, more convenient printing for Neuron and Network, etc. Specifically, this example (https://gitlab.com/neuroinf/ctxctl_contrib/-/blob/samna-dynapse1/example/example_neuronGroup.py) shows you a more convenient way of creating a network.