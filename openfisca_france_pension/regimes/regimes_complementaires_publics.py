"""Régimes complémentaires du secteur privé."""

import numpy as np

from openfisca_core.model_api import *
from openfisca_core.parameters import ParameterNotFound
from openfisca_core.variables import Variable

from openfisca_france_pension.entities import Person
from openfisca_france_pension.regimes.regime import AbstractRegimeEnPoints
from openfisca_france_pension.variables.hors_regime import TypesCategorieSalarie
from openfisca_france_pension.regimes.regime_general_cnav import conversion_parametre_en_euros


class RegimeIrcantec(AbstractRegimeEnPoints):
    name = "Régime complémentaire public Ircantec"
    variable_prefix = "ircantec"
    parameters_prefix = "retraites.secteur_public.regimes_complementaires.ircantec"

    class coefficient_de_minoration(Variable):
        value_type = float
        default_value = 1.0
        entity = Person
        definition_period = YEAR
        label = "Coefficient de minoration"

        def formula_2010(individu, period, parameters):
            # TODO find starting date
            minoration = parameters(period).regime_name.coefficient_de_minoration
            trimestres_de_decote = min_(
                individu('regime_general_cnav_decote_trimestres', period),
                10 * 4,
                )
            coefficient_de_minoration = (
                np.clip(trimestres_de_decote, 0, 3 * 4) * minoration.decote_par_trimestre_entre_aod_plus_2_ans_et_add
                + np.clip(trimestres_de_decote - 3 * 4, 0, 2 * 4) * minoration.decote_par_trimestre_entre_aod_et_aod_plus_2_ans
                + + np.clip(trimestres_de_decote - 5 * 4, 0, 5 * 4) * minoration.decote_par_trimestre_avant_aod
                )
            trimestres_de_surcote = individu('regime_general_cnav_surcote_trimestres', period)
            coefficient_de_majoration = trimestres_de_surcote * minoration.surcote_par_trimestre
            return 1 - coefficient_de_minoration + coefficient_de_majoration

        def formula_1971(individu, period, parameters):
            # TODO find starting date
            minoration = parameters(period).regime_name.coefficient_de_minoration
            trimestres_de_decote = min_(
                individu('regime_general_cnav_decote_trimestres', period),
                10 * 4,
                )
            coefficient_de_minoration = (
                np.clip(trimestres_de_decote, 0, 3 * 4) * minoration.decote_par_trimestre_entre_aod_plus_2_ans_et_add
                + np.clip(trimestres_de_decote - 3 * 4, 0, 2 * 4) * minoration.decote_par_trimestre_entre_aod_et_aod_plus_2_ans
                + np.clip(trimestres_de_decote - 5 * 4, 0, 5 * 4) * minoration.decote_par_trimestre_avant_aod
                )
            return 1 - coefficient_de_minoration

    class cotisation(Variable):
        value_type = float
        default_value = 0
        entity = Person
        definition_period = YEAR
        label = "Cotisation"

        def formula(individu, period, parameters):
            categorie_salarie = individu("categorie_salarie", period)
            salaire_de_base = individu("regime_general_cnav_salaire_de_base", period)
            plafond_securite_sociale = parameters(period).prelevements_sociaux.pss.plafond_securite_sociale_annuel * conversion_parametre_en_euros(period.start.year)
            employeur = parameters(period).regime_name.prelevements_sociaux.employeur
            salarie = parameters(period).regime_name.prelevements_sociaux.salarie
            return (
                (categorie_salarie == TypesCategorieSalarie.public_non_titulaire)
                * (
                    employeur.ircantec.calc(salaire_de_base, factor = plafond_securite_sociale)
                    + salarie.ircantec.calc(salaire_de_base, factor = plafond_securite_sociale)
                    )
                )

    class majoration_pension(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Majoration de pension"

        def formula(individu, period, parameters):
            # TODO put parameters in parmaeter file
            nombre_enfants = individu('nombre_enfants', period)
            pension_brute = individu('regime_name_pension_brute', period)
            coefficient_de_majoration = min_(
                .1 * (nombre_enfants >= 3) + .05 * max_(nombre_enfants - 3, 0),
                .3,
                )
            return coefficient_de_majoration * pension_brute

    class pension_brute(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Pension brute"

        def formula(individu, period, parameters):
            valeur_du_point = parameters(period).regime_name.valeur_du_point
            points = individu("regime_name_points", period)
            pension_brute = points * valeur_du_point
            return pension_brute

    class points_annuels(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Points"

        def formula(individu, period, parameters):
            try:
                salaire_de_reference = parameters(period).regime_name.salaire_de_reference.salaire_reference_ircantec
            except ParameterNotFound:
                salaire_de_reference = parameters(period).regime_name.salaire_de_reference.salaire_reference_igrante
            try:
                taux_appel = parameters(period).prelevements_sociaux.cotisations_secteur_public.ircantec.taux_appel
            except ParameterNotFound:
                taux_appel = parameters(1971).prelevements_sociaux.cotisations_secteur_public.ircantec.taux_appel
            cotisation = individu("regime_name_cotisation", period)
            return cotisation / taux_appel / salaire_de_reference
