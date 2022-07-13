# Strucscan

strucscan provides a lightweight Python-based framework for high-throughput material simulation 
that loops over a specified list of input structures and computes a specified list of properties
on compute clusters with a queueing system or on the local host. The property calculations are 
represented as a pipeline of successive, interdependent steps which can easily be adapted and 
extended. The data is stored in a human-readable data tree with flat hierarchy. Strucscan performs 
a series of scalable and easily extendable pre-processing and post-processing steps and compiles 
the results in Python dictionaries for further evaluation. strucscan comes with interfaces to the
VASP software package for ab-initio calculations. The VASP software itself is not included in this
distribution.

# Documentation

A detailed documentation can be found [here](https://strucscan.readthedocs.io/).

# Installation and setup

1. clone repository into a `<directory>` of your choice. Please clone 'master' branch only.
2.  `cd` in your cloned `strucscan` directory and type 
```
pip3 install .
```
3. set-up `~/.strucscan` resource file: copy `.strucscan` in your home directory and set it up 
   according to your preferences. \
   These configurations can be edited all the time and are read in by strucsan at every start. \
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


## Dependencies
- ase
- numpy
- scipy
- spglib

    
## Resource directory
The resource directory contains script templates and configurations for modules and calls that
can be tailored for specific machines. Additionally, you can deposit parameters and settings 
for the individual engine. The resource directory is organized like this:
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

### Example: machineconfig/example_vasp/config.yaml with parallel and serial executable of a VASP engine
```
VASP:
  parallel: | # this pipe is essential for reading multi-line entries
    module load vasp/mpi/5.4.4
    mpirun -np $NTOTALCORES vasp_std
  serial: | # this pipe is essential for reading multi-line entries
    module load vasp/serial/5.4.4
    vasp_std
```

### Example: machineconfig/vulcan.machinescripts/parallel12.sge with scheduler settings for parallel execution
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

## Starting Strucscan

You can start strucscan from the command line using: 
```
strucscan input.yaml
```

Several example calculations with input files are given in the notebooks in `strucscan/examples`.
