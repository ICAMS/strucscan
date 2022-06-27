---
title: 'strucscan: A lightweight Python-based framework for high-throughput material simulation'
tags:
  - Python
  - material simulation
  - high-throughput  
  - ab initio
authors:
  - name: Isabel Pietka
    affiliation: 1
  - name: Ralf Drautz
    affiliation: 1
  - name: Thomas Hammerschmidt
    affiliation: 1 
affiliations:
 - name: Ruhr University Bochum, Interdisciplinary Centre for Advanced Materials Simulation (ICAMS)
   index: 1

date: April 2022
bibliography: paper.bib
---

# Summary

The development of new materials by computational materials science relies to a large degree on the prediction
of material properties by simulation at different time and length scales. A common challenge at the atomic scale
is the need for large numbers of calculations in order to sample, e.g., different chemical compositions, different
crystal structures or different simulation settings. Typical examples of the required high-throughput calculations
are (i) the sampling of the combinatorial space of structure and composition for determining the most stable 
structure of a mixture of chemical elements, (ii) the generation of a data set for constructing an interatomic 
interaction model or (iii) the generation of a data set for inferring properties by machine learning.
Depending on the problem at hand, the number of required calculations may range from hundreds to millions.

The Python-based framework strucscan provides a robust solution to handle such high-throughput calculations
in an efficient way on compute clusters with a queueing system or on the local host. The simple and transparent 
workflow of strucscan loops over a specified list of crystal structures and chemical compositions and computes a 
specified list of properties for each combination. The property calculations are represented as a pipeline of 
successive, interdependent steps which can easily be adapted and extended. The data is stored in a human-readable 
data tree with flat hierarchy. Strucscan performs a series of scalable and easily extendable pre-processing and 
post-processing steps and compiles the results in Python dictionaries for further evaluation. Data provenance for 
research-data management and analytics is realized in terms of the data-tree structure that includes all input 
files.

The present version of strucscan is tailored to the calculation of frequently needed material properties with
widely used atomistic simulation codes on common scheduling systems. The implemented interfaces particularly
support the VASP software package [@Kresse-96], [@Kresse-96b], [@Kresse-99] for density-functional theory (DFT)
calculations on SunGridEngine [@sge] and slurm [@slurm] scheduler systems. With the well-defined and documented 
interfaces, strucscan can be extended with basic programming skills to further scheduling systems, to further
simulation codes and material properties at the atomic scale or to other simulation scales.

# Statement of need

The need for high-throughput calculations in computational materials science lead to the development of several
workflow managers and high-throughput frameworks ([@pymatgen], [@strucscan], [@atomate], [@pyiron], [@aiida], [@asr]). 
These software packages offer numerous features but often require a rather complex infrastructure with, e.g.,
external workflow managers [@FireWorks] for interaction with compute clusters or SQL databases for storing results. 
Moreover, it is often not straightforward to extend these large software packages and to tailor them for 
particular needs. In many practical cases, the repetitive execution of the tasks does not benefit 
from a large toolbox of features or from a predefined database concept but rather needs a concise and transparent 
driver that can be customized to the particular high-throughput task and the specific data management solution.
Strucscan is a lightweight driver with focus on atomistic simulations and offers the following features:

- Transparency: lean and lightweight Python code with transparent and robust handling of tasks and infrastructure
- Dependencies: no external workflow managers or database systems required, only NumPy and ASE [@ase]
- Customization: straight-forward extension to further tasks and interfaces (simulation codes, schedulers) with 
  only low-level programming experience
- Pipelining: simple and transparent realization of task sequences and task dependencies
- Restarts: seamless restart capabilities due to coherent interlinking of workflow organisation and data tree
- Post-processing: customizable post-processing within workflow with results stored in Python dictionaries for 
  further post-processing
- Data provenance: human-readable data tree with flat hierarchy and storage of all input files for metadata 
  generation

# Strucscan

The strucscan framework is based on Python 3.6+ and requires the Atomic Simulation Environment [@ase] and NumPy. 
It is available from a git repository and can be installed with pip or directly with conda (TODO).
Detailed documentation and usage examples of strucscan are available on ??? (TODO). 
High-throughput calculations with strucscan can be started from the command line, from a Python shell or from 
a Juypter notebook as shown in the examples in the strucscan git repository.
The present version is focused on high-throughput DFT calculations on computer clusters with SunGridEngine [@sge] 
and slurm [@slurm] scheduler systems. Future extension to further simulation codes are planned.

The basic workflow of strucscan is visualized in Fig. \autoref{fig:workflow} and includes the following step:

![Workflow of the strucscan framework: the process starts with creating 
a list of jobs by looping over structures and pipelining 
the properties. Any required dependencies will be resolved and inserted
into the list of jobs. Depending on the status of the job, 
the job is monitored if running (or queued), files will be created 
if necessary, and errors will be handled automatically.
If the job is finished successfully, data is collected and a simple
post-processing is conducted \label{fig:workflow}](workflow.pdf)

1. *Input from user* 

The user specifies the materials simulation software and the usage of the scheduler system or localhost.
The input information includes the chemical elements with the required parameter files, the structure files
and the tasks to be performed. The currently implemented tasks are related to materials properties and
include, e.g., the relaxation of the structure or the computation of the equilibrium lattice constant.
The input can be organized in a YAML file format for starting strucscan from the command line or in a 
Python dictionary for starting strucscan from a python shell or a Jupyter Notebook. 

2. *Initialization of workflow*

Based on the input from the user, strucscan generates of list of all necessary calculations by looping 
over the list of given structures and the list of tasks.
In the context of materials properties, a common task is the full relaxation of a crystal structure from
an initial guess of the atomic positions and simulation cell to a configuration that takes a minimum 
total energy in a DFT calculation. This task is often followed by second task where the total energy is
computed with DFT for a series of volumes of the simulation cell around the equilibrium volume and a 
subsequent fit of this energy-volume data to obtain the minimum with high accuracy.
For such interdependent tasks, strucscan uses a pipelining concept that converts the final structure of
one task to the initial structure of a subsequent task. I.e. each structure is pipelined through the list 
of properties. The pipelines are also treated as tasks and can be easily be modified by the user.
In this way the user can operate with higher-level pipeline names and strucscan will automatically insert 
all required tasks along a pipeline.
Continuing with the above example, strucscan provides a pipeline 'EOS' that collects the values of
the equilibrium volume after fitting the energy-volume data after computing the energy-volume data after 
performing a full relaxation.
The result of the workflow initialization is a list of all necessary calculations, '*jobs*', that is 
directly reflected in the structure of the data tree. A restart of strucscan with the same user input 
will find the existing data tree and continue seamlessly after the last finished 
calculation.

3. *Execution of tasks*

After the initialization, strucscan identifies the status of each *job* by checking if the expected
folders exist in the data tree, if it is waiting or running in the scheduler, if it is finished or
if an error occurred. Depending on the status, strucscan will create the necessary input files, start
the calculation or handle an error. This stage is repeated until the list of jobs is complete.
In order to avoid uncontrolled restarts, a job is declared as finished if error handling has been 
attempted unsuccessfully for three times.

4. *Post-processing of results*

At the end of each workflow cycle, strucscan starts post-processing of the calculation results.  
It will collect the central results from the data tree and compile them in Python dictionaries in JSON 
format for further post-processing or for database upload. 
In the context of materials properties the post-processing by strucscan includes, e.g., the fitting of 
energy-volume data to an equation of state and the compilation of the resulting equilibrium volume,
binding energy and bulk modulus in one JSON file for all given structures of a given chemical element
or compound.

# Acknowledgements

The  author  acknowledges  funding  by  the  Deutsche Forschungsgemeinschaft (DFG) through project  C1 
of the collaborative research center SFB/TR 103 (DFG project number 190389738).

# References
