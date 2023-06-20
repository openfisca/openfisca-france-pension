"""OpenFisca France Pension tax-benefit system."""

import logging
import os

from openfisca_core.parameters import ParameterNode
from openfisca_core.taxbenefitsystems import TaxBenefitSystem

from openfisca_france_pension import entities
from openfisca_france_pension.scripts_ast import script_ast
from openfisca_france_pension.revalorisation.salaire import build_coefficient_by_annee_salaire

COUNTRY_DIR = os.path.dirname(os.path.abspath(__file__))

logging.getLogger('numba.core.ssa').disabled = True
logging.getLogger('numba.core.byteflow').disabled = True
logging.getLogger('numba.core.interpreter').disabled = True

# Convert regimes classes to OpenFisca variables.
script_ast.main(verbose = False)


def build_regimes_prelevements_sociaux(parameters):
    # Cnav
    regime_general_cnav = parameters.prelevements_sociaux.cotisations_securite_sociale_regime_general.cnav
    parameters.retraites.secteur_prive.regime_general_cnav.add_child(
        "prelevements_sociaux",
        regime_general_cnav,
        )
    # Agric-Arrco pré 2019
    arrco = parameters.prelevements_sociaux.regimes_complementaires_retraite_secteur_prive.arrco
    parameters.retraites.secteur_prive.regimes_complementaires.arrco.add_child(
        "prelevements_sociaux",
        arrco,
        )
    agirc = parameters.prelevements_sociaux.regimes_complementaires_retraite_secteur_prive.agirc
    parameters.retraites.secteur_prive.regimes_complementaires.agirc.add_child(
        "prelevements_sociaux",
        agirc,
        )
    # Régime unifié Agric-Arrco depuis 2019
    agirc_arrco = parameters.prelevements_sociaux.regimes_complementaires_retraite_secteur_prive.agirc_arrco
    parameters.retraites.secteur_prive.regimes_complementaires.agirc_arrco.add_child(
        "prelevements_sociaux",
        agirc_arrco,
        )
    parameters.retraites.secteur_prive.regimes_complementaires.arrco.prelevements_sociaux.add_child(
        "agirc_arrco",
        agirc_arrco,
        )
    parameters.retraites.secteur_prive.regimes_complementaires.agirc.prelevements_sociaux.add_child(
        "agirc_arrco",
        agirc_arrco,
        )

    # Ircantec
    ircantec = parameters.prelevements_sociaux.cotisations_secteur_public.ircantec
    parameters.retraites.secteur_public.regimes_complementaires.ircantec.add_child(
        "prelevements_sociaux",
        ircantec.taux_cotisations_appeles
        )


build_coefficient_by_annee_salaire()


class CountryTaxBenefitSystem(TaxBenefitSystem):
    def __init__(self):
        super(CountryTaxBenefitSystem, self).__init__(entities.entities)
        self.add_variables_from_directory(os.path.join(COUNTRY_DIR, 'variables'))
        param_path = os.path.join(COUNTRY_DIR, 'parameters')
        self.load_parameters(param_path)
        taux_plein = ParameterNode(
            "taux_plein",
            data = {
                "taux_plein": {
                    "values": {
                        "1948-01-01": .75
                        }
                    }
                }
            )
        self.parameters.retraites.secteur_public.pension_civile.add_child("taux_plein", taux_plein)
        build_regimes_prelevements_sociaux(self.parameters)

        arrco = self.parameters.retraites.secteur_prive.regimes_complementaires.arrco.salaire_de_reference.salaire_reference_en_euros
        unirs = self.parameters.retraites.secteur_prive.regimes_complementaires.unirs.salaire_de_reference.salaire_reference_en_euros
        arrco.values_list = arrco.values_list + unirs.values_list

        arrco = self.parameters.retraites.secteur_prive.regimes_complementaires.arrco.salaire_de_reference.salaire_reference_en_euros
        unirs = self.parameters.retraites.secteur_prive.regimes_complementaires.unirs.salaire_de_reference.salaire_reference_en_euros
        arrco.values_list = arrco.values_list + unirs.values_list

        arrco = self.parameters.retraites.secteur_prive.regimes_complementaires.arrco.point.valeur_point_en_euros
        unirs = self.parameters.retraites.secteur_prive.regimes_complementaires.unirs.point.valeur_point_en_euros
        arrco.values_list = arrco.values_list + unirs.values_list

        self.cache_blacklist = [
            "fonction_publique_aod",
            "fonction_publique_salaire_de_reference",
            "regime_general_cnav_duree_assurance_avpf_annuelle",
            "regime_general_cnav_duree_assurance_emploi_annuelle",
            "regime_general_cnav_duree_assurance_cotisee_annuelle",
            "regime_general_cnav_duree_assurance_annuelle"
            "regime_general_cnav_duree_assurance_periode_assimilee_annuelle"
            "regime_general_cnav_decote_trimestres",
            "regime_general_cnav_surcote_trimestres",
            ]
