strucscan Reference
================

strucscan.core module
------------------

Main module of strucscan. This module contains definitions of the two major
classes, :class:`strucscan.core.jobmanager.JobManager` and :class:`strucscan.core.jobmaker.JobMaker`.
Both communicate together with :class:`strucscan.core.datatree`, :class:`strucscan.core.statusmanager`,
and :class:`strucscan.core.collector`
to initialize a list of :class:`strucscan.core.jobobject`s
which is updated and monitored.

.. automodule:: strucscan.core
   :members:
   :undoc-members:
   :show-inheritance:


This module contains classes that build the interface to the certain material simulation codes.
Each interface class inherit the abstract class :class:`strucscan.engine.generalengine.GeneralEngine`.

strucscan.engine module
---------------------------------

.. automodule:: strucscan.engine.generalengine.GeneralEngine
   :members:
   :undoc-members:
   :show-inheritance:


strucscan.properties module
--------------------

This module contains classes that generate (pre-process) the structure files
for each material property. Each property class inherit the abstract class
:class:`strucscan.properties.generalproperty.GeneralProperty`.


strucscan.error module
--------------------

This module contains classes to manage and handle occuring errors. Similar to the
:class:`stucscan.core.statusmanager.`, the :class:`stucscan.error.errormanager.`
checks the type of error and hands it over to the :class:`stucscan.error.errorhandler.`
related to the material code that generated the job files.

.. automodule:: strucscan.error.errormanager
   :members:
   :undoc-members:
   :show-inheritance:


strucscan.scheduler module
--------------------

This module contains classes that build the interface to queueing systems (and machines without any queue).
Each interface class inherit the abstract class :class:`strucscan.scheduler.GeneralScheduler`.


.. automodule:: strucscan.scheduler.GeneralScheduler
   :members:
   :undoc-members:
   :show-inheritance:
