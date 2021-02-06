"""Tests regime generation."""


import filecmp
import os
import pkg_resources

france_pension_root =  pkg_resources.get_distribution("openfisca-france-pension").location


def test_regime_de_base():
    original = os.path.join(
        france_pension_root,
        'openfisca_france_pension',
        'variables',
        'regime_de_base.py'
        )
    generated = os.path.join(
        france_pension_root,
        'openfisca_france_pension',
        "scripts_ast",
        "result_file_regime_de_base.py"
        )
    assert(filecmp.cmp(original, generated))