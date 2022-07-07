# Getting started

## Trying strucscan

You can try some examples provided with strucscan using [Binder](https://mybinder.org/) 
without installing the package. Please use [this link] to try the package.

## Installation

### Supported operating systems

strucscan can be installed on Linux based systems only.

### Installation using [conda](https://anaconda.org)

strucscan can be installed directly using Conda from the conda-forge channel by the following statement
```
conda install -c conda-forge strucscan
```

This is the recommended way to install if you have an Anaconda distribution.

### Installation using pip

strucscan is not available on pip directly. However, strucscan can be installed using pip by
```
pip install pybind11
pip install git+https://github.com/ICAMS/strucscan
```

### Installation from the repository

strucscan can be built from the repository by
```
git clone <link>
cd strucscan
pip install .
```

### Using a conda environment

strucscan can also be installed in a conda environment, making it easier to manage dependencies. 
A python3 Conda environment can be created by,
```
conda create -n myenv python=3
```
Once created, the environment can be activated using,
```
conda activate myenv
```
Now the strucscan repository can be cloned and the module can be installed. 
Python dependencies are installed automatically.
```
(myenv) git clone https://github.com/ICAMS/strucscan.git
(myenv) cd strucscan
(myenv) pip install .
```


### Dependencies

-   [numpy](https://numpy.org/)
-   [ase](https://wiki.fysik.dtu.dk/ase/)

