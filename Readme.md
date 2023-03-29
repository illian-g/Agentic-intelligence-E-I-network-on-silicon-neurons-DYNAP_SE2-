# Documentation 
- The documentation of Samna is [here](https://synsense-sys-int.gitlab.io/samna/) in which 
DYNAP-SE1 related part is this [section](
https://synsense-sys-int.gitlab.io/samna/devkits/dynapSeSeries/dynapse1/summary.html). 
The documentation of this [Python utilities library
](https://gitlab.com/neuroinf/ctxctl_contrib/-/tree/samna-dynapse1) of 
Samna for DYNAP-SE1 is [here](https://neuroinf.gitlab.io/ctxctl_contrib/).

  ---
  **NOTE**

  The automatically generated APIs of this library may still have some issues to be displayed in 
  [Modules](https://neuroinf.gitlab.io/ctxctl_contrib/contents/modules.html) and [APIs Summary](
  https://neuroinf.gitlab.io/ctxctl_contrib/contents/api_sum.html). To compile the latest
  doc locally, please follow this `How to compile the doc?` [section](#How-to-compile-the-doc-?).
  The PDF version of the manual is at the [samna-dynapse1-doc](
  https://gitlab.com/neuroinf/ctxctl_contrib/-/tree/samna-dynapse1-doc) 
  branch of this repository, which might be a bit
  out-dated compared to the compiled one. 

  ---


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
       
