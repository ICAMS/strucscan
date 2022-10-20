# Getting started

## Trying strucscan

You can try some examples provided with strucscan using [Binder](https://mybinder.org/) 
without installing the package. Please use [this link](https://mybinder.org/v2/gh/ICAMS/strucscan/main) to try the package.

## Installation

### Supported operating systems

strucscan can be installed on Linux based systems only.


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



### Setup

#### Configuration file

After installing strucscan successfully you need to set-up the `.strucscan` configuration file. 
A [template](https://github.com/ICAMS/strucscan/blob/main/.strucscan) can be found in the github repository. 
Copy the file to your home directory and configure it to your preferences. 
These configurations can be edited all the time and are read in by strucsan at every start.

   **Mandatory keys:**
   - `PROJECT_PATH`: (str) top node of your data tree.
   - `STRUCTURES_PATH`: (str) top node of your structure pool.
   - `RESOURCE_PATH`: (str) path to configuration files for binaries, submission script, 
     engines settings and potential files.
     
   **Optional keys:**
   - `DEBUG`: (bool) enables print commands for more insight. Default is `False`.
   - `STRUCT_FILE_FORMAT`: (str) structure file format of your structure files. 
     Valid values are all formats comptabile with `ase.io.read` method. Default is `cfg`.
   - `SLEEP_TIME`: (int) Time in sec that strucscan will rest before starting the next monitoring loop. Default are 60 s.


#### Structure directory

This directory should contain a pool of structure files. 
Exemplarily, a [template](https://github.com/ICAMS/strucscan/tree/main/examples/structures/unaries) 
can be found in the examples on github.


#### Resource directory

The resource directory contains script templates and configurations for modules and calls that
can be tailored for specific machines. Additionally, you can deposit parameters and settings 
for the individual engine. A [template](https://github.com/ICAMS/strucscan/tree/main/examples/resources) 
is given in the examples on github.
The resource directory is organized like this:
```
resources
 ├── machineconfig
 │    ├── HPC1
 │    │    ├── config.yaml
 │    │    └── machinescripts
 │    │         ├── queue1.sge
 │    │         ├── queue2.sge
 │    │         └── ...
 │    │         
 │    ├── HPC2
 │    │    ├── config.yaml
 │    │    └── machinescripts
 │    │         ├── queue1.sge
 │    │         ├── queue2.sge
 │    │         └── ...
 │    │         
 │    └── ...
 │
 └── engines
      ├── vasp
      │    ├── bin
      │    ├── settings
      │    └── potentials
      │         ├── potpaw
      │         ├── potpaw_PBE
      │         └── potpaw_GGA
      │         
      ├── another_engine
      │    ├── bin
      │    ├── settings
      │    └── potentials
      │         
      └── ...
```
The machine configuration folder (machineconfig) contains the information that is required 
to start a serial or parallel calculation with the specific engine on the local host or to
submit it do the scheduler of a compute cluster.
This includes particularly modules that need to be loaded, the executable, and the queue
requests in the config.yaml file as well as additional scripts that may be needed.

##### Example: machineconfig/example_vasp/config.yaml with parallel and serial executable of a VASP engine
```
VASP:
  parallel: | # this pipe is essential for reading multi-line entries
    module load vasp/mpi/5.4.4
    mpirun -np $NTOTALCORES vasp_std
  serial: | # this pipe is essential for reading multi-line entries
    module load vasp/serial/5.4.4
    vasp_std
```

##### Example: machineconfig/dummy/machinescripts/parallel12.sge with scheduler settings for parallel execution
```
#!/bin/bash 
#$ -S /bin/tcsh 
#$ -N [JOB_NAME] 
#$ -l qname=parallel12.q 
#$ -pe mpi12 [NTOTALCORES] 
#$ -e $JOB_ID.err 
#$ -o $JOB_ID.o 
#$ -cwd 
#$ -j y 
#$ -R y 
ipcrm --all 
#START=`date` 
#HOST=`hostname` 
#QNAME="parallel12" 
#echo "start: $START $HOSTNAME  $QNAME" > start.dat
```
