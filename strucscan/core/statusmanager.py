from strucscan.error import errormanager
from strucscan.scheduler import NoQueue

import os

FINISHED = "finished"               # 1
RUNNING = "running"                 # 0
QUEUED = "queued"                   # 0
NOT_EXISTING = "does not exist"     # 0
ERROR = "error"                     # 1/0


def determine_status__job_id(calc, jobpath, job_list):
    """
    On queuing systems, job_id is queue id, on systems without queue, job_id euqils process id

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
    """
    status_index, status, job_id = (0, NOT_EXISTING, None)
    if os.path.exists(jobpath):
        os.chdir(jobpath)
        files = os.listdir(jobpath)
        if "end.dat" in files:
            if calc.check_if_finished(files):
                status_index, status, job_id = (1, FINISHED, None)
            else:
                status_index, status, job_id, _ = errormanager.determine_status__job_id(calc, jobpath, job_list)
        else:
            if isinstance(calc.get_scheduler(), NoQueue):
                if "start.dat" in files:
                    status_index, status, job_id = (0, RUNNING, None)
                else:
                    status_index, status, job_id = (0, NOT_EXISTING, None)
            else:
                job_id = calc.scheduler.get_job_id_by_jobpath(jobpath)
                if calc.scheduler.is_job_id_in_queue(job_id):
                    if calc.has_resultfile(files):
                        status_index, status, job_id = (0, RUNNING, job_id)
                    else:
                        status_index, status, job_id = (0, QUEUED, job_id)
                else:
                    status_index, status, job_id, _ = errormanager.determine_status__job_id(calc, jobpath, job_list)
    return status_index, status, job_id
