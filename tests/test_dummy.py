import pytest
import os

from strucscan.core.jobmanager import JobManager
from strucscan.resources.inputyaml import DUMMY

from strucscan.utils import PROJECT_PATH

def test_dummy():
    input_dict = DUMMY().EXAMPLE
    input_dict.update({'verbose': True})

    JobManager(input_dict)

    assert os.path.exists(PROJECT_PATH() + "/DUMMY/Al") == True
    assert os.path.exists(PROJECT_PATH() + "/DUMMY/Al/static__fcc__Al") == True
    assert len(os.listdir(PROJECT_PATH() + "/DUMMY/Al/static__fcc__Al")) == 8

    assert os.path.exists(PROJECT_PATH() + "/DUMMY/Al/atomic__fcc__Al") == True
    assert len(os.listdir(PROJECT_PATH() + "/DUMMY/Al/atomic__fcc__Al")) == 8

    assert os.path.exists(PROJECT_PATH() + "/DUMMY/Al/total__fcc__Al") == True
    assert len(os.listdir(PROJECT_PATH() + "/DUMMY/Al/total__fcc__Al")) == 8

    assert os.path.exists(PROJECT_PATH() + "/DUMMY/Al/eos_static__fcc__Al") == True
    assert len(os.listdir(PROJECT_PATH() + "/DUMMY/Al/eos_static__fcc__Al")) == 27
