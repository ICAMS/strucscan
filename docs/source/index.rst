strucscan: A lightweight Python-based framework for high-throughput material simulation
=========================================================================================

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
support the VASP software package [(Kresse, 1996)](https://doi.org/10.1016/0927-0256(96)00008-0), [(Kresse, 1996)](https://doi.org/10.1103/PhysRevB.54.11169), [(Kresse, 1999)](https://doi.org/10.1103/PhysRevB.59.1758) for density-functional theory (DFT)
calculations on SunGridEngine [(Gentzsch, 2001)](https://doi.org/10.1109/CCGRID.2001.923173) and slurm [(Yoo, 2003)](https://doi.org/10.1007/10968987_3) scheduler systems. With the well-defined and documented
interfaces, strucscan can be extended with basic programming skills to further scheduling systems, to further
simulation codes and material properties at the atomic scale and to other simulation scales.

Highlights
----------

- transparency: lean and lightweight Python code with transparent and robust handling of tasks and infrastructure
- dependencies: no external workflow managers or database systems required, only NumPy and ASE [(Larsen, 2017)](https://doi.org/10.1088/1361-648X/aa680e)
- customization: straight-forward extension to further tasks and interfaces (simulation codes, schedulers) with
  only low-level programming experience
- pipelining: simple and transparent realization of task sequences and task dependencies
- restarts: seamless restart capabilities due to coherent interlinking of workflow organisation and data tree
- post-processing: customizable post-processing within workflow with results stored in Python dictionaries for
  further post-processing
- data provenance: human-readable data tree with flat hierarchy and storage of all input files for metadata
  generation

Documentation
-------------

.. toctree::

    downloadandinstall
    methodsandexamples
    modules
    prologue/extending
    prologue/helpandsupport
    prologue/citing
    prologue/acknowledgements
    prologue/license

