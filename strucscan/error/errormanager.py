from strucscan.engine.vasp import Vasp
from strucscan.error.errorhandler import *


def determine_status__job_id(calc, jobpath, job_list):
    """
    - checks job ib jobpath on any errors
    - if the job has been restarted more than 3 times, the job status is set to (1, 'error') which leads the JobManager to count the job as finished, i.e. to stop monitoring it
    - if the job has been restarted less than 3 times, the engine specific errorhandler is called

    Legend
    - 0 : does not exist
    - 0 : queued
    - 0 : error
    - 1 : error
    - 1 : finished

    :param calc: (strucscan.engine.generalengine.GeneralEngine object) calculator object
    :param jobpath: (str) absolute path to job directory
    :param job_list: (list) list of all JobObjects
    :return: (int, str, str) tuple of job status index (int), status (str) and job id (str).
    On queuing systems, job_id equilas queue id, on systems without queue, job_id euqils process id
    """
    index = None
    job_id = None
    nrestarts = 0
    jobobject = None

    status_index, status = (1, "error")
    for ind, _jobobject in enumerate(job_list):
        _jobpath = _jobobject.get_jobpath()
        _job_id = _jobobject.get_job_id()
        _nrestarts = _jobobject.get_nrestarts()
        if jobpath == _jobpath:
            index = ind
            job_id = _job_id
            nrestarts = _nrestarts
            jobobject = _jobobject

    if jobobject is None:
        pass
    else:
        nrestarts += 1
        if nrestarts > 3:
            pass
        else:
            jobobject.set_nrestarts(nrestarts)
            job_list[index] = jobobject
            if isinstance(calc, Vasp):
                status_index, status, job_id = VaspErrorManager(calc, jobpath, job_id).return_status__job_id()
            # here you can add ErrorManagers for further engines
    return status_index, status, job_id, nrestarts
