"""Abstract regimes definition."""
from datetime import datetime
import numpy as np
from openfisca_core.model_api import *
from openfisca_core.errors.variable_not_found_error import VariableNotFoundError
from openfisca_france_pension.entities import Person

def revalorise(variable_31_decembre_annee_precedente, variable_originale, annee_de_liquidation, revalorisation, period):
    return select([annee_de_liquidation > period.start.year, annee_de_liquidation == period.start.year, annee_de_liquidation < period.start.year], [0, variable_originale, variable_31_decembre_annee_precedente * revalorisation])
'Régimes complémentaires du secteur privé.'
import numpy as np
from openfisca_core.model_api import *
from openfisca_core.variables import Variable
from openfisca_france_pension.entities import Person
from openfisca_france_pension.regimes.regime import AbstractRegimeComplementaire
from openfisca_france_pension.variables.hors_regime import TypesCategorieSalarie

class agirc_coefficient_de_minoration(Variable):
    value_type = float
    default_value = 1.0
    entity = Person
    definition_period = YEAR
    label = 'Coefficient de minoration'

    def formula_1947_03_14(individu, period, parameters):
        minoration = parameters(period).secteur_prive.regimes_complementaires.agirc.coefficient_de_minoration
        coefficient_de_minoration_by_distance_aad_en_annee = minoration.coefficient_minoration_en_fonction_distance_age_annulation_decote_en_annee
        distances_age_annulation_decote_en_annee = np.asarray(list(coefficient_de_minoration_by_distance_aad_en_annee._children.keys())).astype('int')
        annees_de_decote = min_(max_((-individu('regime_general_cnav_decote_trimestres', period) / 4).astype(int), distances_age_annulation_decote_en_annee.min()), distances_age_annulation_decote_en_annee.max())
        coefficient_de_minoration = coefficient_de_minoration_by_distance_aad_en_annee[annees_de_decote]
        return coefficient_de_minoration

class agirc_cotisation(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'cotisation retraite employeur'

    def formula(individu, period):
        return individu('agirc_cotisation_employeur', period) + individu('agirc_cotisation_salarie', period)

class agirc_cotisation_employeur(Variable):
    value_type = float
    default_value = 0
    entity = Person
    definition_period = YEAR
    label = 'Cotisation employeur'

    def formula_2019(individu, period, parameters):
        categorie_salarie = individu('categorie_salarie', period)
        salaire_de_base = individu('salaire_de_base', period)
        plafond_securite_sociale = parameters(period).prelevements_sociaux.pss.plafond_securite_sociale_annuel
        employeur = parameters(period).secteur_prive.regimes_complementaires.agirc.prelevements_sociaux.agirc_arrco.employeur
        return (categorie_salarie == TypesCategorieSalarie.prive_cadre) * employeur.agirc_arrco.calc(salaire_de_base, factor=plafond_securite_sociale)

    def formula(individu, period, parameters):
        categorie_salarie = individu('categorie_salarie', period)
        salaire_de_base = individu('salaire_de_base', period)
        plafond_securite_sociale = parameters(period).prelevements_sociaux.pss.plafond_securite_sociale_annuel
        employeur = parameters(period).secteur_prive.regimes_complementaires.agirc.prelevements_sociaux.employeur
        return (categorie_salarie == TypesCategorieSalarie.prive_cadre) * employeur.agirc.calc(salaire_de_base, factor=plafond_securite_sociale)

class agirc_cotisation_salarie(Variable):
    value_type = float
    default_value = 0
    entity = Person
    definition_period = YEAR
    label = 'Cotisation salarié'

    def formula_2019(individu, period, parameters):
        categorie_salarie = individu('categorie_salarie', period)
        salaire_de_base = individu('salaire_de_base', period)
        plafond_securite_sociale = parameters(period).prelevements_sociaux.pss.plafond_securite_sociale_annuel
        salarie = parameters(period).secteur_prive.regimes_complementaires.agirc.prelevements_sociaux.agirc_arrco.salarie
        return (categorie_salarie == TypesCategorieSalarie.prive_cadre) * salarie.agirc_arrco.calc(salaire_de_base, factor=plafond_securite_sociale)

    def formula(individu, period, parameters):
        categorie_salarie = individu('categorie_salarie', period)
        salaire_de_base = individu('salaire_de_base', period)
        plafond_securite_sociale = parameters(period).prelevements_sociaux.pss.plafond_securite_sociale_annuel
        salarie = parameters(period).secteur_prive.regimes_complementaires.agirc.prelevements_sociaux.salarie
        return (categorie_salarie == TypesCategorieSalarie.prive_cadre) * salarie.agirc.calc(salaire_de_base, factor=plafond_securite_sociale)

class agirc_liquidation_date(Variable):
    value_type = date
    entity = Person
    definition_period = ETERNITY
    label = 'Date de liquidation'
    default_value = datetime.max.date()

class agirc_majoration_pension(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Majoration de pension'

    def formula_2012(individu, period, parameters):
        points_enfants = individu('agirc_points_enfants', period)
        valeur_du_point = parameters(period).secteur_prive.regimes_complementaires.agirc.point.valeur_point_en_euros
        points_enfants = individu('agirc_points_enfants', period)
        valeur_du_point = parameters(period).secteur_prive.regimes_complementaires.agirc.point.valeur_point_en_euros
        plafond = 1000 * valeur_du_point / parameters(2012).secteur_prive.regimes_complementaires.agirc.point.valeur_point_en_euros
        return where(individu('date_de_naissance', period) >= np.datetime64('1951-08-02'), min_(points_enfants * valeur_du_point, plafond), points_enfants * valeur_du_point)

    def formula_1999(individu, period, parameters):
        points_enfants = individu('agirc_points_enfants', period)
        valeur_du_point = parameters(period).secteur_prive.regimes_complementaires.agirc.point.valeur_point_en_euros
        return points_enfants * valeur_du_point

    def formula(individu, period, parameters):
        return individu.empty_array()

class agirc_majoration_pension_au_31_decembre(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Majoration de pension au 31 décembre'

    def formula(individu, period, parameters):
        annee_de_liquidation = individu('agirc_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970
        if all(period.start.year < annee_de_liquidation):
            return individu.empty_array()
        majoration_pension = individu('agirc_majoration_pension', period)
        return revalorise(majoration_pension, majoration_pension, annee_de_liquidation, 1, period)

class agirc_pension(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Pension'

    def formula(individu, period):
        pension_brute = individu('agirc_pension_brute', period)
        majoration_pension = individu('agirc_majoration_pension', period)
        coefficient_de_minoration = individu('agirc_coefficient_de_minoration', period)
        try:
            decote = individu('agirc_decote', period)
        except VariableNotFoundError:
            decote = 0
        pension = (pension_brute + majoration_pension) * (1 - decote) * coefficient_de_minoration
        return pension

class agirc_pension_au_31_decembre(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Pension brute au 31 décembre'

    def formula(individu, period, parameters):
        annee_de_liquidation = individu('agirc_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970
        if all(period.start.year < annee_de_liquidation):
            return individu.empty_array()
        pension = individu('agirc_pension', period)
        return revalorise(pension, pension, annee_de_liquidation, 1, period)

class agirc_pension_brute(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Pension brute'

    def formula(individu, period, parameters):
        valeur_du_point = parameters(period).secteur_prive.regimes_complementaires.agirc.point.valeur_point_en_euros
        points = individu('agirc_points', period)
        points_minimum_garantis = individu('agirc_points_minimum_garantis', period)
        pension_brute = (points + points_minimum_garantis) * valeur_du_point
        return pension_brute

class agirc_pension_brute_au_31_decembre(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Pension brute au 31 décembre'

    def formula(individu, period, parameters):
        annee_de_liquidation = individu('agirc_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970
        if all(period.start.year < annee_de_liquidation):
            return individu.empty_array()
        pension_brute = individu('agirc_pension_brute', period)
        return revalorise(pension_brute, pension_brute, annee_de_liquidation, 1, period)

class agirc_pension_servie(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Pension servie'

    def formula(individu, period, parameters):
        annee_de_liquidation = individu('agirc_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970
        if all(period.start.year < annee_de_liquidation):
            return individu.empty_array()
        pension = individu('agirc_pension', period)
        return revalorise(pension, pension, annee_de_liquidation, 1, period)

class agirc_points(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Points'

    def formula(individu, period, parameters):
        annee_de_liquidation = individu('agirc_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970
        last_year = period.start.period('year').offset(-1)
        salaire_de_reference = parameters(period).secteur_prive.regimes_complementaires.agirc.salaire_de_reference.salaire_reference_en_euros
        from openfisca_core.errors import ParameterNotFound
        try:
            taux_appel = parameters(period).secteur_prive.regimes_complementaires.agirc.prelevements_sociaux.taux_appel
        except ParameterNotFound:
            return individu.empty_array()
        cotisation = individu('agirc_cotisation', period)
        points_annee_courante = cotisation / salaire_de_reference / taux_appel
        points_annee_precedente = individu('agirc_points', last_year)
        if all(points_annee_precedente == 0):
            return points_annee_courante
        points = select([period.start.year > annee_de_liquidation, period.start.year <= annee_de_liquidation], [points_annee_precedente, points_annee_precedente + points_annee_courante])
        return points

class agirc_points_enfants(Variable):
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
        points_enfants_a_charge = individu('agirc_points_enfants_a_charge', period)
        points_enfants_nes_et_eleves = individu('agirc_points_enfants_nes_et_eleves', period)
        return max_(points_enfants_a_charge, points_enfants_nes_et_eleves)

class agirc_points_enfants_a_charge(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Points enfants à charge'

    def formula_2012(individu, period, parameters):
        points = individu('agirc_points', period)
        nombre_enfants_a_charge = individu('nombre_enfants_a_charge', period)
        return 0.05 * points * nombre_enfants_a_charge

class agirc_points_enfants_nes_et_eleves(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Points enfants nés et élevés'

    def formula_2012(individu, period):
        points = individu('agirc_points', period) - individu('agirc_points', 2011)
        nombre_enfants_nes_et_eleves = individu('nombre_enfants', period)
        points_enfants_nes_et_eleves_anterieurs = individu('agirc_points_enfants_nes_et_eleves', 2011)
        return 0.1 * points * (nombre_enfants_nes_et_eleves >= 3) + points_enfants_nes_et_eleves_anterieurs

    def formula_1945(individu, period):
        points = individu('agirc_points', period)
        nombre_enfants_nes_et_eleves = individu('nombre_enfants', period)
        return points * ((nombre_enfants_nes_et_eleves == 3) * 0.08 + (nombre_enfants_nes_et_eleves == 4) * 0.12 + (nombre_enfants_nes_et_eleves == 5) * 0.16 + (nombre_enfants_nes_et_eleves == 6) * 0.2 + (nombre_enfants_nes_et_eleves >= 7) * 0.24)

class agirc_points_minimum_garantis(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Points minimum garantis'

class arrco_coefficient_de_minoration(Variable):
    value_type = float
    default_value = 1.0
    entity = Person
    definition_period = YEAR
    label = 'Coefficient de minoration'

    def formula_1957_05_15(individu, period, parameters):
        minoration = parameters(period).secteur_prive.regimes_complementaires.arrco.coefficient_de_minoration
        coefficient_de_minoration_by_distance_aad_en_annee = minoration.coefficient_minoration_en_fonction_distance_age_annulation_decote_en_annee
        distances_age_annulation_decote_en_annee = np.asarray(list(coefficient_de_minoration_by_distance_aad_en_annee._children.keys())).astype('int')
        annees_de_decote = min_(max_((-individu('regime_general_cnav_decote_trimestres', period) / 4).astype(int), distances_age_annulation_decote_en_annee.min()), distances_age_annulation_decote_en_annee.max())
        coefficient_de_minoration = coefficient_de_minoration_by_distance_aad_en_annee[annees_de_decote]
        return coefficient_de_minoration

class arrco_cotisation(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'cotisation retraite employeur'

    def formula(individu, period):
        return individu('arrco_cotisation_employeur', period) + individu('arrco_cotisation_salarie', period)

class arrco_cotisation_employeur(Variable):
    value_type = float
    default_value = 0
    entity = Person
    definition_period = YEAR
    label = 'Cotisation employeur'

    def formula_2019(individu, period, parameters):
        categorie_salarie = individu('categorie_salarie', period)
        salaire_de_base = individu('salaire_de_base', period)
        plafond_securite_sociale = parameters(period).prelevements_sociaux.pss.plafond_securite_sociale_annuel
        employeur = parameters(period).secteur_prive.regimes_complementaires.arrco.prelevements_sociaux.agirc_arrco.employeur
        return (categorie_salarie == TypesCategorieSalarie.prive_non_cadre) * employeur.agirc_arrco.calc(salaire_de_base, factor=plafond_securite_sociale)

    def formula(individu, period, parameters):
        categorie_salarie = individu('categorie_salarie', period)
        salaire_de_base = individu('salaire_de_base', period)
        plafond_securite_sociale = parameters(period).prelevements_sociaux.pss.plafond_securite_sociale_annuel
        employeur = parameters(period).secteur_prive.regimes_complementaires.arrco.prelevements_sociaux.employeur
        employeur_non_cadre = employeur.noncadre.arrco.calc(salaire_de_base, factor=plafond_securite_sociale)
        employeur_cadre = employeur.cadre.arrco.calc(salaire_de_base, factor=plafond_securite_sociale)
        return select([categorie_salarie == TypesCategorieSalarie.prive_non_cadre, categorie_salarie == TypesCategorieSalarie.prive_cadre], [employeur_non_cadre, employeur_cadre])

class arrco_cotisation_salarie(Variable):
    value_type = float
    default_value = 0
    entity = Person
    definition_period = YEAR
    label = 'Cotisation salarié'

    def formula_2019(individu, period, parameters):
        categorie_salarie = individu('categorie_salarie', period)
        salaire_de_base = individu('salaire_de_base', period)
        plafond_securite_sociale = parameters(period).prelevements_sociaux.pss.plafond_securite_sociale_annuel
        salarie = parameters(period).secteur_prive.regimes_complementaires.arrco.prelevements_sociaux.agirc_arrco.salarie
        return (categorie_salarie == TypesCategorieSalarie.prive_non_cadre) * salarie.agirc_arrco.calc(salaire_de_base, factor=plafond_securite_sociale)

    def formula(individu, period, parameters):
        categorie_salarie = individu('categorie_salarie', period)
        salaire_de_base = individu('salaire_de_base', period)
        plafond_securite_sociale = parameters(period).prelevements_sociaux.pss.plafond_securite_sociale_annuel
        salarie = parameters(period).secteur_prive.regimes_complementaires.arrco.prelevements_sociaux.salarie
        salarie_non_cadre = salarie.noncadre.arrco.calc(salaire_de_base, factor=plafond_securite_sociale)
        salarie_cadre = salarie.cadre.arrco.calc(salaire_de_base, factor=plafond_securite_sociale)
        return select([categorie_salarie == TypesCategorieSalarie.prive_non_cadre, categorie_salarie == TypesCategorieSalarie.prive_cadre], [salarie_non_cadre, salarie_cadre])

class arrco_liquidation_date(Variable):
    value_type = date
    entity = Person
    definition_period = ETERNITY
    label = 'Date de liquidation'
    default_value = datetime.max.date()

class arrco_majoration_pension(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Majoration de pension'

    def formula_2012(individu, period, parameters):
        points_enfants = individu('arrco_points_enfants', period)
        valeur_du_point = parameters(period).secteur_prive.regimes_complementaires.arrco.point.valeur_point_en_euros
        points_enfants = individu('arrco_points_enfants', period)
        valeur_du_point = parameters(period).secteur_prive.regimes_complementaires.arrco.point.valeur_point_en_euros
        plafond = 1000 * valeur_du_point / parameters(2012).secteur_prive.regimes_complementaires.arrco.point.valeur_point_en_euros
        return where(individu('date_de_naissance', period) >= np.datetime64('1951-08-02'), min_(points_enfants * valeur_du_point, plafond), points_enfants * valeur_du_point)

    def formula_1999(individu, period, parameters):
        points_enfants = individu('arrco_points_enfants', period)
        valeur_du_point = parameters(period).secteur_prive.regimes_complementaires.arrco.point.valeur_point_en_euros
        return points_enfants * valeur_du_point

    def formula(individu, period, parameters):
        return individu.empty_array()

class arrco_majoration_pension_au_31_decembre(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Majoration de pension au 31 décembre'

    def formula(individu, period, parameters):
        annee_de_liquidation = individu('arrco_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970
        if all(period.start.year < annee_de_liquidation):
            return individu.empty_array()
        majoration_pension = individu('arrco_majoration_pension', period)
        return revalorise(majoration_pension, majoration_pension, annee_de_liquidation, 1, period)

class arrco_pension(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Pension'

    def formula(individu, period):
        pension_brute = individu('arrco_pension_brute', period)
        majoration_pension = individu('arrco_majoration_pension', period)
        coefficient_de_minoration = individu('arrco_coefficient_de_minoration', period)
        try:
            decote = individu('arrco_decote', period)
        except VariableNotFoundError:
            decote = 0
        pension = (pension_brute + majoration_pension) * (1 - decote) * coefficient_de_minoration
        return pension

class arrco_pension_au_31_decembre(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Pension brute au 31 décembre'

    def formula(individu, period, parameters):
        annee_de_liquidation = individu('arrco_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970
        if all(period.start.year < annee_de_liquidation):
            return individu.empty_array()
        pension = individu('arrco_pension', period)
        return revalorise(pension, pension, annee_de_liquidation, 1, period)

class arrco_pension_brute(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Pension brute'

    def formula(individu, period, parameters):
        valeur_du_point = parameters(period).secteur_prive.regimes_complementaires.arrco.point.valeur_point_en_euros
        points = individu('arrco_points', period)
        points_minimum_garantis = individu('arrco_points_minimum_garantis', period)
        pension_brute = (points + points_minimum_garantis) * valeur_du_point
        return pension_brute

class arrco_pension_brute_au_31_decembre(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Pension brute au 31 décembre'

    def formula(individu, period, parameters):
        annee_de_liquidation = individu('arrco_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970
        if all(period.start.year < annee_de_liquidation):
            return individu.empty_array()
        pension_brute = individu('arrco_pension_brute', period)
        return revalorise(pension_brute, pension_brute, annee_de_liquidation, 1, period)

class arrco_pension_servie(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Pension servie'

    def formula(individu, period, parameters):
        annee_de_liquidation = individu('arrco_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970
        if all(period.start.year < annee_de_liquidation):
            return individu.empty_array()
        pension = individu('arrco_pension', period)
        return revalorise(pension, pension, annee_de_liquidation, 1, period)

class arrco_points(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Points'

    def formula(individu, period, parameters):
        annee_de_liquidation = individu('arrco_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970
        last_year = period.start.period('year').offset(-1)
        salaire_de_reference = parameters(period).secteur_prive.regimes_complementaires.arrco.salaire_de_reference.salaire_reference_en_euros
        from openfisca_core.errors import ParameterNotFound
        try:
            taux_appel = parameters(period).secteur_prive.regimes_complementaires.arrco.prelevements_sociaux.taux_appel
        except ParameterNotFound:
            return individu.empty_array()
        cotisation = individu('arrco_cotisation', period)
        points_annee_courante = cotisation / salaire_de_reference / taux_appel
        points_annee_precedente = individu('arrco_points', last_year)
        if all(points_annee_precedente == 0):
            return points_annee_courante
        points = select([period.start.year > annee_de_liquidation, period.start.year <= annee_de_liquidation], [points_annee_precedente, points_annee_precedente + points_annee_courante])
        return points

class arrco_points_enfants(Variable):
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
        points_enfants_a_charge = individu('arrco_points_enfants_a_charge', period)
        points_enfants_nes_et_eleves = individu('arrco_points_enfants_nes_et_eleves', period)
        return max_(points_enfants_a_charge, points_enfants_nes_et_eleves)

class arrco_points_enfants_a_charge(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Points enfants à charge'

    def formula(individu, period, parameters):
        points = individu('arrco_points', period)
        nombre_enfants_a_charge = individu('nombre_enfants_a_charge', period)
        return 0.05 * points * nombre_enfants_a_charge

class arrco_points_enfants_nes_et_eleves(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Points enfants nés et élevés'

    def formula_2012(individu, period, parameters):
        nombre_enfants_nes_et_eleves = individu('nombre_enfants', period)
        if all(nombre_enfants_nes_et_eleves == 0):
            return individu.empty_array()
        points = individu('arrco_points', period) - individu('arrco_points', 2011)
        points_enfants_nes_et_eleves_anterieurs = individu('arrco_points_enfants_nes_et_eleves', 2011)
        return 0.1 * points * (nombre_enfants_nes_et_eleves >= 3) + points_enfants_nes_et_eleves_anterieurs

    def formula_1999(individu, period, parameters):
        nombre_enfants_nes_et_eleves = individu('nombre_enfants', period)
        if all(nombre_enfants_nes_et_eleves == 0):
            return individu.empty_array()
        points = individu('arrco_points', period) - individu('arrco_points', 1998)
        points_enfants_nes_et_eleves_anterieurs = individu('arrco_points_enfants_nes_et_eleves', 1998)
        return 0.05 * points * (nombre_enfants_nes_et_eleves >= 3) + points_enfants_nes_et_eleves_anterieurs

    def formula_1945(individu, period, parameters):
        return individu.empty_array()

class arrco_points_minimum_garantis(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Points minimum garantis'