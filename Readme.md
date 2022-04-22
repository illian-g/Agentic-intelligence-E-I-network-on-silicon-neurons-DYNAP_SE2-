# Documentation 
- The documentation of Samna for DYNAP-SE1 is [here](https://code.ini.uzh.ch/jzhao/samna-dynapse1-doc). The manual of Samna 0.14.10.0 is [here](https://synsense-sys-int.gitlab.io/samna/).
- This branch (```samna-dynapse1```) works with Samna 0.14.10.0. For an old version, please use branch ```samna-dynapse1-0.8.32.0``` which is compatible with Samna 0.8.32.0.

# Installation

- Method 1: to get the latest version, you can do:
    
    ```bash
    pip install samna
    ```
    
    This installs the samna loader package. The full module is loaded with the first ```import samna```.
- Method 2:
  ```bash
  pip install samna [--upgrade] --index-url https://gitlab.com/api/v4/projects/27423070/packages/pypi/simple
  ```
  ```--upgrade``` is needed if you already installed Samna and want to have the latest version.

- Method 3: If the latest version does NOT work, you can roll back to version 0.8.32.0 by doing:
  ```bash
  pip install samna==0.8.32.0 -i https://gitlab.com/api/v4/projects/27423070/packages/pypi/simple
  ```
  And use branch ```samna-dynapse1-0.8.32.0```

See more details in the [install](https://synsense-sys-int.gitlab.io/samna/install.html) section of Samna documentation.

# How to compile the sphinx doc?
- Install [sphinx](https://www.sphinx-doc.org/en/master/) following the instructions [here](https://www.sphinx-doc.org/en/master/usage/installation.html).
- Then go to the `doc` folder and compile the document.

```bash
cd doc
make html
```
The html files will be generated under `doc/build/html`.

# How to contribute?
Please read [How to contribute?](https://gitlab.com/neuroinf/ctxctl_contrib/-/tree/master) and you need to change `master` branch to `samna-dynapse1`.        

# Debugging
1. The GUI and `matplotlib.pyplot` may not work depending on your system.
  - If you get the error below, please `open_dynapse1` without GUI.
    > samna.open_remote_node(visualizer_id, viz_name)
    RuntimeError: Store with ID: 3 timed out on content request

  - If you get the error below, please avoid importing `matplotlib.pyplot` together with `Samna`.
    > free(): invalid pointer
    [1]    18258 abort (core dumped)

# Update history
- monitor_neuron() error should be fixed in version 0.7.19.

- We added some new features to the Python libs (mainly in [netgen.py](https://gitlab.com/neuroinf/ctxctl_contrib/-/blob/samna-dynapse1/netgen.py)), e.g. NeuronGroup, several add_connections* functions to create connections between 2 neuron groups, more convenient printing for Neuron and Network, etc. Specifically, this [example](https://gitlab.com/neuroinf/ctxctl_contrib/-/blob/samna-dynapse1/example/example_neuron_group.py) shows you a more convenient way of creating a network.

- New Samna version 0.8.22.0 comes with new features!
  - "Dynapse1NeuronTrace" filter node is implemented, which can be used to track instantaneous firing rates, or to do STDP-like learning. [Here](https://gitlab.com/neuroinf/ctxctl_contrib/-/blob/samna-dynapse1/test/with_hardware/trace_stdp_WIP/neuron_trace_test.py) is an example showing how the trace filter works, and this [script](https://gitlab.com/neuroinf/ctxctl_contrib/-/blob/samna-dynapse1/example/test_stdp.py) is a simple STDP learning example.
  - "Dynapse1NeuronSelect" update: `set_neurons()` now accepts tuple neuron ID list, i.e. list[(int,int,int)] indicating (chip,core,neuron) IDs, instead of global neuron ids. Please adapt your scripts accordingly. 
  
- The Python [libraries](https://gitlab.com/neuroinf/ctxctl_contrib/-/tree/samna-dynapse1) are updated as well.
  - File names are changed to match Python name convention: e.g. NetworkGenerator.py -> netgen.py, Dynapse1Constants.py -> dynapse1constants.py, Dynapse1Utils.py -> dynapse1utils.py, etc. Sorry for the inconvenience, but please modify your import accordingly.
  - STDP modules are added so that implementation of STDP-like learning are supported. Check this [script](https://gitlab.com/neuroinf/ctxctl_contrib/-/blob/samna-dynapse1/example/test_stdp.py) as a simple learning example.