# Documentation 
- The documentation of Samna is [here](https://synsense-sys-int.gitlab.io/samna/) in which 
DYNAP-SE1 related part is this [section](
https://synsense-sys-int.gitlab.io/samna/devkits/dynapSeSeries/dynapse1/summary.html). 
The documentation of this [Python utilities library
](https://code.ini.uzh.ch/ncs/libs/dynap-se1) of 
Samna for DYNAP-SE1 is [here](https://neuroinf.gitlab.io/ctxctl_contrib/).

  ---
  **NOTE**

  The automatically generated APIs of this library may still have some issues to be displayed in 
  [Modules](https://neuroinf.gitlab.io/ctxctl_contrib/contents/modules.html) and [APIs Summary](
  https://neuroinf.gitlab.io/ctxctl_contrib/contents/api_sum.html). To compile the latest
  doc locally, please follow this [How to compile the doc?](#How-to-compile-the-doc-?) section.
  The PDF version of the manual is at the [samna-dynapse1-doc](
  https://gitlab.com/neuroinf/ctxctl_contrib/-/tree/samna-dynapse1-doc) 
  branch of this repository, which might be a bit
  out-dated compared to the compiled one. 

  ---

- [`User Guide - DYNAP-SE1`](https://docs.google.com/document/d/e/2PACX-1vQV36QRWsQl4ROfvRo7mbHb5_ZQ4Q1Qw64AkfdhuPEtIXYq1kf_ZsD3-GZkYPKqrlkOiizCq-Jjt_kD/pub?urp=gmail_link&gxid=8203366) - in-detail overview of the lower level chip behaviour with the legacy chip control software CAER
- [`Video tutorial from the course NI06 - Neuromorphic Processor `](https://tube.switch.ch/switchcast/uzh.ch/events/383ee32a-58b8-48d5-bed0-a915ce341961) 
- [`GUI demo`](https://gitlab.com/neuroinf/ctxctl_contrib/-/tree/samna-dynapse1-NI-demo 
) 
- [`How to Set up Biases`](https://code.ini.uzh.ch/ncs/expt/dynapse-biases-howtosetup) - A guide to logic behind setting the biases of the chip

## Related Repositories 
-------
- teili: [`pypi`](https://pypi.org/project/teili/), [`docu`](https://teili.readthedocs.io/en/latest/) - a Brian2 library to model the on-chip circuit behaviour
- [`PyGetScope`](https://code.ini.uzh.ch/ncs/libs/pygetscope) library for working with Agilent scopes as a standalone repository (same as the included submodule here)

## Papers
-------

- [`Paper with DPI equations`](https://ieeexplore.ieee.org/document/6809149)

# Installation

Install Samna version 0.18 (verified to work with this repository)

  ```bash
  pip install samna==0.18
  ```

See more details in the [install](https://synsense-sys-int.gitlab.io/samna/install.html) section of Samna documentation.

# How to compile the doc?
- To compile the sphinx doc in this repository, install [sphinx](
https://www.sphinx-doc.org/en/master/) following the instructions
[here](https://www.sphinx-doc.org/en/master/usage/installation.html).

```bash
python -m pip install sphinx sphinx_book_theme sphinx-autodoc-typehints sphinxcontrib-napoleon
```
- Then go to the `doc` folder and compile the document into html or PDF format.
  - html:

    ```bash
    cd doc
    make html
    ```
    The html files will be generated under `doc/build/html`.

  - PDF:
    ```bash
    cd doc
    make latexpdf
    ```
    The PDF file `samna-dynapse1.pdf` will be generated under `doc/build/latex`.
       
