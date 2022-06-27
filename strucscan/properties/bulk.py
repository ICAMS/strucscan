def get_bulk_properties(calc, absolute_path):
    """
    :param calc: (strucscan.engine.generalengine.GeneralEngine object) calculator object
    :param absolute_path: (str) absolute path to job directory
    :return: (dict) python dictionary with summarized results
    """
    final_struct = calc.read_final_structure(absolute_path)
    energy = final_struct.get_potential_energy()

    result_dict = {}
    result_dict['structure_energy'] = energy
    result_dict['forces'] = final_struct.get_forces()
    result_dict['n_atom'] = len(final_struct)
    result_dict['volume'] = final_struct.get_volume()
    result_dict['stresses'] = final_struct.get_stress()
    result_dict['pressure'] = -1./3. * (final_struct.get_stress()[0:3])
    return result_dict
