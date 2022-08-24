import pytest
import os

from strucscan.core.jobmanager import JobManager
from strucscan.resources.inputyaml import DUMMY

def test_dummy():
    input_dict = DUMMY().EXAMPLE
    input_dict.update({'verbose': True})

    assert os.path.exists("/home/users/pietki8q/git/strucscan-pietki8q/tests/data/DUMMY/Al") == True
    assert os.path.exists("/home/users/pietki8q/git/strucscan-pietki8q/tests/data/DUMMY/Al/static__fcc__Al") == True
    assert len(os.listdir("/home/users/pietki8q/git/strucscan-pietki8q/tests/data/DUMMY/Al/static__fcc__Al")) == 8

    assert os.path.exists("/home/users/pietki8q/git/strucscan-pietki8q/tests/data/DUMMY/Al/atomic__fcc__Al") == True
    assert len(os.listdir("/home/users/pietki8q/git/strucscan-pietki8q/tests/data/DUMMY/Al/atomic__fcc__Al")) == 8

    assert os.path.exists("/home/users/pietki8q/git/strucscan-pietki8q/tests/data/DUMMY/Al/total__fcc__Al") == True
    assert len(os.listdir("/home/users/pietki8q/git/strucscan-pietki8q/tests/data/DUMMY/Al/total__fcc__Al")) == 8

    assert os.path.exists("/home/users/pietki8q/git/strucscan-pietki8q/tests/data/DUMMY/Al/eos_total__fcc__Al") == True
    assert len(os.listdir("/home/users/pietki8q/git/strucscan-pietki8q/tests/data/DUMMY/Al/eos_total__fcc__Al")) == 27
