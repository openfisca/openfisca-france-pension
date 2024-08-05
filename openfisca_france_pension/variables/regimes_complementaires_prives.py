"""Abstract regimes definition."""
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
from openfisca_france_pension.regimes.regime import AbstractRegimeEnPoints
from openfisca_france_pension.variables.hors_regime import TypesCategorieSalarie
from openfisca_france_pension.regimes.regime_general_cnav import conversion_parametre_en_euros

class agirc_coefficient_de_minoration(Variable):
    value_type = float
    default_value = 1.0
    entity = Person
    definition_period = YEAR
    label = 'Coefficient de minoration'

    def formula_1947_03_14(individu, period, parameters):
        minoration = parameters(period).retraites.secteur_prive.regimes_complementaires.agirc.coefficient_de_minoration
        coefficient_de_minoration_by_distance_aad_en_annee = minoration.coefficient_minoration_en_fonction_distance_age_annulation_decote_en_annee
        distances_age_annulation_decote_en_annee = np.asarray(list(coefficient_de_minoration_by_distance_aad_en_annee._children.keys())).astype('int')
        annees_de_decote = min_(max_((-individu('regime_general_cnav_decote_trimestres', period) / 4).astype(int), distances_age_annulation_decote_en_annee.min()), distances_age_annulation_decote_en_annee.max())
        coefficient_de_minoration = coefficient_de_minoration_by_distance_aad_en_annee[annees_de_decote]
        return coefficient_de_minoration

class agirc_cotisation(Variable):
    value_type = float
    default_value = 0
    entity = Person
    definition_period = YEAR
    label = 'Cotisation'

    def formula_2019(individu, period, parameters):
        categorie_salarie = individu('categorie_salarie', period)
        salaire_de_base = individu('regime_general_cnav_salaire_de_base', period)
        plafond_securite_sociale = parameters(period).prelevements_sociaux.pss.plafond_securite_sociale_annuel * conversion_parametre_en_euros(period.start.year)
        employeur = parameters(period).retraites.secteur_prive.regimes_complementaires.agirc.prelevements_sociaux.agirc_arrco.employeur
        salarie = parameters(period).retraites.secteur_prive.regimes_complementaires.agirc.prelevements_sociaux.agirc_arrco.salarie
        return (categorie_salarie == TypesCategorieSalarie.prive_cadre) * (employeur.agirc_arrco.calc(salaire_de_base, factor=plafond_securite_sociale) + salarie.agirc_arrco.calc(salaire_de_base, factor=plafond_securite_sociale))

    def formula_1948(individu, period, parameters):
        categorie_salarie = individu('categorie_salarie', period)
        salaire_de_base = individu('regime_general_cnav_salaire_de_base', period)
        plafond_securite_sociale = parameters(period).prelevements_sociaux.pss.plafond_securite_sociale_annuel * conversion_parametre_en_euros(period.start.year)
        employeur = parameters(period).retraites.secteur_prive.regimes_complementaires.agirc.prelevements_sociaux.taux_effectifs_salaries_employeurs.avant81.employeur.agirc.copy()
        salarie = parameters(period).retraites.secteur_prive.regimes_complementaires.agirc.prelevements_sociaux.taux_effectifs_salaries_employeurs.avant81.salarie.agirc.copy()
        agirc = employeur
        agirc.add_tax_scale(salarie)
        points_gmp = parameters(period).retraites.secteur_prive.regimes_complementaires.agirc.gmp.garantie_minimale_points
        salaire_de_reference = parameters(period).retraites.secteur_prive.regimes_complementaires.agirc.salaire_de_reference.salaire_reference_en_euros
        taux_appel = parameters(period).retraites.secteur_prive.regimes_complementaires.agirc.prelevements_sociaux.taux_appel
        cotisation_gmp_annuelle = points_gmp * salaire_de_reference * taux_appel
        base_gmp_annuelle = cotisation_gmp_annuelle / agirc.rates[1]
        salaire_charniere_annuel = plafond_securite_sociale + base_gmp_annuelle
        salaire_charniere = salaire_charniere_annuel / plafond_securite_sociale
        cotisation = cotisation_gmp_annuelle
        n = (cotisation + 0.1) * 12
        agirc.add_bracket(n / plafond_securite_sociale, 0)
        agirc.rates[0] = cotisation / n
        agirc.thresholds[2] = salaire_charniere
        return (categorie_salarie == TypesCategorieSalarie.prive_cadre) * agirc.calc(salaire_de_base, factor=plafond_securite_sociale)

class agirc_liquidation_date(Variable):
    value_type = date
    entity = Person
    definition_period = ETERNITY
    label = 'Date de liquidation'
    default_value = date(2250, 12, 31)

class agirc_majoration_pension(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Majoration de pension'

    def formula_2019(individu, period, parameters):
        points_enfants = individu('agirc_points_enfants', period)
        valeur_du_point = parameters(period).retraites.secteur_prive.regimes_complementaires.agirc_arrco.point.valeur_point_en_euros
        plafond = 1000 * valeur_du_point / parameters(2012).retraites.secteur_prive.regimes_complementaires.arrco.point.valeur_point_en_euros
        return where(individu('date_de_naissance', period) >= np.datetime64('1951-08-02'), min_(points_enfants * valeur_du_point, plafond), points_enfants * valeur_du_point)

    def formula_2012(individu, period, parameters):
        points_enfants = individu('agirc_points_enfants', period)
        valeur_du_point = parameters(period).retraites.secteur_prive.regimes_complementaires.agirc.point.valeur_point_en_euros
        plafond = 1000 * valeur_du_point / parameters(2012).retraites.secteur_prive.regimes_complementaires.agirc.point.valeur_point_en_euros
        return where(individu('date_de_naissance', period) >= np.datetime64('1951-08-02'), min_(points_enfants * valeur_du_point, plafond), points_enfants * valeur_du_point)

    def formula_1999(individu, period, parameters):
        points_enfants = individu('agirc_points_enfants', period)
        valeur_du_point = parameters(period).retraites.secteur_prive.regimes_complementaires.agirc.point.valeur_point_en_euros
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

    def formula_2019(individu, period, parameters):
        valeur_du_point = parameters(period).retraites.secteur_prive.regimes_complementaires.agirc_arrco.point.valeur_point_en_euros
        points = individu('agirc_points', period)
        points_minimum_garantis = individu('agirc_points_minimum_garantis', period)
        pension_brute = (points + points_minimum_garantis) * valeur_du_point
        return pension_brute

    def formula(individu, period, parameters):
        valeur_du_point = parameters(period).retraites.secteur_prive.regimes_complementaires.agirc.point.valeur_point_en_euros
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
        last_year = period.last_year
        points_annee_precedente = individu('agirc_points', last_year)
        points_annuels_annee_courante = individu('agirc_points_annuels', period) + individu('agirc_points_a_la_liquidation', period) * (annee_de_liquidation == period.start.year)
        if all(points_annee_precedente == 0):
            return points_annuels_annee_courante
        points = select([period.start.year > annee_de_liquidation, period.start.year <= annee_de_liquidation], [points_annee_precedente, points_annee_precedente + points_annuels_annee_courante])
        return points

class agirc_points_a_la_liquidation(Variable):
    value_type = float
    entity = Person
    definition_period = ETERNITY
    label = 'Points à la liquidation'

class agirc_points_annuels(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Points annuels'

    def formula(individu, period):
        points_emploi_annuels = individu('agirc_points_emploi_annuels', period)
        points_hors_emploi_annuels = individu('agirc_points_hors_emploi_annuels', period)
        return points_emploi_annuels + points_hors_emploi_annuels

class agirc_points_emploi_annuels(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Points annuels en emploi'

    def formula_2019(individu, period, parameters):
        agirc_arrco = parameters(period).retraites.secteur_prive.regimes_complementaires.agirc_arrco
        salaire_de_reference = agirc_arrco.salaire_de_reference.salaire_reference_en_euros
        taux_appel = agirc_arrco.prelevements_sociaux.taux_appel
        cotisation = individu('agirc_cotisation', period)
        return cotisation / salaire_de_reference / taux_appel

    def formula_1947(individu, period, parameters):
        salaire_de_reference = parameters(period).retraites.secteur_prive.regimes_complementaires.agirc.salaire_de_reference.salaire_reference_en_euros
        taux_appel = parameters(period).retraites.secteur_prive.regimes_complementaires.agirc.prelevements_sociaux.taux_appel
        cotisation = individu('agirc_cotisation', period)
        return cotisation / salaire_de_reference / taux_appel

class agirc_points_enfants(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Points enfants'

    def formula(individu, period):
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

class agirc_points_hors_emploi_annuels(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Points annuels hors emploi'

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
        minoration = parameters(period).retraites.secteur_prive.regimes_complementaires.arrco.coefficient_de_minoration
        coefficient_de_minoration_by_distance_aad_en_annee = minoration.coefficient_minoration_en_fonction_distance_age_annulation_decote_en_annee
        distances_age_annulation_decote_en_annee = np.asarray(list(coefficient_de_minoration_by_distance_aad_en_annee._children.keys())).astype('int')
        annees_de_decote = min_(max_((-individu('regime_general_cnav_decote_trimestres', period) / 4).astype(int), distances_age_annulation_decote_en_annee.min()), distances_age_annulation_decote_en_annee.max())
        coefficient_de_minoration = coefficient_de_minoration_by_distance_aad_en_annee[annees_de_decote]
        return coefficient_de_minoration

class arrco_cotisation(Variable):
    value_type = float
    default_value = 0
    entity = Person
    definition_period = YEAR
    label = 'Cotisation'

    def formula_2019(individu, period, parameters):
        categorie_salarie = individu('categorie_salarie', period)
        salaire_de_base = individu('regime_general_cnav_salaire_de_base', period)
        plafond_securite_sociale = parameters(period).prelevements_sociaux.pss.plafond_securite_sociale_annuel * conversion_parametre_en_euros(period.start.year)
        employeur = parameters(period).retraites.secteur_prive.regimes_complementaires.arrco.prelevements_sociaux.agirc_arrco.employeur
        salarie = parameters(period).retraites.secteur_prive.regimes_complementaires.arrco.prelevements_sociaux.agirc_arrco.salarie
        return (categorie_salarie == TypesCategorieSalarie.prive_non_cadre) * (employeur.agirc_arrco.calc(salaire_de_base, factor=plafond_securite_sociale) + salarie.agirc_arrco.calc(salaire_de_base, factor=plafond_securite_sociale))

    def formula_1962(individu, period, parameters):
        categorie_salarie = individu('categorie_salarie', period)
        salaire_de_base = individu('regime_general_cnav_salaire_de_base', period)
        plafond_securite_sociale = parameters(period).prelevements_sociaux.pss.plafond_securite_sociale_annuel * conversion_parametre_en_euros(period.start.year)
        employeur = parameters(period).retraites.secteur_prive.regimes_complementaires.arrco.prelevements_sociaux.taux_effectifs_salaries_employeurs.employeur
        employeur_non_cadre = employeur.noncadre.arrco.calc(salaire_de_base, factor=plafond_securite_sociale)
        employeur_cadre = employeur.cadre.arrco.calc(salaire_de_base, factor=plafond_securite_sociale)
        salarie = parameters(period).retraites.secteur_prive.regimes_complementaires.arrco.prelevements_sociaux.taux_effectifs_salaries_employeurs.salarie
        salarie_non_cadre = salarie.noncadre.arrco.calc(salaire_de_base, factor=plafond_securite_sociale)
        salarie_cadre = salarie.cadre.arrco.calc(salaire_de_base, factor=plafond_securite_sociale)
        return select([categorie_salarie == TypesCategorieSalarie.prive_non_cadre, (categorie_salarie == TypesCategorieSalarie.prive_cadre) * (period.start.year >= 1976)], [employeur_non_cadre + salarie_non_cadre, employeur_cadre + salarie_cadre], default=0)

class arrco_liquidation_date(Variable):
    value_type = date
    entity = Person
    definition_period = ETERNITY
    label = 'Date de liquidation'
    default_value = date(2250, 12, 31)

class arrco_majoration_pension(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Majoration de pension'

    def formula_2019(individu, period, parameters):
        points_enfants = individu('arrco_points_enfants', period)
        valeur_du_point = parameters(period).retraites.secteur_prive.regimes_complementaires.agirc_arrco.point.valeur_point_en_euros
        plafond = 1000 * valeur_du_point / parameters(2012).retraites.secteur_prive.regimes_complementaires.arrco.point.valeur_point_en_euros
        return where(individu('date_de_naissance', period) >= np.datetime64('1951-08-02'), min_(points_enfants * valeur_du_point, plafond), points_enfants * valeur_du_point)

    def formula_2012(individu, period, parameters):
        points_enfants = individu('arrco_points_enfants', period)
        valeur_du_point = parameters(period).retraites.secteur_prive.regimes_complementaires.arrco.point.valeur_point_en_euros
        plafond = 1000 * valeur_du_point / parameters(2012).retraites.secteur_prive.regimes_complementaires.arrco.point.valeur_point_en_euros
        return where(individu('date_de_naissance', period) >= np.datetime64('1951-08-02'), min_(points_enfants * valeur_du_point, plafond), points_enfants * valeur_du_point)

    def formula_1999(individu, period, parameters):
        points_enfants = individu('arrco_points_enfants', period)
        valeur_du_point = parameters(period).retraites.secteur_prive.regimes_complementaires.arrco.point.valeur_point_en_euros
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

    def formula_2019(individu, period, parameters):
        valeur_du_point = parameters(period).retraites.secteur_prive.regimes_complementaires.agirc_arrco.point.valeur_point_en_euros
        points = individu('arrco_points', period)
        points_minimum_garantis = individu('arrco_points_minimum_garantis', period)
        pension_brute = (points + points_minimum_garantis) * valeur_du_point
        return pension_brute

    def formula(individu, period, parameters):
        valeur_du_point = parameters(period).retraites.secteur_prive.regimes_complementaires.arrco.point.valeur_point_en_euros
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
        last_year = period.last_year
        points_annee_precedente = individu('arrco_points', last_year)
        points_annuels_annee_courante = individu('arrco_points_annuels', period) + individu('arrco_points_a_la_liquidation', period) * (annee_de_liquidation == period.start.year)
        if all(points_annee_precedente == 0):
            return points_annuels_annee_courante
        points = select([period.start.year > annee_de_liquidation, period.start.year <= annee_de_liquidation], [points_annee_precedente, points_annee_precedente + points_annuels_annee_courante])
        return points

class arrco_points_a_la_liquidation(Variable):
    value_type = float
    entity = Person
    definition_period = ETERNITY
    label = 'Points à la liquidation'

class arrco_points_annuels(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Points annuels'

    def formula(individu, period):
        points_emploi_annuels = individu('arrco_points_emploi_annuels', period)
        points_hors_emploi_annuels = individu('arrco_points_hors_emploi_annuels', period)
        return points_emploi_annuels + points_hors_emploi_annuels

class arrco_points_emploi_annuels(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Points annuels en emploi'

    def formula_2019(individu, period, parameters):
        agirc_arrco = parameters(period).retraites.secteur_prive.regimes_complementaires.agirc_arrco
        salaire_de_reference = agirc_arrco.salaire_de_reference.salaire_reference_en_euros
        taux_appel = agirc_arrco.prelevements_sociaux.taux_appel
        cotisation = individu('arrco_cotisation', period)
        return cotisation / salaire_de_reference / taux_appel

    def formula_1962(individu, period, parameters):
        salaire_de_reference = parameters(period).retraites.secteur_prive.regimes_complementaires.arrco.salaire_de_reference.salaire_reference_en_euros
        taux_appel = parameters(period).retraites.secteur_prive.regimes_complementaires.arrco.prelevements_sociaux.taux_appel
        cotisation = individu('arrco_cotisation', period)
        return cotisation / salaire_de_reference / taux_appel

class arrco_points_enfants(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Points enfants'

    def formula(individu, period):
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

class arrco_points_hors_emploi_annuels(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Points annuels hors emploi'

class arrco_points_minimum_garantis(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Points minimum garantis'