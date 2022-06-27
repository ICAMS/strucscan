from strucscan.engine.generalengine import GeneralEngine
from strucscan.core import datatree
from strucscan.utils import SEPERATOR, PROJECT_PATH, RESOURCE_PATH, get_nspecies
from strucscan.scheduler import get_machine_configuration_dict
from strucscan.resources.properties import *

from ase import io

import numpy as np
import os
import subprocess


class Vasp(GeneralEngine):
    def __init__(self, input_dict):
        """
        :param input_dict: (dict) input dictionary. Please follow to the examples in strucscan.resources.inputyaml
        """
        GeneralEngine.__init__(self, input_dict)
        self.init_magmoms = self.input_dict["initial magnetic moments"]
        self.magconfig = self.input_dict["magnetic configuration"]
        self.kdens = float(self.input_dict["kdens"])
        self.kmesh = self.input_dict["kmesh"]
        self.kpointsfile = self.input_dict["k points file"]

        self.POTENTIALS_PATH = RESOURCE_PATH() + "/engines/vasp/potentials"
        self.SETTINGS_PATH = RESOURCE_PATH() + "/engines/vasp/settings"
        self.KPOINTS_PATH = RESOURCE_PATH() + "/engines/vasp/kpoints"
        self.resultfilename = "OUTCAR"
        self.final_struct_fname = "OUTCAR.gz"
        self.struct_file_format = "vasp-out"


    def get_name(self):
        """
        :return: (str) engine name that is given by user in input_dict
        """
        return self.name

    def kpoints(self, atoms, property=None):
        """
        :param atoms: (ASE atoms object)
        :param property: (str) name of property. If surface calculation, k_z is set to 1
        :return: (str list) list of lines of KPOINTS file
        """
        if property == "dos":
            self.kdens = 0.1
        kpoints = []
        if self.kpointsfile != "":
            with open(self.KPOINTS_PATH + "/" + self.kpointsfile, "r") as f:
                kpoints = f.readlines()
        else:
            l1, l2, l3 = atoms.get_cell()
            kpoints = ["Automatic mesh (cubic sys)\n",
                       "0\n",
                       self.kmesh + "\n"]
            omega = np.linalg.det(np.array([l1, l2, l3]))
            g1 = 2 * np.pi / omega * np.cross(l2, l3)
            g2 = 2 * np.pi / omega * np.cross(l3, l1)
            g3 = 2 * np.pi / omega * np.cross(l1, l2)
            kmesh = np.rint(
                np.array([np.linalg.norm(g) for g in [g1, g2, g3]]) / self.kdens
            )
            kmesh[kmesh < 1] = 1
            if property:
                pass

            kpoints.append(" %i %i %i\n" % (kmesh[0], kmesh[1], kmesh[2]))
            kpoints.append(" 0 0 0\n")
        return kpoints

    @staticmethod
    def get_magmom(atoms, initial_magmoms):
        """
        :param atoms: (ASE atoms object)
        :param initial_magmoms: (float list) list of initial magmom per element
        :return: (str) INCAR magmom tag
        """
        nspecies = get_nspecies(atoms)
        if len(initial_magmoms) < nspecies[0]:
            initial_magmoms = nspecies[0] * [initial_magmoms[0]]
        if not isinstance(initial_magmoms, np.ndarray):
            initial_magmoms = np.asarray(initial_magmoms)
        magmom = " ".join([str(n) + "*" + str(int(m)) for n, m in zip(nspecies, initial_magmoms)])
        return magmom

    @staticmethod
    def get_npar(ntotalcores):
        """
        :param ntotalcores: (int) number of total cores, that is #cores per node * #of nodes
        :return: (int) value for INCAR NPAR
        """
        npar = 1
        for i in range(int(np.floor(np.sqrt(ntotalcores))), 1, -1):
            if ntotalcores % i == 0:
                npar = i
                break
        return npar

    @staticmethod
    def parse_incar(incar):
        """
        :param incar: (str) INCAR lines read from file
        :return: (dict) dictionary in form of {INCAR_TAG : VALUE}
        """
        incar_dict = {}
        incar_lines = incar.split("\n")
        for line in incar_lines:
            try:
                key = line.split()[0]
            except IndexError:
                pass
            else:
                if key.isalpha():
                    key = line.split("=")[0].strip()
                    value = line.split("=")[1].strip()
                    incar_dict[key] = value
        if "kdens" in incar_dict:
            del incar_dict["kdens"]
        return incar_dict

    def configure_incar(self, incar_dict, atoms, ntotalcores, magconfig, initial_magmoms, property):
        """
        - parses and configures incar
        - ensures that tags are set properly (e.g, ISPIN, ISIF, ...)

        :param incar_dict: (dict) dictionary in form of {INCAR_TAG : VALUE}
        :param atoms: (ASE atoms object)
        :param ntotalcores: (int) number of total cores, that is #cores per node * #of nodes
        :param magconfig: (str) magnetic configuration: 'SP' or 'NM'
        :param initial_magmoms: (float list) list of initial magmom per element
        :param property: (str) name of property
        :return: (str list) list of lines that needs to be written to INCAR file
        """
        configuration_dict = {}

        npar = self.get_npar(ntotalcores)
        configuration_dict["NPAR"] = npar

        if magconfig == "SP":
            configuration_dict["ISPIN"] = "2"
            magmom = self.get_magmom(atoms, initial_magmoms)
            configuration_dict["MAGMOM"] = magmom

        if property in STATIC_PROPERTIES:
            configuration_dict["ISIF"] = 2
            configuration_dict["IBRION"] = -1
            configuration_dict["NSW"] = 0
        elif property in ATOMIC_PROPERTIES:
            configuration_dict["ISIF"] = 2
            configuration_dict["IBRION"] = 2
        elif property in TOTAL_PROPERTIES:
            configuration_dict["ISIF"] = 3
            configuration_dict["IBRION"] = 2
        elif property == "dos":
            configuration_dict["ISMEAR"] = -5 # tetrahedron smearing
            configuration_dict["ICHARG"] = 11 # charge density will be kept constant
            configuration_dict["NSW"] = 0
            configuration_dict["NEDOS"] = 300 # DOSCAR resolution
            configuration_dict["ISIF"] = 2
            configuration_dict["IBRION"] = -1
        else:
            raise Exception("Could not distinguish property in static, atomic, total relaxation. Exiting.")

        for key, value in configuration_dict.items():
            incar_dict[key] = str(value)

        incar_lines = []
        for key, value in incar_dict.items():
            incar_lines.append("{key:15} = {value}\n".format(key=key, value=value))
        return incar_lines

    def get_potpath(self, specie, potential):
        """
        :param specie: (str) chemical element with valence, e.g. 'Cr' or 'Cr_pv'
        :param potential: (str) 'PBE', 'LDA', or 'PW91'
        :return: (str) abosolute path to potential file
        """
        if potential == "PBE":
            potential = "potpaw_PBE"
        elif potential == "LDA":
            potential = "potpaw"
        elif potential == "PW91":
            potential = "potpaw_GGA"
        else:
            raise NameError("Unkown potential {}".format(potential))
        potpath = "{}/{}/{}/POTCAR".format(self.POTENTIALS_PATH, potential, specie)
        return potpath

    def make_inputfiles(self, machine_info, jobobject):
        """
        - method that creates / writes VASP specific input files
        - for VASP, e.g. this method has to write INCAR, KPOINTS, POSCAR, POTCAR
        - calls strucscan.engine.vasp.VASP.get_absolute_jobpath
        - calls strucscan.engine.vasp.VASP.make_machinefile
        - calls strucscan.engine.vasp.VASP.write_structure

        :param machine_info: (dict) dictionary of form {"queuename": str, "ncores": int, "nnodes": int}
        :param jobobject: (strucscan.core.jobobject.JobObject object) object that contains information about job
        :return: (str) machine_script_fname
        """
        jobpath = jobobject.get_jobpath()
        atoms = jobobject.basis_ref_atoms
        property = jobobject.property

        initial_magmoms = [float(i) for i in str(self.init_magmoms).split()]
        magconfig = "NM"
        for magmom in initial_magmoms:
            if magmom != 0:
                magconfig = "SP"
                break

        if not os.path.exists(jobpath):
            os.makedirs(jobpath)

        # machine file
        jobname = self.subjobname(self.species, property)

        ncores = int(machine_info["ncores"])
        nnodes = int(machine_info["nnodes"])
        ntotalcores = ncores * nnodes
        nsteps = 1
        if isinstance(atoms, list):
            nsteps = len(atoms)
        machinefile, machinefilename = self.make_machinefile(machine_info, jobname, ntotalcores, property, nsteps)
        with open(jobpath + "/" + machinefilename, "w") as f:
            for line in machinefile:
                f.write(line)

        # write POSCAR
        if isinstance(atoms, list):
            # this is in the case of any task that requires multiple structures for calculation,
            # e.g. E-V curves, murnaghan calculation, transformation paths, ... .
            for i, atom in enumerate(atoms):
                self.write_structure(atom, jobpath, structfilename="POSCAR-%i" % i)
            atoms = atoms[0]
        else:
            self.write_structure(atoms, jobpath)

        # read, configure INCAR
        with open("{}/{}".format(self.SETTINGS_PATH, self.settings), "r") as f:
            incarlines = f.readlines()
        incar_dict = {}
        for line in incarlines:
            if line[0].isalpha():
                key = line.split("=")[0].strip().upper()
                value = line.split("=")[-1].strip("\n").strip().upper()
                incar_dict[key] = value
        incar_lines = self.configure_incar(incar_dict, atoms, ntotalcores, magconfig, initial_magmoms, property)

        # generate KPOINTS
        kpoints = self.kpoints(atoms, property)

        # write INCAR, KPOINTS
        for file, filename in zip([incar_lines, kpoints], ["INCAR", "KPOINTS"]):
            with open(jobpath + "/" + filename, "w") as f:
                for line in file:
                    f.write(line)

        # cat POTCAR
        cat_command = ""
        for specie in self.species.split():
            cat_command += " " + self.get_potpath(specie, self.potential)
        os.system("cat {} > {}/POTCAR".format(cat_command, jobpath))
        return machinefilename

    def get_absolute_jobpath(self, property, jobobject, structpath=None):
        """
        - VASP specific method to return absolute path to job directory
        - example: 'DATA_TREE_PATH/ENGINE_SIGNATURE/RELATIVE_JOBPATH' -> 'DATA_TREE_PATH/VASP_5_4_PBE/AlNi/static__L1_2_NiAl'
        - while 'DATA_TREE_PATH' is configured in .strucscan and 'RELATIVE_JOBPATH' is generated by

        strucscan.datatree.get_relative_jobpath, 'ENGINE_SIGNATURE' needs to be generated by this method
        :param property: (str) name of property
        :param structpath: (str) absolute path to structure file
        :return: (str) absolute path to job directory
        """
        cmd = subprocess.Popen("grep ENCUT {}/{}".format(self.SETTINGS_PATH, self.settings),
                               shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        output, err = cmd.communicate()
        if not err:
            encut = int(output.split()[2])
        else:
            species_split = [s.split("_")[0] for s in self.species.split()]
            enmaxs = []
            for specie in species_split:
                cmd = subprocess.Popen("grep ENMAX {}".format(self.get_potpath(specie, self.potential)),
                                       shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
                output, err = cmd.communicate()
                enmax = int(float(str(output.split()[2])[2:-2]))
                enmaxs.append(enmax)
            encut = max(enmaxs)

        engine_signature = "{}{}{:d}_kdens_0_{:.0f}".format(self.engine_name, SEPERATOR, encut, self.kdens*1e03)
        jobpath = datatree.get_relative_jobpath(self.input_dict["species"], property, jobobject,
                                                structpath=structpath)

        absolute_jobpath = "{}/{}_{}_{}/{}". \
            format(PROJECT_PATH(),
                   engine_signature,
                   self.magconfig.upper(),
                   self.potential,
                   jobpath
                   )

        return absolute_jobpath

    def make_machinefile(self, machine_info, jobname, ntotalcores, property, nsteps):
        """
        - VASP specific method to create and write machine script

        :param machine_info: (dict) machine configuration script taken from 'input_dict'
        :param jobname: (str) name of job, e.g. 'static__fcc__Al'
        :param ntotalcores: (int) number of total cores, that is #cores per node * #of nodes
        :param property: (str) name of property
        :param nsteps: (int) number of single calculation of, e.g. E-V curves, transformation path, ...
        :return: (str list, str) tuple of (list of lines in machine script, machine script file name)
        """
        machine_script, machine_script_fname = self.scheduler.configure_machine_script(machine_info, jobname=jobname)
        if ntotalcores > 1:  # parallel
            config = self.machine_configuration_dict["VASP"]["parallel"]
        else:  # serial
            config = self.machine_configuration_dict["VASP"]["serial"]
        prerequisites = config.split("\n")[:-2]
        call = config.split("\n")[-2]
        call = call.replace("$NTOTALCORES", str(ntotalcores))
        call = call.split(">")[0] + " >& vasp.out"

        machine_script.append("echo \"property: %s\" >> start.dat\n" % property)
        machine_script.append("\n")

        for prerequisite in prerequisites:
            machine_script.append(prerequisite)
        machine_script.append("\n")

        if nsteps > 1:
            for i in range(nsteps):
                machine_script.append("cp POSCAR-%i POSCAR\n" % i)
                machine_script.append(call + "\n")
                machine_script.append("mv CONTCAR CONTCAR-%i\n" % i)
                machine_script.append("mv OUTCAR OUTCAR-%i\n" % i)
                machine_script.append("gzip OUTCAR-%i\n" % i)
                machine_script.append("mv OSZICAR OSZICAR-%i\n" % i)
                machine_script.append("mv vasprun.xml vasprun-%i.xml\n" % i)
                machine_script.append("gzip vasprun-%i.xml\n" %i)
                machine_script.append("\n")
            machine_script.append("rm POSCAR\n")
        else:
            machine_script.append(call + "\n")
            machine_script.append("gzip OUTCAR\n")
            machine_script.append("gzip OSZICAR\n")
            machine_script.append("gzip vasprun.xml\n")

        machine_script.append("rm WAVECAR EIGENVAL CHG DOSCAR IBZKPT REPORT XDATCAR PROCAR PCDAT\n")
        machine_script.append("\n")
        machine_script.append("STOP=`date`\n")
        machine_script.append("echo \"stop: $STOP  $HOSTNAME\" >> end.dat ")
        return machine_script, machine_script_fname

    @staticmethod
    def write_structure(atoms, jobpath, structfilename="POSCAR"):
        """
        - VASP specific method to write engine specific structure file

        :param atoms: (ASE atoms object) atoms object with assigned chemical symbols, magnetic moments
        and scaled positions
        :param jobpath: (str) absolute path to job directory
        :param structfilename: (str) name of structure file that is written to disk. for VASP, structfilename is 'POSCAR'
        :return: 0
        """
        io.write(jobpath + "/" + structfilename, atoms, format="vasp")
        return

    @staticmethod
    def read_final_structure(path, resultfilename="OUTCAR.gz"):
        """
        - VASP specific method to read final structure file

        :param path: (str) absolute path to result directory
        :param resultfilename: (str) name of final structure file. for VASP, structfilename is 'OUTCAR.gz'
        :return: (ASE atoms object) final atoms object
        """
        fname = path
        if resultfilename not in fname:
            fname += "/" + resultfilename
        try:
            final_struct = io.read(fname, format="vasp-out")
            return final_struct
        except Exception:
            raise FileNotFoundError("{} not found.".format(fname))

    def check_if_finished(self, files):
        """
        - VASP specific method to check if the calculation in job directory with files with files is finished

        :param files: (str list) str list of all files in directory
        :return: (bool)
        """
        result_filename = self.resultfilename
        for file in files:
            if ("OUTCAR" in file) and (".gz" in file):
                result_filename = file
        cmd = subprocess.Popen("zgrep \"Total CPU time used (sec):\" %s" % result_filename, shell=True,
                               stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        output, err = cmd.communicate()
        if str(err) != "":
            if str(output)[2:-1] != "":
                return True
        return
