from strucscan.core.jobmanager import JobManager

import sys
import yaml


def main():
    cmdarg = sys.argv[:]
    if len(cmdarg) == 1:
        print("Please specify an input file: strucscan [input.yaml]")
        print("For help, type strucscan --help")
        sys.exit(0)
    else:
        arg = cmdarg[1]
        if arg == "--help":
            print("strucscan: A Lightweight Python-based framework for high-throughput material simulation")
            print("by ICAMS, Ruhr University Bochum")
            print("")
            print("Usage:")
            print("strucscan [input.yaml]")
            print("")
            print("Please specify the path to your input file.")
            print("Input file needs to be in yaml format.")
            print("For examples, see https://github.com/ICAMS/strucscan/tree/main/examples")
            print("A template input file can be seen in examples/dummy.yaml")
            print("")
            print("If you have an idea for a new feature, a question or found a bug,")
            print("you can submit it through the issue page of the repository:")
            print("https://github.com/ICAMS/strucscan/issues")
        else:
            input_dict = read_input(arg)
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
