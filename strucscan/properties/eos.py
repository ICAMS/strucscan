from ase.eos import EquationOfState

import numpy as np
import os

volume_range = 0.1
num_of_point = 11


def generate_structures(atoms):
    """
    :param atoms: (ASE atoms object)
    :return: (ASE atoms object list) list of modified ASE atoms objects
    """
    vol_min = 1 - volume_range
    vol_max = 1 + volume_range

    strained_structures = []
    for strain in np.linspace(vol_min, vol_max, num_of_point):
        basis = atoms.copy()

        cell = basis.get_cell()
        cell *= strain ** (1. / 3.)

        basis.set_cell(cell, scale_atoms=True)
        strained_structures.append(basis)
    return strained_structures


def get_EOS_properties(calc, absolute_path):
    """
    :param calc: (strucscan.engine.generalengine.GeneralEngine object) calculator object
    :param absolute_path: (str) absolute path to job directory
    :return: (dict) python dictionary with summarized results
    """
    energy_list = []
    volume_list = []
    stress_list = []
    pressure_list = []
    result_filename = calc.get_result_filename()
    for filename in os.listdir(absolute_path):
        if (result_filename in filename):
            final_struct = calc.read_final_structure(absolute_path,
                                                     resultfilename=filename)
            energy_list.append(final_struct.get_potential_energy())
            volume_list.append(final_struct.get_volume())
            stress = final_struct.get_stress()
            stress_list.append(stress)
            pressure_list.append(-1./3.*sum(stress[0:3]))

    eos = EquationOfState(volume_list, energy_list, eos='murnaghan')
    v0, e0, B = eos.fit()

    outputdict = {}
    outputdict["volume"] = np.array(volume_list)
    outputdict["energy"] = np.array(energy_list)
    outputdict['stresses'] = np.array(stress_list)
    outputdict['pressure'] = np.array(pressure_list)
    outputdict["equilibrium_energy"] = e0
    outputdict["equilibrium_volume"] = v0
    outputdict["equilibrium_bulk_modulus"] = B
    return outputdict
