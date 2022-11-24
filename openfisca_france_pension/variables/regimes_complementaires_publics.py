"""Abstract regimes definition."""
import numpy as np
from openfisca_core.model_api import *
from openfisca_core.errors.variable_not_found_error import VariableNotFoundError
from openfisca_france_pension.entities import Person

def revalorise(variable_31_decembre_annee_precedente, variable_originale, annee_de_liquidation, revalorisation, period):
    return select([annee_de_liquidation > period.start.year, annee_de_liquidation == period.start.year, annee_de_liquidation < period.start.year], [0, variable_originale, variable_31_decembre_annee_precedente * revalorisation])
'Régimes complémentaires du secteur privé.'
from openfisca_core.model_api import *
from openfisca_core.variables import Variable
from openfisca_france_pension.entities import Person
from openfisca_france_pension.regimes.regime import AbstractRegimeComplementaire
from openfisca_france_pension.variables.hors_regime import TypesCategorieSalarie
from openfisca_france_pension.regimes.regime_general_cnav import conversion_parametre_en_euros

class ircantec_coefficient_de_minoration(Variable):
    value_type = float
    default_value = 1.0
    entity = Person
    definition_period = YEAR
    label = 'Coefficient de minoration'

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
        employeur = parameters(period).secteur_public.regimes_complementaires.ircantec.prelevements_sociaux.employeur
        salarie = parameters(period).secteur_public.regimes_complementaires.ircantec.prelevements_sociaux.salarie
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

    def formula_2019(individu, period, parameters):
        points_enfants = individu('ircantec_points_enfants', period)
        valeur_du_point = parameters(period).secteur_prive.regimes_complementaires.agirc_arrco.point.valeur_point_en_euros
        plafond = 1000 * valeur_du_point / parameters(2012).secteur_prive.regimes_complementaires.arrco.point.valeur_point_en_euros
        return where(individu('date_de_naissance', period) >= np.datetime64('1951-08-02'), min_(points_enfants * valeur_du_point, plafond), points_enfants * valeur_du_point)

    def formula_2012(individu, period, parameters):
        points_enfants = individu('ircantec_points_enfants', period)
        valeur_du_point = parameters(period).secteur_public.regimes_complementaires.ircantec.point.valeur_point_en_euros
        plafond = 1000 * valeur_du_point / parameters(2012).secteur_public.regimes_complementaires.ircantec.point.valeur_point_en_euros
        return where(individu('date_de_naissance', period) >= np.datetime64('1951-08-02'), min_(points_enfants * valeur_du_point, plafond), points_enfants * valeur_du_point)

    def formula_1999(individu, period, parameters):
        points_enfants = individu('ircantec_points_enfants', period)
        valeur_du_point = parameters(period).secteur_public.regimes_complementaires.ircantec.point.valeur_point_en_euros
        return points_enfants * valeur_du_point

    def formula(individu, period, parameters):
        return individu.empty_array()

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

    def formula_2019(individu, period, parameters):
        valeur_du_point = parameters(period).secteur_prive.regimes_complementaires.agirc_arrco.point.valeur_point_en_euros
        points = individu('ircantec_points', period)
        points_minimum_garantis = individu('ircantec_points_minimum_garantis', period)
        pension_brute = (points + points_minimum_garantis) * valeur_du_point
        return pension_brute

    def formula(individu, period, parameters):
        valeur_du_point = parameters(period).secteur_public.regimes_complementaires.ircantec.point.valeur_point_en_euros
        points = individu('ircantec_points', period)
        points_minimum_garantis = individu('ircantec_points_minimum_garantis', period)
        pension_brute = (points + points_minimum_garantis) * valeur_du_point
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
        last_year = period.start.period('year').offset(-1)
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
        salaire_de_reference = parameters(period).secteur_public.regimes_complementaires.ircantec.salaire_de_reference.salaire_reference_en_euros
        taux_appel = parameters(period).secteur_public.regimes_complementaires.ircantec.prelevements_sociaux.taux_appel
        cotisation = individu('ircantec_cotisation', period)
        return cotisation / salaire_de_reference / taux_appel

class ircantec_points_enfants(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Points enfants'

    def formula(individu, period, parameters):
        """
            Deux types de majorations pour enfants peuvent s'appliquer :
                - pour enfant à charge au moment du départ en retraite
                - pour enfant nés et élevés en cours de carrière (majoration sur la totalité des droits acquis)
                C'est la plus avantageuse qui s'applique.
            """
        points_enfants_a_charge = individu('ircantec_points_enfants_a_charge', period)
        points_enfants_nes_et_eleves = individu('ircantec_points_enfants_nes_et_eleves', period)
        return max_(points_enfants_a_charge, points_enfants_nes_et_eleves)

class ircantec_points_enfants_a_charge(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Points enfants à charge'

class ircantec_points_enfants_nes_et_eleves(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Points enfants nés et élevés'

class ircantec_points_minimum_garantis(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Points minimum garantis'