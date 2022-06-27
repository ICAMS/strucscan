from shutil import copyfile

from ase import io

from strucscan.core import datatree
from strucscan.scheduler import *


class GeneralErrorManager:
    def __init__(self, calc, jobpath, job_id):
        """
        abstract ErrorManager object

        :param calc: (strucscan.engine.generalengine.GeneralEngine object) calculator object
        :param jobpath: (str) absolute path to job directory
        :param job_id: (str) id of job in scheduler: on queuing systems, job_id equilas queue id, on systems without queue, job_id euqils process id
        """
        self.calc = calc
        self.jobpath = jobpath
        self.job_id = job_id
        self.status_index, self.status = (1, "error")

    def adapt_machinfile(self):
        """
        - adapts machine file of failed job for restart

        :return: (str list) adapted machine file
        """
        raise NotImplementedError

    def return_status__job_id(self):
        """
        :return: (int, str, str) tuple of job status index (int), status (str) and job id (str).
        On queuing systems, job_id equilas queue id, on systems without queue, job_id euqils process id
        """
        return self.status_index, self.status, self.job_id


class VaspErrorManager(GeneralErrorManager):
    def __init__(self, calc, jobpath, job_id):
        GeneralErrorManager.__init__(self, calc, jobpath, job_id)

        calculator, composition, property, prototype, stochio = datatree.parse_absolute_path(jobpath)
        jobname = calc.subjobname(composition, property)
        suffix = get_machinefile_suffix(calc)
        self.machinefilename = jobname + "." + suffix

        if not os.path.exists(jobpath):
            raise NotADirectoryError("Job directory has not been created.")
        else:
            files = os.listdir(jobpath)
            if "vasp.out" not in files:
#                # error in submission script
                self.status__job_id = (1, "error", self.job_id)
            elif ("vasp.out" in files) and ("OUTCAR" not in files):
                # vasp_std started but canceled immediately
                self.status__job_id = (1, "error", self.job_id)
            elif ("vasp.out" in files) and ("OUTCAR" and files):
                print("VaspErrorManager: Job outtimed, copying CONTCAR to POSCAR")
                # vasp_std started, scheduler had no time to gzip OUTCAR, job timed out
                os.chdir(jobpath)
                try:
                    io.read("CONTCAR", format="vasp")
                except IndexError:
                    # no lines written to CONTCAR, too less memory, ...
                    self.status_index, self.status, self.job_id = (1, "error", self.job_id)
                else:
                    copyfile("CONTCAR", "POSCAR")

                    n_structures, n_finished = determine_left_over_structures(jobpath,
                                                                              resultfilename="OUTCAR",
                                                                              strucfilename="POSCAR")
                    if n_structures > 0:
                        self.machinefile = self.adapt_machinfile()
                        with open(self.jobpath + "/" + self.machinefilename, "w") as f:
                            for line in self.machinefile:
                                f.write(line)

                    job_id = calc.submit_job(self.machinefilename)
                    self.status_index, self.status, self.job_id = (0, "queued", job_id)
            elif "OUTCAR.gz" in files:
                # vasp_std started and finished, error in subroutines, memory error, ...
                self.status_index, self.status, self.job_id = (1, "error", self.job_id)

    def adapt_machinfile(self):
        """
        - adapts machine file of failed job for restart

        :return: (str list) adapted machine file
        """
        machinefile = []
        try:
            with open(self.machinefilename, "r") as f:
                machinefile = f.readlines()
        except FileNotFoundError:
            raise

        if machinefile != []:
            header, footer, binary_call = split_machinefile_into_header_footer_binary_call(machinefile)
            n_structures, n_finished = determine_left_over_structures(self.jobpath, resultfilename="OUTCAR", strucfilename="POSCAR")
            header.append("\n")

            ntotalcores = self.calc.get_scheduler().get_total_number_of_cores(machinefile)
            pe = "serial"
            if ntotalcores > 1:
                pe = "parallel"
            config = self.calc.machine_configuration_dict["VASP"][pe]
            prerequisites = config.split("\n")[:-2]
            for prerequisite in prerequisites:
                header.append(prerequisite)
            header.append("\n")

            for ind in range(n_finished, n_structures-n_finished):
                header.append("cp POSCAR-%i POSCAR\n" % ind)
                header.append("%s\n" % binary_call)
                header.append("gzip OUTCAR\n")
                header.append("gzip OUTCAR.gz OUTCAR-%i.gz\n" % ind)
                header.append("gzip vasprun.xml.gz\n")
                header.append("mv vasprun.xml.gz vasprun.xml-%i.gz\n" % ind)
                header.append("")
            header.append("rm WAVECAR EIGENVAL CHG DOSCAR IBZKPT REPORT XDATCAR PROCAR PCDAT vasp.out")
            for line in footer:
                header.append(line)
            return header
        else:
            raise FileNotFoundError("No machine file with name {} in {} found!".format(self.machinefilename, self.jobpath))


def get_machinefile_suffix(calc):
    """
    :param calc: (strucscan.engine.generalengine.GeneralEngine object) calculator object
    :return: (str) machine file name suffix. E.g., for slurm it is '.slurm'. See for strucscan.scheduler
    """
    return calc.get_scheduler().suffix


def split_machinefile_into_header_footer_binary_call(machinefile):
    """
    - devides machine file in three string lists by header, footer, and everything in between ('call')

    :param machinefile: (str list) list of lines from machine file
    :return: (str, str, str) head, footer, call
    """
    header_last_line_index = 0
    for ind, line in enumerate(machinefile):
        if "echo \"property" in line:
            header_last_line_index = ind+1
    header = machinefile[:header_last_line_index]

    footer_last_line_index = 0
    for ind, line in enumerate(machinefile):
        if "STOP=`date`" in line:
            footer_last_line_index = ind
    footer = machinefile[footer_last_line_index:]

    call = ""
    for ind, line in enumerate(machinefile):
        if ">&" in line:
            call = line.strip("\n")
    return header, footer, call


def determine_left_over_structures(jobpath, resultfilename="", strucfilename=""):
    """
    - if job requires to calculate multiple structures, e.g. E-V curves, ..., this method determines
    the number of total structures required and the number of already finished structures

    :param jobpath: (str) path to working directory
    :param resultfilename: (str) final result file name. For VASP, e.g. it is "OUTCAR"
    :param strucfilename: (str) structure file name. For VASP, e.g. it is "POSCAR"
    :return: (int, int) number of total struture files in jobpath, number of finished structures in jobpath
    """
    files = os.listdir(jobpath)
    n_todo = 0
    n_finished = 0
    for file in files:
        if (resultfilename + "-" in file) and (".gz" in file):
            n_finished += 1
        if strucfilename + "-" in file:
            n_todo += 1
    n_structures = n_todo + n_finished
    return n_structures, n_finished
