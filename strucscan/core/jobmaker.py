from strucscan.core import statusmanager
from strucscan.core.datatree import get_basis_ref_structpath_and_conditional_jobpath
from strucscan.core.jobobject import JobObject
from strucscan.utils import STRUCT_FILE_FORMAT, SEPERATOR, scale_by_atvolume, read_structure_from_file
from strucscan.error import errormanager
from strucscan.resources.properties import *

from ase import io

import os
import copy


class JobMaker:
    def __init__(self, job_list, calc, input_dict):
        """
        - initializes queried jobs in job_list
        - updates job status (monitoring)
        - conducts file creation

        :param job_list: (list) list of all JobObjects
        :param calc: (strucscan.engine.generalengine.GeneralEngine object) calculator object
        :param input_dict: (dict) input dictionary. Please follow to the examples in strucscan.resources.inputyaml
        """
        self.job_list = job_list
        self.calc = calc
        self.input_dict = input_dict
        self.inner_job_list = []
        self.VERBOSE = self.input_dict["verbose"]

    def initialize_jobs(self, structpath, properties):
        """
        :param structpath: (str) absolute path to structure file
        :param properties: (str list) list of assembled properties known to strucscan
        :return: (jobobject list) list of stucscan.core.jobobject.JobObject objects
        """
        # remove any valence specific suffix from VASP POTCARs
        species = " ".join([s.split("_")[0] for s in self.input_dict["species"].split()])
        atoms = read_structure_from_file(structpath, species, STRUCT_FILE_FORMAT())
        stochio = atoms.get_chemical_formula()

        first_property = properties[0]
        first_jobobject = JobObject(species, first_property, basis_ref_atoms=atoms, stochio=stochio, nrestarts=0)
        jobpath = self.calc.get_absolute_jobpath(first_property, first_jobobject, structpath=structpath)
        first_jobobject.set_jobpath(jobpath)
        status_index, status, job_id = statusmanager.determine_status__job_id(self.calc, jobpath, self.job_list)
        first_jobobject.set_status_index_job_id(status_index, status, job_id)

        conditional_files = ""
        basis_ref_structpath = structpath
        if first_property in ADVANCED_PROPERTIES:
            basis_ref_structpath, conditional_files = get_basis_ref_structpath_and_conditional_jobpath(
                self.calc, first_jobobject.get_jobpath())
        first_jobobject.conditional_files = conditional_files
        first_jobobject.structpath = basis_ref_structpath
        self.inner_job_list.append(first_jobobject)

        if len(properties) > 1:
            basis_ref_structpath = first_jobobject.get_jobpath() + "/" + self.calc.final_struct_fname
            for property in properties:
                jobpath = self.calc.get_absolute_jobpath(property, first_jobobject, structpath=structpath)
                status_index, status, job_id = statusmanager.determine_status__job_id(self.calc, jobpath, self.job_list)

                conditional_files = first_jobobject.get_jobpath()
                if property in ADVANCED_PROPERTIES:
                    basis_ref_structpath, conditional_files = get_basis_ref_structpath_and_conditional_jobpath(
                        self.calc, jobpath)
                atoms = None
                if statusmanager.determine_status__job_id(
                        self.calc, conditional_files, self.job_list)[1] == "finished":
                    atoms = io.read(basis_ref_structpath, format=self.calc.struct_file_format)

                jobobject = JobObject(species, property,
                                      jobpath=jobpath,
                                      basis_ref_atoms=atoms,
                                      basis_ref_structpath=basis_ref_structpath,
                                      stochio=stochio,
                                      status_index=status_index,
                                      status=status,
                                      job_id=job_id,
                                      nrestarts=0,
                                      scale_atoms=False,
                                      conditional_files=conditional_files)
                basis_ref_structpath = jobobject.get_jobpath() + "/" + self.calc.final_struct_fname
                first_jobobject = jobobject
                self.inner_job_list.append(jobobject)

        # check if any conditional jobs are missing
        list_of_conditional_files = [jobobject.conditional_files for jobobject in self.inner_job_list]
        list_of_jobpaths = [jobobject.get_jobpath() for jobobject in self.inner_job_list]
        for conditional_files in list_of_conditional_files:
            if (conditional_files not in list_of_jobpaths) and (conditional_files != ""):
                status_index, status, job_id = statusmanager.determine_status__job_id(
                    self.calc, conditional_files, self.job_list)
                property = conditional_files.split("/")[-1].split(SEPERATOR)[0]
                basis_ref_structpath, _conditional_files = get_basis_ref_structpath_and_conditional_jobpath(
                    self.calc, conditional_files)
                atoms = None
                if statusmanager.determine_status__job_id(
                        self.calc, _conditional_files, self.job_list)[1] == "finished":
                    atoms = io.read(basis_ref_structpath, format=self.calc.struct_file_format)
                if (_conditional_files == conditional_files):
                    _conditional_files = ""
                    basis_ref_structpath = ""
                    atoms = read_structure_from_file(structpath, species, STRUCT_FILE_FORMAT())
                jobobject = JobObject(species, property,
                                      jobpath=conditional_files,
                                      basis_ref_atoms=atoms,
                                      basis_ref_structpath=basis_ref_structpath,
                                      stochio=stochio,
                                      status_index=status_index,
                                      status=status,
                                      job_id=job_id,
                                      nrestarts=0,
                                      scale_atoms=False,
                                      conditional_files=_conditional_files)
                self.inner_job_list.insert(0, jobobject)
        return self.inner_job_list

    def update(self, jobobject):
        """
        :param jobobject: (strucscan.core.jobobject.JobObject object) object that contains information about job
        :return: (strucscan.core.jobobject.JobObject object) updated JobObject
        """
        jobpath = jobobject.get_jobpath()
        status = jobobject.get_status()
        nrestarts = jobobject.get_nrestarts()

        if status == statusmanager.NOT_EXISTING:
            if (jobobject.conditional_files == "") or (statusmanager.determine_status__job_id(
                    self.calc, jobobject.conditional_files, self.job_list)[1] == "finished"):
                if jobobject.basis_ref_atoms is None:
                    jobobject.basis_ref_atoms = io.read(jobobject.structpath, format=self.calc.struct_file_format)
                self.create_job_files(jobobject)
        elif status == statusmanager.QUEUED:
            pass
        elif status == statusmanager.RUNNING:
            pass
        elif status == statusmanager.ERROR:
            status_index, status, job_id, nrestarts = errormanager.determine_status__job_id(self.calc, jobpath, self.job_list)
        elif status == statusmanager.FINISHED:
            pass

        # update jobobject
        status_index, status, job_id = statusmanager.determine_status__job_id(self.calc, jobpath, self.job_list)
        _jobobject = copy.deepcopy(jobobject)
        _jobobject.set_status_index_job_id(status_index, status, job_id)
        _jobobject.set_nrestarts(nrestarts)
        return _jobobject

    def adpat_queue_to_smallest_queue_if_neccessary(self, atoms):
        """
        - adapts initial machine configuration dictionary to 'smallest' queue
        - this ensures that not a multi-core queue is used for a 'small' structure

        :param atoms: (ASE atoms object) ASE atoms object
        :return: (dict)
        """
        machine_info = {"queuename": self.input_dict["queuename"],
                         "ncores": self.input_dict["ncores"],
                         "nnodes": self.input_dict["nnodes"]
                         }
        ntotalcores = int(machine_info["ncores"]) * int(machine_info["nnodes"])
        if isinstance(atoms, list):
            atoms = atoms[0]
        if (len(atoms) < 8) and (ntotalcores > 1):
            try:
               machine_info["queuename"] = self.calc.scheduler.get_smallest_queue()
               machine_info["ncores"] = 1
               machine_info["nnodes"] = 1
            except KeyError:
                # NoQueue
                pass
        return machine_info

    def make_files(self, jobobject):
        """
        - wrapper around strucscan.engine.generalengine.GeneralEngine.make_inputfiles
        - submits job if given by user

        :param jobobject: (strucscan.core.jobobject.JobObject object) object that contains information about job
        :return: 0
        """
        atoms = jobobject.basis_ref_atoms
        jobpath = jobobject.get_jobpath()
        machine_info = self.adpat_queue_to_smallest_queue_if_neccessary(atoms)
        machine_script_fname = self.calc.make_inputfiles(machine_info, jobobject)
        if self.input_dict["submit"] and machine_script_fname:
            self.submit_job(jobpath, machine_script_fname)
        return

    def create_job_files(self, jobobject):
        """
        - checks jobobject property if pre-processing is necessary
        - if so, jobobject atoms will be updated
        - calls JobMaker.make_files()

        :param jobobject: (strucscan.core.jobobject.JobObject object) object that contains information about job
        :return: 0
        """
        property = jobobject.property
        if (property in ADVANCED_PROPERTIES) and (statusmanager.determine_status__job_id(
                self.calc, jobobject.conditional_files, self.job_list)[1] == "finished"):
            atoms = self.get_advanced_prototypes(jobobject)
            jobobject.basis_ref_atoms = atoms
            self.make_files(jobobject)
        else:
            atoms = jobobject.basis_ref_atoms
            if jobobject.scale_atoms:
                atoms = scale_by_atvolume(atoms, self.input_dict["initial atvolume"])
            jobobject.basis_ref_atoms = atoms
            self.make_files(jobobject)
        return

    def submit_job(self, jobpath, machinefilename):
        """
        - wrapper around strucscan.engine.generalengine.GeneralEngine.submit_job
        - checks job status before submission

        :param jobpath: (str) absolute path to job directory
        :param machinefilename: (str) filename of submission script / machine script
        :return: 0
        """
        _, jobstatus, job_id = statusmanager.determine_status__job_id(self.calc, jobpath, self.job_list)
        if (jobstatus == statusmanager.NOT_EXISTING) or (jobstatus == statusmanager.ERROR):
            os.chdir(jobpath)
            job_id = self.calc.submit_job(machinefilename)
            if self.VERBOSE:
                if job_id is not None:
                    print("Submitted:", jobpath.split("/")[-1], " (" + job_id + ")")
                else:
                    print("Submitted:", jobpath.split("/")[-1])
        return

    def get_advanced_prototypes(self, jobobject):
        property = jobobject.property
        basis_ref = jobobject.basis_ref_atoms
        if "eos" in property:
            from strucscan.properties import eos
            strained_structures = eos.generate_structures(basis_ref)
            return strained_structures
        return
