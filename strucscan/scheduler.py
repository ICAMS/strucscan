import subprocess
import yaml
import os

from strucscan.utils import read_configuration


class GeneralScheduler:
    def __init__(self, machinename):
        """
        Abstract class for general queuing system

        :param machinename: (str) name of machine. This is equals to the directory name
        containing the config.yaml and machinescripts for the specific machine.
        """
        self.machinename = machinename
        self.suffix = "sh" # should be adapted to specific scheduler system

        self.configurations = read_configuration()
        self.machine_configuration_dict = get_machine_configuration_dict(machinename)

        self.MACHINE_SCRIPT_PATH = "{}/machineconfig/{}/machinescripts". \
            format(self.configurations["RESOURCE_PATH"], self.machinename)

    def get_smallest_queue(self):
        """
        :return: (str) name of the smallest queue available on this machine.
        """
        try:
            return self.machine_configuration_dict["smallest queue"]
        except:
            return ""

    def configure_machine_script(self, machine_info, jobname="noname"):
        """
        SunGridEngine specific method to configure machine script.

        :param machine_info: (dict) machine information about queue, nnodes, ncores provided by user in input.yaml
        :param jobname: (str) name of job
        :return: (str list, str) tuple of (machine file lines, machine file name)
        """
        queuename = machine_info["queuename"]
        PATH_TO_MACHINE_SCRIPT = "{}/{}.{}".format(self.MACHINE_SCRIPT_PATH, queuename, self.suffix)
        with open(PATH_TO_MACHINE_SCRIPT, "r") as f:
            machine_script = f.readlines()
        ncores = int(machine_info["ncores"])
        nnodes = int(machine_info["nnodes"])
        ntotalcores = int(ncores * nnodes)
        for i, line in enumerate(machine_script):
            if "[JOB_NAME]" in line:
                machine_script[i] = line.replace("[JOB_NAME]", jobname)
            if "[NCORES]" in line:
                machine_script[i] = line.replace("[NCORES]", str(ncores))
            if "[NNODES]" in line:
                machine_script[i] = line.replace("[NNODES]", str(nnodes))
            if "[NTOTALCORES]" in line:
                machine_script[i] = line.replace("[NTOTALCORES]", str(ntotalcores))
        machine_script_fname = jobname + "." + self.suffix
        return machine_script, machine_script_fname

    def submit(self, machinefilename):
        """
        Abstract method to submit machine file with 'machine_script_fname'

        :param machinefilename: (str) name of machine script
        :return: id of job in scheduler: on queuing systems, job_id equilas queue id,
        on systems without queue, job_id equals process id
        """
        raise NotImplementedError

    @staticmethod
    def get_queue_ids():
        """
        Abstract method that returns str list of all job ids in queue. On systems without queue, job_id equals process id

        :return: (str list) str list of all job ids in queue. On systems without queue, job_id equals process id
        """
        raise NotImplementedError

    def is_job_id_in_queue(self, job_id):
        """
        Abstract method

        :param job_id: (str) id of job: on queuing systems, job_id equilas queue id,
        on systems without queue, job_id equals process id
        :return: (bool) if job id is queue / process list or not
        """
        raise NotImplementedError

    def get_job_id_by_jobpath(self, jobpath):
        """
        Abstract method

        :param jobpath: (str) absolute path to job directory
        :return: (str) id of job: on queuing systems, job_id equilas queue id,
        on systems without queue, job_id equals process id
        """
        raise NotImplementedError

    def get_total_number_of_cores(self, machine_script):
        """
        Abstract method that scans the machine_script and returns total number of cores used for calculation

        :param machine_script: (str) machine script lines
        :return: (int) total number of cores
        """
        raise NotImplementedError


class SunGridEngine(GeneralScheduler):
    def __init__(self, machinename):
        """
        Scheduler class for SunGridEngine queuing system

        :param machinename: (str) name of machine. This is equals to the directory name
        containing the config.yaml and machinescripts for the specific machine.
        """
        GeneralScheduler.__init__(self, machinename)
        self.suffix = "sge" # file suffix appended to machine_script_fname: script.sge

    def submit(self, machine_script_fname):
        """
        SunGridEngine specific method to submit machine file with 'machine_script_fname'

        :param machine_script_fname: (str) name of machine script
        :return: id of job: on queuing systems, job_id equilas queue id,
        on systems without queue, job_id equals process id
        """
        cmd = subprocess.Popen("qsub " + machine_script_fname,
                               shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        output, err = cmd.communicate()
        if output:
            job_id = str(output).split()[2]
            return job_id
        else:
            if ("error opening" in str(err)) and ("No such file or directory" in str(err)):
                for file in os.listdir(os.getcwd()):
                    if "." + self.suffix in file:
                        machine_script_fname = file
                        cmd = subprocess.Popen("qsub " + machine_script_fname,
                                               shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
                        output, err = cmd.communicate()
                        if output:
                            job_id = str(output).split()[2]
                            return job_id
            else:
                raise FileNotFoundError(err)

    @staticmethod
    def get_queue_ids():
        """
        SunGridEngine specific method that returns str list of all job ids in queue.

        On systems without queue, job_id equals process id
        :return: (str list) str list of all job ids in queue. On systems without queue, job_id equals process id
        """
        cmd = subprocess.Popen("qstat", shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        output, err = cmd.communicate()
        queue_ids = [line.split()[0] for line in str(output)[2:-1].split("\\n")[2:-1]]
        return queue_ids

    def is_job_id_in_queue(self, job_id):
        """
        SunGridEngine specific method

        :param job_id: (str) id of job: on queuing systems, job_id equilas queue id, on systems without queue, job_id equals process id
        :return: (bool) if job id is queue / process list or not
        """
        queue_ids = self.get_queue_ids()
        if queue_ids is None:
            return False
        else:
            if job_id in self.get_queue_ids():
                return True

    def get_job_id_by_jobpath(self, jobpath):
        """
        SunGridEngine specific method

        :param jobpath: (str) absolute path to job directory
        :return: (str) id of job: on queuing systems, job_id equilas queue id, on systems without queue, job_id equals process id
        """
        queue_ids = self.get_queue_ids()
        job_id = None
        if queue_ids is not None:
            for id in queue_ids:
                cmd = subprocess.Popen("qstat -j %s | grep sge_o_workdir" % id,
                                       shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
                output, err = cmd.communicate()
                if output:
                    sge_o_workdir = str(output)[2:-3].split()[-1]
                    if jobpath == sge_o_workdir:
                        job_id = id
        return job_id

    def get_total_number_of_cores(self, machine_script):
        """
        SunGridEngine specific method that scans the machine_script and returns total number of cores
        used for calculation

        :param machine_script: (str) machine script lines
        :return: (int) total number of cores
        """
        ntotalcores = 1
        for ind, line in enumerate(machine_script):
            if "#$ -pe" in line:
                ntotalcores = int(machine_script[ind].split()[-1])
        return ntotalcores


class Slurm(GeneralScheduler):
    def __init__(self, machinename):
        """
        Scheduler class for SunGridEngine queuing system

        :param machinename: (str) name of machine. This is equals to the directory name
        containing the config.yaml and machinescripts for the specific machine.
        """
        GeneralScheduler.__init__(self, machinename)
        self.suffix = "slurm" # file suffix appended to machine_script_fname: script.sge

    @staticmethod
    def get_queue_ids():
        """
        Slurm specific method that returns str list of all job ids in queue. On systems without queue, job_id equals process id

        :return: (str list) str list of all job ids in queue. On systems without queue, job_id equals process id
        """
        cmd = subprocess.Popen("sacct", shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        output, err = cmd.communicate()
        queue_ids = [line.split()[0] for line in str(output)[2:-1].split("\\n")[2:-1]]
        return queue_ids

    def is_job_id_in_queue(self, job_id):
        """
        Slurm specific method

        :param job_id: (str) id of job: on queuing systems, job_id equilas queue id, on systems without queue, job_id equals process id
        :return: (bool) if job id is queue / process list or not
        """
        queue_ids = self.get_queue_ids()
        if queue_ids is None:
            return False
        else:
            if job_id in queue_ids:
                return True

    def get_job_id_by_jobpath(self, jobpath):
        """
        Slurm specific method

        :param jobpath: (str) absolute path to job directory
        :return: (str) id of job: on queuing systems, job_id equilas queue id,
        on systems without queue, job_id equals process id
        """
        queue_ids = self.get_queue_ids()
        job_id = None
        if queue_ids is not None:
            for id in queue_ids:
                cmd = subprocess.Popen("scontrol show job %s | grep WorkDir" % id, shell=True, stderr=subprocess.PIPE,
                                       stdout=subprocess.PIPE)
                output, err = cmd.communicate()
                if output:
                    workdir = str(output)[2:-3].split()[-1].split("WorkDir=")[-1]
                    if jobpath == workdir:
                        job_id = id
        return job_id

    def submit(self, machine_script_fname):
        """
        Slurm specific method to submit machine file with 'machine_script_fname'

        :param machine_script_fname: (str) name of machine script
        :return: id of job: on queuing systems, job_id equilas queue id, on systems without queue, job_id equals process id
        """
        cmd = subprocess.Popen("sbatch " + machine_script_fname, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        output, err = cmd.communicate()
        if output:
            jobID = str(output).split()[3][:-3]
            return jobID
        else:
            cmd = subprocess.Popen("machinename", shell=True, stderr=subprocess.PIPE,
                                   stdout=subprocess.PIPE)
            output, err = cmd.communicate()
            if output:
                hostname = str(output)[2:-3]
            else:
                hostname = "unknown host"
            raise AttributeError("{} has no queueing system.".format(hostname))

    def get_total_number_of_cores(self, machine_script):
        """
        Slurm specific method that scans the machine_script and returns total number of cores
        used for calculation

        :param machine_script: (str) machine script lines
        :return: (int) total number of cores
        """
        ntotalcores = 1
        for ind, line in enumerate(machine_script):
            if "#SBATCH -n" in line:
                ntotalcores = int(machine_script[ind].split()[-1])
        return ntotalcores


class NoQueue(GeneralScheduler):
    def __init__(self, machinename):
        """
        Scheduler class for no queuing system

        :param machinename: (str) name of machine. This is equals to the directory name
        containing the config.yaml and machinescripts for the specific machine.
        """
        GeneralScheduler.__init__(self, machinename)

    def configure_machine_script(self, machine_info, jobname="noname"):
        """
        SunGridEngine specific method to configure machine script.

        :param machine_info: (dict) machine information about queue, nnodes, ncores provided by user in input.yaml
        :param jobname: (str) name of job
        :return: (str list, str) tuple of (machine file lines, machine file name)
        """
        machine_script = ["#!/bin/bash\n"]
        machine_script_fname = jobname + "." + self.suffix
        return machine_script, machine_script_fname

    def submit(self, machine_script_fname):
        """
        Method to submit machine file with 'machine_script_fname'

        :param machine_script_fname: (str) name of machine script
        :return: id of job: on queuing systems, job_id equilas queue id,
        on systems without queue, job_id equals process id
        """
        cmd = subprocess.Popen("chmod +x %s" % machine_script_fname,
                               shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        output, err = cmd.communicate()
        cmd = subprocess.Popen("./%s &" % machine_script_fname,
                               shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        output, err = cmd.communicate()
        return None

    def get_job_id_by_jobpath(self, jobpath):
        """
        :param jobpath: (str) absolute path to job directory
        :return: (str) id of job: on queuing systems, job_id equilas queue id, on systems without queue, job_id equals process id
        """
        raise NotImplementedError

    def get_total_number_of_cores(self, machine_script):
        """
        Localhost specific method that scans the machine_script and returns total number of cores
        used for calculation

        :param machine_script: (str) machine script lines
        :return: (int) total number of cores
        """
        return 1


def get_machine_configuration_dict(machinename):
    """
    :return: (dict) machine configuration dictionary
    """
    try:
        configurations = read_configuration()
        MACHINE_CONFIGURATION_PATH = "{}/machineconfig/{}".format(configurations["RESOURCE_PATH"], machinename)
        with open(MACHINE_CONFIGURATION_PATH + "/config.yaml", "r") as stream:
            machine_configuration_dict = yaml.safe_load(stream)
        return machine_configuration_dict
    except Exception as err:
        raise err
