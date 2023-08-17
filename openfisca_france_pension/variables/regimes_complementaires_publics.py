"""Abstract regimes definition."""
from openfisca_core.model_api import *
from openfisca_core.errors.variable_not_found_error import VariableNotFoundError
from openfisca_france_pension.entities import Person

def revalorise(variable_31_decembre_annee_precedente, variable_originale, annee_de_liquidation, revalorisation, period):
    return select([annee_de_liquidation > period.start.year, annee_de_liquidation == period.start.year, annee_de_liquidation < period.start.year], [0, variable_originale, variable_31_decembre_annee_precedente * revalorisation])
'Régimes complémentaires du secteur privé.'
import numpy as np
from openfisca_core.model_api import *
from openfisca_core.parameters import ParameterNotFound
from openfisca_core.variables import Variable
from openfisca_france_pension.entities import Person
from openfisca_france_pension.regimes.regime import AbstractRegimeEnPoints
from openfisca_france_pension.variables.hors_regime import TypesCategorieSalarie
from openfisca_france_pension.regimes.regime_general_cnav import conversion_parametre_en_euros

class ircantec_coefficient_de_minoration(Variable):
    value_type = float
    default_value = 1.0
    entity = Person
    definition_period = YEAR
    label = 'Coefficient de minoration'

    def formula_2010(individu, period, parameters):
        minoration = parameters(period).retraites.secteur_public.regimes_complementaires.ircantec.coefficient_de_minoration
        trimestres_de_decote = min_(individu('regime_general_cnav_decote_trimestres', period), 10 * 4)
        coefficient_de_minoration = np.clip(trimestres_de_decote, 0, 3 * 4) * minoration.decote_par_trimestre_entre_aod_plus_2_ans_et_add + np.clip(trimestres_de_decote - 3 * 4, 0, 2 * 4) * minoration.decote_par_trimestre_entre_aod_et_aod_plus_2_ans + +np.clip(trimestres_de_decote - 5 * 4, 0, 5 * 4) * minoration.decote_par_trimestre_avant_aod
        trimestres_de_surcote = individu('regime_general_cnav_surcote_trimestres', period)
        coefficient_de_majoration = trimestres_de_surcote * minoration.surcote_par_trimestre
        return 1 - coefficient_de_minoration + coefficient_de_majoration

    def formula_1971(individu, period, parameters):
        minoration = parameters(period).retraites.secteur_public.regimes_complementaires.ircantec.coefficient_de_minoration
        trimestres_de_decote = min_(individu('regime_general_cnav_decote_trimestres', period), 10 * 4)
        coefficient_de_minoration = np.clip(trimestres_de_decote, 0, 3 * 4) * minoration.decote_par_trimestre_entre_aod_plus_2_ans_et_add + np.clip(trimestres_de_decote - 3 * 4, 0, 2 * 4) * minoration.decote_par_trimestre_entre_aod_et_aod_plus_2_ans + np.clip(trimestres_de_decote - 5 * 4, 0, 5 * 4) * minoration.decote_par_trimestre_avant_aod
        return 1 - coefficient_de_minoration

class ircantec_cotisation(Variable):
    value_type = float
    default_value = 0
    entity = Person
    definition_period = YEAR
    label = 'Cotisation'

    def formula(individu, period, parameters):
        categorie_salarie = individu('categorie_salarie', period)
        salaire_de_base = individu('regime_general_cnav_salaire_de_base', period)
        plafond_securite_sociale = parameters(period).prelevements_sociaux.pss.plafond_securite_sociale_annuel * conversion_parametre_en_euros(period.start.year)
        employeur = parameters(period).retraites.secteur_public.regimes_complementaires.ircantec.prelevements_sociaux.employeur
        salarie = parameters(period).retraites.secteur_public.regimes_complementaires.ircantec.prelevements_sociaux.salarie
        return (categorie_salarie == TypesCategorieSalarie.public_non_titulaire) * (employeur.ircantec.calc(salaire_de_base, factor=plafond_securite_sociale) + salarie.ircantec.calc(salaire_de_base, factor=plafond_securite_sociale))

class ircantec_liquidation_date(Variable):
    value_type = date
    entity = Person
    definition_period = ETERNITY
    label = 'Date de liquidation'
    default_value = date(2250, 12, 31)

class ircantec_majoration_pension(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Majoration de pension'

    def formula(individu, period, parameters):
        nombre_enfants = individu('nombre_enfants', period)
        pension_brute = individu('ircantec_pension_brute', period)
        coefficient_de_majoration = min_(0.1 * (nombre_enfants >= 3) + 0.05 * max_(nombre_enfants - 3, 0), 0.3)
        return coefficient_de_majoration * pension_brute

class ircantec_majoration_pension_au_31_decembre(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Majoration de pension au 31 décembre'

    def formula(individu, period, parameters):
        annee_de_liquidation = individu('ircantec_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970
        if all(period.start.year < annee_de_liquidation):
            return individu.empty_array()
        majoration_pension = individu('ircantec_majoration_pension', period)
        return revalorise(majoration_pension, majoration_pension, annee_de_liquidation, 1, period)

class ircantec_pension(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Pension'

    def formula(individu, period):
        pension_brute = individu('ircantec_pension_brute', period)
        majoration_pension = individu('ircantec_majoration_pension', period)
        coefficient_de_minoration = individu('ircantec_coefficient_de_minoration', period)
        try:
            decote = individu('ircantec_decote', period)
        except VariableNotFoundError:
            decote = 0
        pension = (pension_brute + majoration_pension) * (1 - decote) * coefficient_de_minoration
        return pension

class ircantec_pension_au_31_decembre(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Pension brute au 31 décembre'

    def formula(individu, period, parameters):
        annee_de_liquidation = individu('ircantec_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970
        if all(period.start.year < annee_de_liquidation):
            return individu.empty_array()
        pension = individu('ircantec_pension', period)
        return revalorise(pension, pension, annee_de_liquidation, 1, period)

class ircantec_pension_brute(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Pension brute'

    def formula(individu, period, parameters):
        valeur_du_point = parameters(period).retraites.secteur_public.regimes_complementaires.ircantec.valeur_du_point
        points = individu('ircantec_points', period)
        pension_brute = points * valeur_du_point
        return pension_brute

class ircantec_pension_brute_au_31_decembre(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Pension brute au 31 décembre'

    def formula(individu, period, parameters):
        annee_de_liquidation = individu('ircantec_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970
        if all(period.start.year < annee_de_liquidation):
            return individu.empty_array()
        pension_brute = individu('ircantec_pension_brute', period)
        return revalorise(pension_brute, pension_brute, annee_de_liquidation, 1, period)

class ircantec_pension_servie(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Pension servie'

    def formula(individu, period, parameters):
        annee_de_liquidation = individu('ircantec_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970
        if all(period.start.year < annee_de_liquidation):
            return individu.empty_array()
        pension = individu('ircantec_pension', period)
        return revalorise(pension, pension, annee_de_liquidation, 1, period)

class ircantec_points(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Points'

    def formula(individu, period, parameters):
        annee_de_liquidation = individu('ircantec_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970
        last_year = period.last_year
        points_annee_precedente = individu('ircantec_points', last_year)
        points_annuels_annee_courante = individu('ircantec_points_annuels', period) + individu('ircantec_points_a_la_liquidation', period) * (annee_de_liquidation == period.start.year)
        if all(points_annee_precedente == 0):
            return points_annuels_annee_courante
        points = select([period.start.year > annee_de_liquidation, period.start.year <= annee_de_liquidation], [points_annee_precedente, points_annee_precedente + points_annuels_annee_courante])
        return points

class ircantec_points_a_la_liquidation(Variable):
    value_type = float
    entity = Person
    definition_period = ETERNITY
    label = 'Points à la liquidation'

class ircantec_points_annuels(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Points'

    def formula(individu, period, parameters):
        try:
            salaire_de_reference = parameters(period).retraites.secteur_public.regimes_complementaires.ircantec.salaire_de_reference.salaire_reference_ircantec
        except ParameterNotFound:
            salaire_de_reference = parameters(period).retraites.secteur_public.regimes_complementaires.ircantec.salaire_de_reference.salaire_reference_igrante
        try:
            taux_appel = parameters(period).prelevements_sociaux.cotisations_secteur_public.ircantec.taux_appel
        except ParameterNotFound:
            taux_appel = parameters(1971).prelevements_sociaux.cotisations_secteur_public.ircantec.taux_appel
        cotisation = individu('ircantec_cotisation', period)
        return cotisation / taux_appel / salaire_de_reference

class ircantec_points_minimum_garantis(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Points minimum garantis'