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

- [`Introductory Jupyter Notebook with the basic functionality rundown`](https://code.ini.uzh.ch/ncs/libs/dynap-se1/-/blob/main/Samna_demo.ipynb) - the main introduction to using this repository
- [`User Guide - DYNAP-SE1`](https://docs.google.com/document/d/e/2PACX-1vQV36QRWsQl4ROfvRo7mbHb5_ZQ4Q1Qw64AkfdhuPEtIXYq1kf_ZsD3-GZkYPKqrlkOiizCq-Jjt_kD/pub?urp=gmail_link&gxid=8203366) - in-detail overview of the lower level chip behaviour with the legacy chip control software CAER
- [`Video tutorial from the course NI06 - Neuromorphic Processor `](https://tube.switch.ch/switchcast/uzh.ch/events/383ee32a-58b8-48d5-bed0-a915ce341961) 
- [`How to Set up Biases`](dynapse-biases-howtosetup.md) - A guide to logic behind setting the biases of the chip

## Related Repositories 
-------
- teili: [`pypi`](https://pypi.org/project/teili/), [`docu`](https://teili.readthedocs.io/en/latest/) - a Brian2 library to model the on-chip circuit behaviour
- [`PyGetScope`](https://code.ini.uzh.ch/ncs/libs/pygetscope) library for working with Agilent scopes as a standalone repository (same as the included submodule here)

## Papers
-------

- [`Paper with DPI equations`](https://ieeexplore.ieee.org/document/6809149)

## Inventory
-------

- [`Google Sheets for DYNAP-SE Inventory`](https://docs.google.com/spreadsheets/d/1nH2ihmJopggJwHB5A8NmtKlDbAkQdN7nsJvuaCBwr5c/edit?usp=sharing)

## Booking-System
-------

- [`Team-up Booking for access to dynapse1`](https://teamup.com/kszuuhkh7ss24gerzz)

# Installation

Install Samna version 0.17 (verified to work with this repository)

  ```bash
  pip install samna==0.17
  ```

See more details in the [install](https://synsense-sys-int.gitlab.io/samna/install.html) section of Samna documentation.

# Connecting to VPN and Zemo

## INI's new VPN

 ```bash
  sudo openfortivpn sslvpn.ini.uzh.ch:10443 -u saghos  --trusted-cert 389bf6fd691373e230f11d05acba0634c45d0ded98eaaec49b521e9374af81ca
  ```

You’ll need to use a new VPN server provided for INI by UZH. The UZH is using a VPN solution from Fortinet. The name of the server is sslvpn.ini.uzh.ch (130.60.23.50) port 10443. For some clients this may be entered as <tt>sslvpn.ini.uzh.ch:10443</tt>.  Remember this is now a UZH service so please make sure to login with your UZH credentials (not INI). Clients for almost all system are available from https://forticlient.com/downloads If you do not have a UZH account, please contact us.

On Windows 10 you can use [https://www.microsoft.com/en-us/p/forticlient/9wzdncrdh6mc?activetab=pivot:overviewtab  FortiClient-Win10] if you want to remember your username and password.  But no one has managed to make this client work yet. If you make it work, please edit wiki to show the magic. Setting DNS server numbers manually in network WAN miniport does not help.

On linux we suggest you install the *openfortivpn* package and run VPN via the following command, replacing <UZH-shortname> with your UZH shortname:

<tt>$ sudo openfortivpn sslvpn.ini.uzh.ch:10443 -u </tt>'''<UZH-shortname>'''<tt> </tt>

Note that you need to use UZH credentials, i.e. UZH shortname and password, not INI credentials, as this service is provided by UZH.

openfortivpn is also solution when you need command line VPN. 

It is possible to set up fortivpn via the package network-manager-fortisslvpn-gnome that makes it available to the gnome network manager (might need reboot or restart of network-manager service after install of package). 

If it does not work with that method (DNS problem), edit the VPN connection, go to IPv4 and add the following two DNS servers (instead of automatic):

<tt>130.60.128.3</tt>

<tt>130.60.64.51</tt>

Install Samna version 0.17 (verified to work with this repository)

  ```bash
  pip install samna==0.17
  ```


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
       
