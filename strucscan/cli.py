from strucscan.core.jobmanager import JobManager

import sys
import yaml


def main():
    cmdarg = sys.argv[:]
    if len(cmdarg) == 1:
        print("Please specify an input file: strucscan <input.yml>")
        sys.exit(0)
    else:
        inputfile = cmdarg[1]
        input_dict = read_input(inputfile)
        JobManager(input_dict)


def read_input(inputfile):
    def str_presenter(dumper, data):
         if len(data.splitlines()) > 1:  # check for multiline string
             return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
         return dumper.represent_scalar('tag:yaml.org,2002:str', data)
    yaml.add_representer(str, str_presenter)
    with open(inputfile, "r") as stream:
        input_dict = yaml.safe_load(stream)
    return input_dict
