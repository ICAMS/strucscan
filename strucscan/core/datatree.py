from strucscan.utils import *
from strucscan.resources.properties import *


def get_relative_jobpath(species, property, jobobject, structpath=None):
    """
    - generates directory layers below 'engine signature': DATA_TREE_PATH/ENGINE_SIGNATURE/RELATIVE_JOBPATH
    - example: DATA_TREE_PATH/ENGINE_SIGNATURE/AlNi/atomic__fcc__Ni'

    :param species: (str) space separated species, e.g. 'Al Ni'
    :param property: (str) name of property
    :param structpath: (str) absolute path to structure file
    :return: (str) relative jobpath, that is the path below engine_name layer, e.g. 'Al/static__fcc__Al'
    """
    composition = "".join([elm for elm in sorted(species.split())])
    stochio = jobobject.get_stochio()
    prototype = ""
    if structpath is not None:
        prototype = structpath.split("/")[-1].split(".")[0]
    else:
        prototype = SEPERATOR.join([s for s in jobobject.jobpath.split(SEPERATOR)[1:-1]])
    jobpath = "{composition}/{property}{SEPERATOR}{prototype}{SEPERATOR}{stochio}". \
        format(composition=composition,
               property=property,
               SEPERATOR=SEPERATOR,
               prototype=prototype,
               stochio=stochio
               )

    return jobpath


def parse_absolute_path(absolute_path):
    """
    :param absolute_path: (str) absolute path to job directory
    :return: (str tuple) separated path to job directory
    """
    splitted_path = absolute_path.split("/")[len(PROJECT_PATH().split("/")):]
    calculator_and_settings = splitted_path[0]
    composition = splitted_path[1]
    property_prototype_stochio = splitted_path[2].split(SEPERATOR)
    property = property_prototype_stochio[0]
    prototype = "_".join([p for p in property_prototype_stochio[1:-1]])
    stochio = property_prototype_stochio[-1].split(".")[0]

    return calculator_and_settings, composition, property, prototype, stochio


def get_basis_ref_structpath_and_conditional_jobpath(calc, jobpath):
    """
    :param jobpath: (str) absolute path to job directory
    :return: (str, str) absolute path to final basis_ref structure file, absolute directory path to conditional files
    """
    property = jobpath.split("/")[-1].split(SEPERATOR)[0]
    property_split = property.split("_")
    option = property_split[-1]
    split = jobpath.split("/")
    structname = "_".join([s for s in split[-1].split(SEPERATOR)[1:-1] if s != ""])
    stochio = split[-1].split(SEPERATOR)[-1]
    path = "/".join([s for s in split[:-1]])
    dirname = "{option}{seperator}{structname}{seperator}{stochio}".format(
        option=option,
        seperator=SEPERATOR,
        structname=structname,
        stochio=stochio
    )
    basis_ref_structpath = path + "/" + dirname + "/" + calc.final_struct_fname

    if len(property_split) > 1:
        if properties_conifg_dict[property_split[0]] in ADVANCED_TASKS:
            task = properties_conifg_dict[property_split[0]]
            if task != option:
                dirname = task + "_" + dirname
    conditional_files = path + "/" + dirname
    return basis_ref_structpath, conditional_files
