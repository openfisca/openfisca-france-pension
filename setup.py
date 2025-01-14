"""An openfisca based model of the French Pension system."""


from setuptools import find_packages, setup


setup(
    name = "OpenFisca-France-Pension",
    python_requires='>=3.9',
    version = "0.0.3",
    author = "OpenFisca Team",
    author_email = "contact@openfisca.org",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Operating System :: POSIX",
        "Programming Language :: Python",
        "Topic :: Scientific/Engineering :: Information Analysis",
        ],
    description = "OpenFisca tax and benefit system for France-Pension",
    keywords = "benefit microsimulation social tax",
    license ="http://www.fsf.org/licensing/licenses/agpl-3.0.html",
    url = "https://github.com/openfisca/openfisca-france-pension",
    include_package_data = True,  # Will read MANIFEST.in
    data_files = [
        (
            "share/openfisca/openfisca-france-pension",
            ["CHANGELOG.md", "LICENSE", "README.md"],
            ),
        ],
    install_requires = [
        "bottleneck >=1.3.2,<=2.0.0",
        "OpenFisca-Core >= 41.5.0,<44",
        "numba>=0.54,<1.0.0",
        "pandas>=2.0,<3.0",
        ],
    extras_require = {
        "dev": [
            "autopep8",
            "flake8>=3.9,<4.0",
            "flake8-import-order",
            "flake8-print",
            "pycodestyle >=2.6.0",
            ],
        # "scenario": [
        #     # "OpenFisca-Survey-Manager >=0.46.6,<1.0.0",
        #     # "pyreadr>=0.4.2,<1.0.0",
        #     ]
        },
    packages=find_packages(),
    )
