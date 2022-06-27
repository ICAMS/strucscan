from copy import deepcopy

from strucscan.utils import get_new_chemical_formula_from_atoms


class JobObject():
    def __init__(self, species, property,
                 jobpath="", basis_ref_atoms=None, basis_ref_structpath="", stochio="",
                 status_index=1, status="finished", job_id=None, nrestarts=0,
                 scale_atoms=True, conditional_files=""):
        """
        - contains most important information about a job
        - each job is assigned one JobObject
        - the JobObject object is stored in the job_list

        :param jobpath: (str) absolute path to job directory
        :param basis_ref_atoms: (ASE atoms object) atoms object as read from structure file
                      (without assigned chemical symbols, magnetic moments, ...)
        :param species: (str) space-separated species, e.g. 'Al Ni'
        :param basis_ref_structpath: (str) absolute path to structure file
        :param property: (str) name of property
        :param status_index: (int) indicates status of job: 0 = not finished, 1 = finished
        :param status: (str) detailed status of job: 'queued', 'running', 'error', or 'finished'
        :param job_id: (str) id of job: on queuing systems, job_id is queue id,
                             on systems without queue, job_id is None
        :param nrestarts: (int) number of restarts. The job will declared as (1, 'error') if nrestarts > 3
        :param requires_condition: (bool) True if any prerequisite calculation is required
        :param condition_finished: (bool) True if required prerequisite calculation is finished
        """
        self.species = species
        self.property = property
        self.jobpath = jobpath
        self.basis_ref_atoms = basis_ref_atoms
        self.structpath = basis_ref_structpath
        self.stochio = stochio
        self.status_index = status_index
        self.status = status
        self.job_id = job_id
        self.nrestarts = nrestarts
        self.scale_atoms = scale_atoms
        self.conditional_files = conditional_files

        if self.job_id is None:
            self.job_id = "None"

    def get_jobpath(self):
        """
        :return: (str) absolute path to job directory
        """
        return self.jobpath

    def set_jobpath(self, jobpath):
        """
        :param jobpath: (str) absolute path to job directory
        :return: 0
        """
        self.jobpath = jobpath
        return

    def get_basis_ref_atoms(self):
        """
        :return: (ASE atoms object) atoms object
        """
        return self.basis_ref_atoms

    def get_species(self):
        """
        :return: (str) space separated species, e.g. 'Al Ni'
        """
        return self.species

    def get_stochio(self):
        """
        :return: (str) chemical formula
        """
        return self.stochio

    def get_structpath(self):
        """
        :return: (str) absolute path to structure file
        """
        return self.structpath

    def get_property(self):
        """
        :return: (str) name of property
        """
        return self.property

    def get_status_index(self):
        """
        :return: (int) indicates status of job: 0 = not finished, 1 = finished
        """
        return self.status_index

    def get_status(self):
        """
        :return: (str) detailed status of job: 'queued', 'running', 'error', or 'finished'
        """
        return self.status

    def get_status_index_job_id(self):
        """
        :return: (int) status_index, (str) status, (str) job_id
        """
        return self.status_index, self.status, self.job_id

    def set_status_index_job_id(self, status_index, status, job_id):
        """

        :param status_index: (int) indicates status of job: 0 = not finished, 1 = finished
        :param status: (str) detailed status of job: 'queued', 'running', 'error', or 'finished'
        :param job_id: (str) id of job: on queuing systems, job_id is queue id,
                             on systems without queue, job_id is None
        :return: 0
        """
        self.status_index = status_index
        self.status = status
        self.job_id = job_id
        return

    def get_job_id(self):
        """
        :return: (str) id of job: on queuing systems, job_id is queue id,
                             on systems without queue, job_id is None
        """
        return self.job_id

    def get_nrestarts(self):
        """
        :return: (int) number of restarts. The job will declared as (1, 'error') if nrestarts > 3
        """
        return self.nrestarts

    def set_nrestarts(self, nrestarts):
        """"
        :param nrestarts: (int) number of restarts. The job will declared as (1, 'error') if nrestarts > 3
        """
        self.nrestarts = nrestarts
