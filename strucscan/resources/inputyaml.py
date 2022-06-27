from copy import deepcopy

class GENERAL:
    def __init__(self):
        self.MANDATORY = {'species': "str",
                          'engine': "str",
                          'machine': "str",
                          'ncores': "str",
                          'nnodes': "str",
                          'queuename': "str",
                          'potential': "str",
                          'properties': "str",
                          'prototypes': "str",
                          'settings': "str"
                          }

        self.OPTIONAL = {'initial atvolume': "default",
                        "verbose": False,
                        "monitor": True,
                        "submit": True,
                        "collect": True
                        }

        self.ALL = deepcopy(self.MANDATORY)
        self.ALL = self.ALL.update(self.OPTIONAL)


class DUMMY(GENERAL):
    def __init__(self):
        GENERAL.__init__(self)

        self.EXAMPLE = {'species': "Al",
                         'engine': "dummy",
                         'machine': "dummy",
                         'initial atvolume': "default",
                         'ncores': "1",
                         'nnodes': "1",
                         'queuename': "none",
                         'properties': "static atomic total eos",
                         'prototypes': "fcc.cfg",
                         'potential': "none",
                         'settings':  'none',
                         }


class VASP(GENERAL):
    def __init__(self):
        GENERAL.__init__(self)
        self.MANDATORY.update({'magnetic configuration': "str"})
        self.MANDATORY.update({'initial magnetic moments': "str"})

        self.OPTIONAL.update({'kdens': 0.15})
        self.OPTIONAL.update({'kmesh': "Monkhorst-pack"})
        self.OPTIONAL.update({'k points file': ""})

        self.EXAMPLE = {'species': "Ni Al_pv",
                        'engine': "VASP 5.4",
                        'machine': "example_vasp",
                        'ncores': "1",
                        'nnodes': "1",
                        'queuename': "none",
                        'potential': "PBE",
                        'properties': "atomic",
                        'prototypes': "L1_2",
                        'settings': "500_SP.incar",
                        'magnetic configuration': "SP",
                        'initial magnetic moments': "2.0 0.",
                        'kdens': "0.15",
                        'kmesh': "Monkhorst-pack",
                        'initial atvolume': "default",
                        "verbose": False,
                        "monitor": True,
                        "submit": True,
                        "collect": False
                        }



MANDATORY = {"DUMMY": DUMMY().MANDATORY,
             "VASP": VASP().MANDATORY
             }

OPTIONAL = {"DUMMY": DUMMY().OPTIONAL,
            "VASP": VASP().OPTIONAL
            }
