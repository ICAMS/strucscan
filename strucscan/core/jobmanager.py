from datetime import datetime
from random import shuffle
import json
import copy
import time
import sys

from ase.io.jsonio import encode, decode

from strucscan.core import statusmanager, collector
from strucscan.core.jobmaker import JobMaker
from strucscan.utils import *
from strucscan.resources.inputyaml import *
from strucscan.resources.properties import *


class JobManager:
    def __init__(self, input_dict):
        """
        - when strucscan is called, it creates the JobManager object first
        - the JobManager object creates the JobMaker and communicates with it
        - a typical workflow looks like in the following:
        1. the JobManager checks the user given input (this happens in __init__)
        2. the JobManager calls the JobMaker to initialize the a list of all jobs, the 'job_list'
        3. every 45 sec (set in ~/.strucscan), the JobManager asks the JobMaker for a status update of all jobs in 'job_list'
        4. depending on the status, the JobMaker reacts
        5. if alls jobs are finished, the JobManager ends the process

        :param input_dict: (dict) input dictionary. Please follow to the examples in strucscan.resources.inputyaml
        """
        self.input_dict = input_dict
        if "queuename" not in self.input_dict:
            # if the host has no queuing system, and the user might have entered no value for the queuename
            # because it is not neccessary by principle
            # set queuename to some value so strucscan does not crash.
            self.input_dict["queuename"] = "(none)"

        self.user_input_dict = copy.deepcopy(self.input_dict)
        self.engine_name = self.input_dict["engine"].split()[0].upper()
        self.jobwatch_filename = "jobwatch" + SEPERATOR + datetime.now().strftime("%m-%d-%Y_%H-%M") + ".dat"
        self.jobwatch = {}
        self.cl_out = {}
        self.cl_out_lines = {}
        self.DATA_TREE_PATH = PROJECT_PATH()
        for string1, string2 in [("Data tree path:", self.DATA_TREE_PATH),
                                 ("Structure repository:", STRUCTURES_PATH()),
                                 ("Resource repository:", RESOURCE_PATH())]:
            print("{:30} {}".format(string1, string2))
        print("")

        # check mandatory keys
        for key in MANDATORY[self.engine_name]:
            if key not in self.input_dict:
                print("Necessary key '{}' not provided".format(key))
                print("Exiting.")
                sys.exit(0)
            elif self.input_dict[key] is None:
                print("No value provided for necessary key '{}'.".format(key))
                print("Exiting.")
                sys.exit(0)

        # check optional keys
        for key in OPTIONAL[self.engine_name]:
            if (key not in self.input_dict) or (self.input_dict[key] is None):
                self.input_dict[key] = OPTIONAL[self.engine_name][key]
                out = OPTIONAL[self.engine_name][key]
                if out == "":
                    out = "(None)"
                print("Optional key '{}' not provided. Default value will be used: {}".format(key, out))

        for key in self.input_dict:
            # cast all non-bool values to str
            if not isinstance(self.input_dict[key], bool):
                self.input_dict[key] = str(self.input_dict[key])

        if DEBUG():
            self.input_dict["verbose"] = True
        self.VERBOSE = self.input_dict["verbose"]

        self.job_list = []
        self.calc = get_calc(self.engine_name, self.input_dict)
        self.calc.set_scheduler()
        self.jobmaker = JobMaker(self.job_list, self.calc, self.input_dict)

        if self.input_dict["monitor"]:
            self.input_dict["submit"] = True
            self.jobmaker.input_dict["submit"] = True

        if (self.input_dict["properties"] is None) or (self.input_dict["prototypes"] is None):
            # if no properties or prototypes have been provided, strucscan will only collect from datatree
            self.assembled_properties = []
            self.prototypes = []
        else:
            self.prototypes = self.input_dict["prototypes"].split()
            self.properties = self.input_dict["properties"].split()
            self.assembled_properties = []

            # check for known and unkown ready-assembled properties
            unkown = []
            delete = []
            for ind, property in enumerate(self.properties):
                if "_" in property:
                    if property not in ALL_PROPERTIES:
                        unkown.append(property)
                    else:
                        self.assembled_properties.append(property)
                    delete.append(ind)

            # remove unkown and ready-assembled properties
            tmp_properties = [prop for ind, prop in enumerate(self.properties) if ind not in delete]
            properties = tmp_properties

            first_property = properties[0]
            if first_property in ADVANCED_TASKS:
                property = first_property + "_" + DEFAULT_OPTION
                self.assembled_properties.append(property)
            else:
                self.assembled_properties.append(first_property)

            if len(properties) > 1:
                for next_property in properties[1:]:
                    if first_property in ADVANCED_TASKS:
                        first_property = DEFAULT_OPTION
                    if next_property in ADVANCED_TASKS:
                        if first_property not in OPTIMIZATIONS:
                            first_property = DEFAULT_OPTION
                        next_property = "{}_{}".format(next_property, first_property)
                    first_property = next_property
                    self.assembled_properties.append(next_property)

            # remove any wrong assembled property
            delete = []
            for ind, property in enumerate(self.assembled_properties):
                if property not in ALL_PROPERTIES:
                    delete.append(ind)
            tmp_properties = [prop for ind, prop in enumerate(self.assembled_properties) if ind not in delete]
            self.assembled_properties = tmp_properties
        self.input_dict["properties"] = " ".join([prop for prop in self.assembled_properties])

        # collect all structure paths
        self.structpaths = []
        for prototype in self.prototypes:
            if prototype[0] == "<":
                for root1, dirs1, files1 in os.walk(STRUCTURES_PATH):
                    for file1 in files1:
                        if prototype[1:-1] in root1:
                            node = root1
                            for root2, dirs2, files2 in os.walk(node):
                                for file2 in files2:
                                    if file2.split(".")[-1] == STRUCT_FILE_FORMAT():
                                        self.structpaths.append(root2 + "/" + file2)
                            break
            else:
                self.structpaths.append(get_structpath(prototype))

        if self.VERBOSE:
            print("\n")
            print("{:30} : {:50} {:50}".format("key:", "your input", "what strucscan reads"))
            print("-"*100)
            for key in self.input_dict:
                value = str(self.input_dict[key])
                user_value = "(not set)"
                if key in self.user_input_dict:
                    user_value = str(self.user_input_dict[key])
                if user_value == "":
                    user_value = "(not set)"
                if value == "":
                    value = "(not set)"
                print("{:<30} : {:<50} {:<50}".format(key, user_value, value))
            print("")

        self.initialize_job_list()
#        self.update_job_list()

        if self.VERBOSE:
            print("")
            print(len(self.job_list), "jobs in JobList:")
            print("-"*114)
            print("{:>3}: {:60}  {:60}".format("#", "jobpath", "prototype path"))
            print("-"*114)
            for i, jobobject in enumerate(self.job_list):
                print("{:>3}: {:60}  {:60}". \
                      format(str(i),
                             "/".join([s for s in jobobject.get_jobpath().split("/")[len(PROJECT_PATH().split("/")):]]),
                             "/".join([s for s in jobobject.structpath.split("/")[len(STRUCTURES_PATH().split("/")):]])
                             )
                      )
            print("")
            if DEBUG():
                print("{:>3}: {:60}  {:8}  {:8}".format("#", "jobpath", "JobID", "Status"))
                print("-" * 114)
                for i, jobobject in enumerate(self.job_list):
                    path = "/".join([s for s in jobobject.get_jobpath().split("/")[len(
                        PROJECT_PATH().split("/")):]])
                    print("{i:>3}: {path:60}  {job_id:8}  {status:8}". \
                          format(i=str(i),
                                 path=path,
                                 job_id=str(jobobject.get_job_id()),
                                 status=jobobject.get_status()
                                 )
                          )
                print("")
            else:
                if self.command_line_output():
                    print(
                        "{:>3}: {:60} {:8} {:8} {:20} {:20}".format("#", "jobpath", "id", "status", "start",
                                                                     "end"))
                    print("-" * 114)
                    for job, line in self.cl_out_lines.items():
                        print(line)
                    print("")

        if (self.job_list != []) and self.input_dict["monitor"]:
            if self.VERBOSE:
                print("")
                print(">> Entering loop:")
            finished = False
            while not finished:
                self.update_job_list()
                if np.array([jobobject.get_status_index() for jobobject in self.job_list]).all() == 1:
                    finished = True
                if self.VERBOSE:
                    if DEBUG():
                        print("{:>3}: {:60}  {:8}  {:8}".format("#", "jobpath", "JobID", "Status"))
                        print("-"*114)
                        for i, jobobject in enumerate(self.job_list):
                            path = "/".join([s for s in jobobject.get_jobpath().split("/")[len(
                                PROJECT_PATH().split("/")):]])
                            print("{i:>3}: {path:60}  {job_id:8}  {status:8}". \
                                    format(i=str(i),
                                           path=path,
                                           job_id=str(jobobject.get_job_id()),
                                           status=jobobject.get_status()
                                           )
                                  )
                        print("")
                    else:
                        if self.command_line_output():
                            print("{:>3}: {:60} {:8} {:8} {:20} {:20}".format("#", "jobpath", "id", "status", "start", "end"))
                            print("-"*114)
                            for job, line in self.cl_out_lines.items():
                                print(line + "\n")
                if self.input_dict["collect"]:
                    self.collect()
                time.sleep(SLEEP_TIME())
        if self.input_dict["collect"]:
            self.collect()
        if self.VERBOSE:
            print("Finished.")

        return

    def initialize_job_list(self):
        """
        - calls JobMaker to initialize the job_list

        :return: 0
        """
        if self.VERBOSE:
            print(">> Initializing:")
        if (self.structpaths != []):
            for structpath in self.structpaths:
                for jobobject in self.jobmaker.initialize_jobs(structpath, self.assembled_properties):
                    if self.VERBOSE:
                        print("Initialized ", jobobject.species, jobobject.property)
                    self.job_list.append(jobobject)

        dubplicates = set()
        unique_jobobject = [jobobject for jobobject in self.job_list
               if jobobject.get_jobpath() not in dubplicates and not dubplicates.add(jobobject.get_jobpath())]
        self.job_list = unique_jobobject
        shuffle(self.job_list)
        return

    def update_job_list(self):
        """
        - calls JobMaker to update job_list

        :return: 0
        """
        for i, jobobject in enumerate(self.job_list):
            if DEBUG():
                print("")
                print("jobmanager update, i:", i)
                print("jobobject jobpath:", jobobject.jobpath)
                print("jobobject structpath:", jobobject.structpath)
                print("jobobject basis_ref_atoms:", jobobject.basis_ref_atoms)
                print("jobobject conditonal files:", jobobject.conditional_files)
            jobobject = self.jobmaker.update(jobobject)
            self.job_list[i] = jobobject
        return

    def command_line_output(self):
        update = False
        for ind, jobobject in enumerate(self.job_list):
            jobpath = "/".join([s for s in jobobject.get_jobpath().split("/")[len(PROJECT_PATH().split("/")):]])
            status_index, status, job_id = jobobject.get_status_index_job_id()
            if jobpath not in self.cl_out:
                self.cl_out[jobpath] = {"start": "", "end": ""}
                self.cl_out_lines[jobpath] = ""
            if (status == "running") and (self.cl_out[jobpath]["start"] == ""):
                self.cl_out[jobpath]["start"] = datetime.now().strftime("%m/%d/%Y %H:%M")
            if (status_index == 1) and (self.cl_out[jobpath]["end"] == ""):
                self.cl_out[jobpath]["end"] = datetime.now().strftime("%m/%d/%Y %H:%M")
            line = "{:>3d} {:60} {:8} {:8} {:20} {:20}".format(ind, jobpath, str(job_id), status, self.cl_out[jobpath]["start"], self.cl_out[jobpath]["end"])
            if line == self.cl_out_lines[jobpath]:
                pass
            else:
                self.cl_out_lines[jobpath] = line
                update = True
        return update

    def collect(self):
        """
        - navigates through the whole data tree from top to bottom
        - collects data from each directory in data tree
        - collects data from a directory only if the data not already have been stored in the output dict written to disk

        :return: 0
        """
        if os.path.exists(self.DATA_TREE_PATH):
            for calculator in os.listdir(self.DATA_TREE_PATH):
                _calc = self.calc
                if self.calc.get_name().upper() in calculator:
                    pass
                else:
                    # if data created by an engine different from self.calc is checked:
                    # create engine object and set current scheduler to it
                    # so statusmanager can determine job status
                    engine_name = calculator.split("_")[0].upper()
                    try:
                        _calc = get_calc(engine_name, self.input_dict)
                    except KeyError:
                        _calc = None
                if _calc is not None:
                    if _calc.get_scheduler() is None:
                        try:
                            _calc.set_schedular()
                        except AttributeError:
                            pass
                    if _calc.get_scheduler() is not None:
                        if os.path.isdir(self.DATA_TREE_PATH + "/" + calculator):
                            for composition in [dir for dir in os.listdir(self.DATA_TREE_PATH + "/" + calculator)]:
                                if os.path.isdir(self.DATA_TREE_PATH + "/" + calculator + "/" + composition):

                                    fname = "{DATA_TREE_PATH}/{calculator}/{calculator}{SEPERATOR}{composition}{SEPERATOR}output_dict.yaml". \
                                        format(DATA_TREE_PATH=self.DATA_TREE_PATH,
                                               calculator=calculator,
                                               SEPERATOR=SEPERATOR,
                                               composition=composition)
                                    output_dict = {}
                                    try:
                                        with open(fname) as stream:
                                            output_dict = json.load(stream)
                                            stream.close()
                                        names = list(output_dict.keys())
                                    except FileNotFoundError:
                                        names = []
                                    composition_path = "{}/{}/{}".format(self.DATA_TREE_PATH, calculator, composition)
                                    for property_prototype_stochio in [dir for dir in os.listdir(composition_path) if os.path.isdir(composition_path + "/" + dir)]:
                                        path = "{DATA_TREE_PATH}/{calculator}/{composition}/{property_prototype_stochio}". \
                                        format(DATA_TREE_PATH=self.DATA_TREE_PATH,
                                               calculator=calculator,
                                               composition=composition,
                                               property_prototype_stochio=property_prototype_stochio)

                                        property = property_prototype_stochio.split(SEPERATOR)[0]
                                        jobname = collector.get_jobname(path)
                                        if jobname in names:
                                            pass
                                        else:
                                            _, status, job_id = statusmanager.determine_status__job_id(_calc, path, self.job_list)
                                            if status == statusmanager.FINISHED:
                                                if DEBUG():
                                                    collecting_directory = "/".join([s for s in path.split("/")[len(self.DATA_TREE_PATH.split("/")):]])
                                                    print(">> collecting", collecting_directory, "...")
                                                result_dict = collector.get_result_dict(_calc, property, path)
                                                if result_dict != {}:
                                                    output_dict[jobname] = result_dict
                                    json_dumps = encode(output_dict)
                                    with open(fname, "w") as f:
                                        f.write(json_dumps)
        if self.VERBOSE:
            print("")
        return
