from pprint import pprint
import traceback
import sys
import os

from strucscan.core import datatree
from strucscan.utils import DEBUG, SEPERATOR


def get_jobname(absolute_path):
    """
    :param absolute_path: (str) absolute path to job directory
    :return: (str) jobname, e.g. 'static__fcc__Al'
    """
    calculator, composition, property, prototype, stochio = datatree.parse_absolute_path(absolute_path)
    job_name = property + SEPERATOR + prototype + SEPERATOR + stochio
    return job_name


def get_result_dict(calc, property, absolute_path):
    """
    :param calc: (strucscan.engine.generalengine.GeneralEngine object) calculator object
    :param property: (str) name of property
    :param absolute_path: (str) absolute path to job directory
    :return: (dict) summarized results of calculation
    """
    result_dict = {}
    try:
        if property in ["static", "atomic", "total"]:
            from strucscan.properties import bulk
            result_dict = bulk.get_bulk_properties(calc, absolute_path)
        elif "eos" in property:
            from strucscan.properties import eos
            result_dict = eos.get_EOS_properties(calc, absolute_path)
    except Exception as exception:
        if DEBUG():
            print("Problem in collecting '{property}' properties from {path}:". \
                  format(property=property,
                         path=absolute_path))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print("line", exc_tb.tb_lineno, "in", fname, ":", exc_type)
            pprint(traceback.format_tb(exc_tb))
            print(exception)
    return result_dict
