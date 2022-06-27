import json
import yaml
import numpy as np
import collections
import re
import os

from ase import Atoms
from ase import io

from strucscan.resources import atomicdata


SEPERATOR = "__"
eV_A2_to_mJ_m2 = 1.60218e-19 * 1e20 * 1e3
alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            flatobj = obj.ravel()
            if np.iscomplexobj(obj):
                flatobj.dtype = obj.real.dtype
            return flatobj.tolist()
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.float):
            return float(obj)
        return json.JSONEncoder.default(self, obj)


def get_resource_file_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources")


def read_configuration():
    """
    :return: (dict) configuration stored in .strucscan
    """
    HOME_DIR = os.path.expanduser("~")

    # define default
    config = {"PROJECT_PATH": "tests/data",
              "RESOURCE_PATH": "resources",
              "STRUCTURES_PATH": "structures"}

    try:
        with open(HOME_DIR + "/.strucscan", "r") as stream:
            config = yaml.safe_load(stream)
    except FileNotFoundError:
        pass
    return config


def PROJECT_PATH():
    return read_configuration()["PROJECT_PATH"]


def RESOURCE_PATH():
    return read_configuration()["RESOURCE_PATH"]


def STRUCTURES_PATH():
    return read_configuration()["STRUCTURES_PATH"]


def DEBUG():
    try:
        if read_configuration()["DEBUG"].lower() == "true":
            return True
    except:
        return False


def STRUCT_FILE_FORMAT():
    try:
        return read_configuration()["STRUCT_FILE_FORMAT"]
    except:
        return "cfg"


def SLEEP_TIME():
    try:
        return read_configuration()["SLEEP_TIME"]
    except:
        return 60


def get_calc(engine_name, input_dict):
    """
    - assigns 'engine_name' to strucscan.core.engine.GeneralEngine object
    - creates strucscan.core.engine.GeneralEngine object
    :param engine_name: (str) name of engine
    :param input_dict: (dict) input dict provided by user
    :return: (strucscan.core.engine.GeneralEngine object)
    """
    calc = None
    if "DUMMY" in engine_name:
        from strucscan.engine.dummy import DummyEngine
        calc = DummyEngine(input_dict)
    elif "VASP" in engine_name:
        from strucscan.engine.vasp import Vasp
        calc = Vasp(input_dict)
    elif "BOPFOX" in engine_name:
        try:
            from strucscan.engine.bopfox import BOPfox
            calc = BOPfox(input_dict)
        except ImportError:
            raise("Could not import bopfox from ase.io. BOPfox calculations are not possible. Exiting.")
    elif "LAMMPS" in engine_name:
        raise("LAMMPS not implemented yet. Exiting.")
    elif "ACE" in engine_name:
        raise("ACE not implemented yet. Exiting.")
    return calc


def get_structpath(prototype_name):
    """
    :param prototype_name: (str) structure file name or absolute path of structure file
    :return: (str) absolute path of structure file
    """
    structpath = ""
    for root, dirs, files in os.walk(STRUCTURES_PATH()):
        for file in files:
            if file == prototype_name:
                structpath = root + "/" + prototype_name
    if structpath == "":
        print("FileNotFound: Could not find {}".format(prototype_name))
    else:
        return structpath


def parse_prototypefile(structpath):
    """
    :param structpath: (str) absolute path to structure file in prototype cfg format (contains 'eleA, eleB', ...)
    :return: tuple of structure cell (3x3 list) and position dictionary
    in form {elmA: list(atomA1, atomA2, ...),  elmB: list(atomB1, atomB2, ...)}
    """
    with open(structpath, "r") as f:
        lines = f.readlines()
    positions_dict = {}
    cell = [[None, None, None], [None, None, None], [None, None, None]]
    for ind, line in enumerate(lines):
        if line[0] == "#":
            pass
        if "Number of particles" in line:
            n_at = int(line.split("=")[-1].strip("\\n"))
        if "H0" in line:
            split = line.split("HO(")[-1].split()[0].strip("H0())")
            dimension, entry = [int(s) - 1 for s in split.split(",")]
            cell[dimension][entry] = float(line.split("=")[-1].split()[0])
        if "ele" in line.lower()[:3]:
            elm = line.lower()[3].upper()
            if elm not in positions_dict:
                positions_dict[elm] = []
            positions_dict[elm].append([float(coord) for coord in lines[ind + 1].split()])
    if positions_dict == {}:
        raise ValueError("Could not parse structure from file. File not in cfg format?")
    return cell, positions_dict


def get_element_order_from_atoms(atoms):
    """
    - assigns letters to chemical symbols alphabteically according to their occurance
      in list of chemical symbols
    - if for example, the list of chemical smybols looks like  ['Ni', 'Ni', 'Al', 'Cr', ...],
      then get_element_order_from_atoms returns {'A': 'Ni', 'B': 'Al', 'C': 'Cr', ...}
      because 'Ni' comes first, 'Al' comes second, 'Cr' comes third, ... .
    :param atoms: (ASE atoms object)
    :return: (dict) of kind {'A': 'Ni', 'B': 'Al', 'C': 'Cr', ...}
    """
    elements = []
    for atom in atoms:
        if atom.symbol not in elements:
            elements.append(atom.symbol)

    element_order = {}
    for ind, element in enumerate(elements):
        element_order[alphabet[ind]] = element
    return element_order


def get_element_positions_from_atoms(atoms):
    """
    :param atoms: (ASE atoms object)
    :return positions_dict: (dict) dictionary of atomic positions,
    e.g. {'Ni' [pos1, pos2, ...], 'Al': [pos1, pos2, ...], 'Cr': [...], ...}
    """
    element_positions = {}
    for atom in atoms:
        if atom.symbol not in element_positions:
            element_positions[atom.symbol] = []
        element_positions[atom.symbol].append(atom.position)
    return element_positions


def get_positions_dict_from_structure_file(structpath, _format):
    """
    :param structpath: (str) absolute path of structure file
    :param _format: (str) ase.io file format or 'prototype' format
    :return positions_dict: (dict) abstract dictionary of atomic positions,
    e.g. {'A' [pos1, pos2, ...], 'B': [pos1, pos2, ...], 'C': [...], ...}
    where 'A' is assigned to the chemical symbol
    that comes first in the list of chemcial symbols of the atoms object.
    If the chemical symbols list is ['Ni', 'Ni', 'Al', 'Cr', ...],
    then 'Ni' is element A, 'Al' is element 'B', 'Cr' is element 'B'.
    """
    if _format == "prototype":
        cell, positions_dict = parse_prototypefile(structpath)
    else:
        atoms = io.read(structpath, format=_format)
        positions_dict = get_positions_dict_from_atoms(atoms)
    return positions_dict


def get_positions_dict_from_atoms(atoms):
    """
    :param atoms: (ASE atoms object)
    :return positions_dict: (dict) abstract dictionary of atomic positions,
    e.g. {'A' [pos1, pos2, ...], 'B': [pos1, pos2, ...], 'C': [...], ...}
    where 'A' is assigned to the chemical symbol
    that comes first in the list of chemcial symbols of the atoms object.
    If the chemical symbols list is ['Ni', 'Ni', 'Al', 'Cr', ...],
    then 'Ni' is element A, 'Al' is element 'B', 'Cr' is element 'B'.
    """
    element_order = get_element_order_from_atoms(atoms)
    element_positions = get_element_positions_from_atoms(atoms)

    positions_dict = {}
    for key1 in element_order:
        for key2 in element_positions:
            if element_order[key1] == key2:
                positions_dict[key1] = element_positions[key2]
    return positions_dict


def get_new_chemical_formula_from_atoms(atoms, species):
    """
    - wrapper around strucscan.utils.get_new_chemical_formula
    :param atoms: (ASE atoms object)
    :param species: (str) chemical species, e.g. 'Ni Al'
    :return: (str) chemical formula
    """
    positions_dict = get_positions_dict_from_atoms(atoms)
    formula = get_new_chemical_formula(positions_dict, species)
    return formula


def get_new_chemical_formula_from_stucture_file(structpath, species, _format):
    """
    - wrapper around strucscan.utils.get_new_chemical_formula
    :param structpath: (str) absolute path of structure file
    :param species: (str) chemical species, e.g. 'Ni Al'
    :param _format: (str) ase.io file format or 'prototype' format
    :return: (str) chemical formula
    """
    if _format == "prototype":
        _, positions_dict = parse_prototypefile(structpath)
    else:
        positions_dict = get_positions_dict_from_structure_file(structpath, _format)
    formula = get_new_chemical_formula(positions_dict, species)
    return formula


def get_new_chemical_formula(positions_dict, species):
    """
    - wrapper around strucscan.utils.get_new_chemical_formula
    :param positions_dict: (dict) abstract dictionary of atomic positions,
    e.g. {'A' [pos1, pos2, ...], 'B': [pos1, pos2, ...], 'C': [...], ...}
    where 'A' is assigned to the chemical symbol
    that comes first in the list of chemcial symbols of the atoms object.
    If the chemical symbols list is ['Ni', 'Ni', 'Al', 'Cr', ...],
    then 'Ni' is element A, 'Al' is element 'B', 'Cr' is element 'B'.
    :param species: (str) chemical species, e.g. 'Ni Al'
    :return: (str) chemical formula
    """
    nspecies = [len(positions_dict[elm]) for elm in positions_dict]
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    formula = ""
    element_labels_order = {}
    species_split = [specie.split("_")[0] for specie in species.split()]
    if ":" in species:
        for specie in species_split:
            split = specie.split(":")
            label = split[0][-1]
            element_labels_order[label] = split[-1]
    else:
        for ind, specie in enumerate(species.split()):
            label = alphabet[ind]
            element_labels_order[label] = specie.split("_")[0]
    element_labels_order = collections.OrderedDict(sorted(element_labels_order.items()))

    element_labels = [element_labels_order[key] for key in element_labels_order]
    if len(element_labels) < len(list(positions_dict.keys())):
        # use last specie for all further atomic sites
        last_specie = element_labels_order[list(element_labels_order.keys())[-1]]
        for key in list(positions_dict.keys())[len(element_labels):]:
            element_labels_order[key] = last_specie
        element_labels = [element_labels_order[key] for key in element_labels_order]
        formula = "".join(elmn for elmn in [elm + str(n) for elm, n in zip(element_labels, nspecies)])
    elif len(element_labels) >= len(list(positions_dict.keys())):
        # strip surplus species
        formula = "".join([elmn for elmn in [elm + str(n) for elm, n in zip(element_labels[:len(nspecies)], nspecies)]])
    return formula


def read_structure_from_file(structpath, species, _format):
    """
    :param structpath: (str) absolute path to structure file
    :param species: (str) chemical species, e.g. 'Ni Al'
    :param _format: (str) ase.io file format or 'prototype' format
    :return: (ASE atoms object) atoms object with decorated chemical symbols
    """
    atoms = None
    if _format == "prototype":
        cell, positions_dict = parse_prototypefile(structpath)
        positions = [p for elm in positions_dict for p in positions_dict[elm]]
        formula = get_new_chemical_formula_from_stucture_file(structpath, species, _format)
        atoms = Atoms(formula, positions=positions, cell=cell)
    else:
        atoms = io.read(structpath, format=_format)
        formula = get_new_chemical_formula_from_stucture_file(structpath, species, _format)
        numbers = re.findall(r'\d+', formula)
        symbols = [s for s in re.split(r'(\d+)', formula) if not s.isdigit()]
        new_chemical_symbols = [symbol for number, symbol in zip(numbers, symbols) for n in range(int(number))]
        atoms.set_chemical_symbols(new_chemical_symbols)
    if atoms is not None:
        return atoms
    else:
        raise TypeError("Could not read structure from {} in format {}".format(structpath, _format))


def get_symbol_dict(atoms):
    """
    :param atoms: (ASE atoms object)
    :return: (dict) dictionary in form of {'chemical symbol': n_at} where n_at is the number of atoms with chemical symbol
    """
    symbols = {}
    for atom in atoms:
        if atom.symbol not in symbols:
            symbols[atom.symbol] = 0
        symbols[atom.symbol] += 1
    return symbols


def get_nspecies(atoms):
    """
    :param atoms: (ASE atoms object)
    :return: (int list) list of number of species in atoms object
    """
    symbols = get_symbol_dict(atoms)
    nspecies = np.array([symbols[symbol] for symbol in symbols])
    return nspecies


def get_initial_atvolume(atoms, initial_atvolumes):
    """
    :param atoms: (ASE atoms object)
    :param initial_atvolumes: (str) initial atomic volume per specie given by user, e.g. "11.2 13.4".
    Type "default" or "d" in order to user defailt atomic volumes.
    :return: (float) initial atomic volume determined by sum([n_i * V_i])
    where n_i is the number of atoms of specie i and V_i is the initial atomic volume for specie i
    """
    init_atvolume = 0
    nspecies = get_nspecies(atoms) / len(atoms)
    if (str(initial_atvolumes).split()[0].lower() == "off") or (str(initial_atvolumes).split()[0].lower() == "false"):
        # do not scale structures
        return False
    elif isinstance(initial_atvolumes, str):
        if initial_atvolumes.split()[0][0].lower() == "d":
            symbols = get_symbol_dict(atoms)
            initial_atvolumes = []
            for symbol in symbols:
                initial_atvolumes.append(atomicdata.atomic_volumes[symbol])
        elif initial_atvolumes.split()[0][0].isdigit(): # corresponds to input "1.0"
            initial_atvolumes = [float(i) for i in initial_atvolumes.split()]
        elif initial_atvolumes.split()[0][0] == ".": # corresponds to input ".1"
            initial_atvolumes = [float(i) for i in initial_atvolumes.split()]

    elif isinstance(initial_atvolumes, float):
        initial_atvolumes = [initial_atvolumes]

    for n, init_atv in zip(nspecies, initial_atvolumes):
        init_atvolume += n*init_atv
    if init_atvolume == 0.:
        raise ValueError("Invalid initial atomic volume 0 .")
    else:
        return init_atvolume


def scale_by_atvolume(atoms, initial_atvolumes, structpath=""):
    """
    :param atoms: (ASE atoms object)
    :param structpath: (str) absolute path of structure file
    :param initial_atvolumes: (str) initial atomic volume per specie given by user, e.g. "11.2 13.4".
    Type "default" or "d" in order to user defailt atomic volumes.
    :return: (ASE atoms object) position scaled atoms object
    """
    cell = atoms.get_cell()
    n_at = len(atoms)
    _initial_atvolumes = get_initial_atvolume(atoms, initial_atvolumes)
    if not _initial_atvolumes:
        return atoms
    else:
        scale = ((_initial_atvolumes * n_at) / atoms.get_volume()) ** (1. / 3.)
        atoms.set_cell(cell * scale, scale_atoms=True)
        return atoms
