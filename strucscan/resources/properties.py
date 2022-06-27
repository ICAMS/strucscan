from strucscan.utils import get_resource_file_path

import yaml


OPTIMIZATIONS = ["static", "atomic", "total"]
STATIC_PROPERTIES = ["static"]
ATOMIC_PROPERTIES = ["atomic"]
TOTAL_PROPERTIES = ["total"]


def assemble_properties(name, options):
    properties = []
    try:
        for option in options:
            properties.append(name + "_" + option)
    except TypeError:
        properties.append(name)
    return properties


with open(get_resource_file_path() + "/properties.yaml", "r") as stream:
    properties_conifg_dict = yaml.safe_load(stream)


try:
    DEFAULT_OPTION = properties_conifg_dict["default_option"]
except KeyError:
    DEFAULT_OPTION = "atomic"


ADVANCED_TASKS = properties_conifg_dict.keys()
ADVANCED_PROPERTIES = []
for name, options in properties_conifg_dict.items():
    if options is not None:
        if options in ADVANCED_TASKS:
            options = [opt.strip(", ") for opt in properties_conifg_dict[options].split()]
        else:
            options = [opt.strip(", ") for opt in options.split()]
    for property in assemble_properties(name, options):
        ADVANCED_PROPERTIES.append(property)
STATIC_PROPERTIES += ADVANCED_PROPERTIES

ALL_PROPERTIES = STATIC_PROPERTIES + ATOMIC_PROPERTIES + TOTAL_PROPERTIES