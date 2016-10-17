"""Package for NamedStruct."""

import sys

__project__ = 'NamedStruct'
__version__ = '0.9.0'

VERSION = __project__ + '-' + __version__

PYTHON_VERSION = 3, 5

if not sys.version_info >= PYTHON_VERSION:  # pragma: no cover (manual test)
    exit("Python {}.{}+ is required.".format(*PYTHON_VERSION))

try:
    # pylint: disable=wrong-import-position
    from namedstruct.message import Message
    from namedstruct.modes import Mode

    # silence F401 flake8 error
    assert Message
    assert Mode

    # Hack to import all the element files and get them registered
    # import importlib
    # import glob
    # import os

    # print('printing file names')
    # print(os.path.dirname(os.path.abspath(__file__)) + '/element*')
    # for file in glob.glob(os.path.dirname(os.path.abspath(__file__)) + '/element*'):
    #     print(file.split(os.sep)[-1][:-3])

    #     mod = importlib.import_module('namedstruct.' + file)
    #     mod.__name__

    __all__ = ['Message', 'Mode']
except ImportError:  # pragma: no cover (manual test)
    pass
