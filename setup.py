import os
from setuptools import setup, find_packages

import versioneer

def package_files(directory):
    paths = []
    for (path, directories, filenames) in os.walk(directory):
        for filename in filenames:
            paths.append(os.path.join('..', path, filename))
    return paths

extra_files = package_files('strucscan/resources')



setup(
    name="strucscan",
    version=versioneer.get_version(),
    description="Lightweight Python-based framework for high-throughput material simulation by ICAMS, Ruhr University Bochum",
    url='https://github.com/ICAMS/strucscan',
    author='Isabel Pietka',
    author_email='isabel.pietka@rub.de',
    license='GPL3',

    classifiers=['Development Status :: 5 - Production/Stable',
                 'Topic :: Scientific/Engineering :: Physics',
                 'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
                 'Intended Audience :: Science/Research',
                 'Operating System :: OS Independent',
                 'Programming Language :: Python :: 3',
                 'Programming Language :: Python :: 3.4',
                 'Programming Language :: Python :: 3.5',
                 'Programming Language :: Python :: 3.6',
                 'Programming Language :: Python :: 3.7'],

    keywords='computational materials science',
    packages=find_packages(include=['strucscan', 'strucscan.*']),
    install_requires=['ase', 'numpy', 'pyyaml'],
    cmdclass=versioneer.get_cmdclass(),
    include_package_data=True,
    package_data={'': extra_files},
    entry_points={
            'console_scripts': [
                'strucscan = strucscan.cli:main'
            ]
        },
)


