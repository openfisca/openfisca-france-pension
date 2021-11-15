"""Abstract regimes definition."""
from datetime import datetime
from openfisca_core.model_api import *
from openfisca_core.errors.variable_not_found_error import VariableNotFoundError
from openfisca_france_pension.entities import Person
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

class agirc_pension_servie(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Pension servie'

    def formula(individu, period, parameters):
        annee_de_liquidation = individu('agirc_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970
        if all(annee_de_liquidation > period.start.year):
            return individu.empty_array()
        pension = individu('agirc_pension', period)
        pension_servie = select([annee_de_liquidation >= period.start.year, annee_de_liquidation < period.start.year], [pension, 0])
        return pension_servie

class agirc_points(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Points'

    def formula(individu, period, parameters):
        annee_de_liquidation = individu('agirc_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970
        last_year = period.start.period('year').offset(-1)
        points_annee_precedente = individu('agirc_points', last_year)
        salaire_de_reference = parameters(period).secteur_prive.regimes_complementaires.agirc.salaire_de_reference.salaire_reference_en_euros
        taux_appel = parameters(period).secteur_prive.regimes_complementaires.agirc.prelevements_sociaux.taux_appel
        cotisation = individu('agirc_cotisation', period)
        points_annee_courante = cotisation / salaire_de_reference / taux_appel
        if all(points_annee_precedente == 0):
            return points_annee_courante
        points = select([period.start.year > annee_de_liquidation, period.start.year <= annee_de_liquidation], [points_annee_precedente, points_annee_precedente + points_annee_courante])
        return points

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

class arrco_pension_brute(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Pension brute'

    def formula_1999(individu, period, parameters):
        valeur_du_point = parameters(period).secteur_prive.regimes_complementaires.arrco.point.valeur_point_en_euros
        points = individu('arrco_points', period)
        points_minimum_garantis = individu('arrco_points_minimum_garantis', period)
        pension_brute = (points + points_minimum_garantis) * valeur_du_point
        return pension_brute

    def formula_1957(individu, period, parameters):
        valeur_du_point = parameters(period).secteur_prive.regimes_complementaires.unirs.point.valeur_point_en_euros
        points = individu('arrco_points', period)
        points_minimum_garantis = individu('arrco_points_minimum_garantis', period)
        pension_brute = (points + points_minimum_garantis) * valeur_du_point
        return pension_brute

class arrco_pension_servie(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Pension servie'

    def formula(individu, period, parameters):
        annee_de_liquidation = individu('arrco_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970
        if all(annee_de_liquidation > period.start.year):
            return individu.empty_array()
        pension = individu('arrco_pension', period)
        pension_servie = select([annee_de_liquidation >= period.start.year, annee_de_liquidation < period.start.year], [pension, 0])
        return pension_servie

class arrco_points(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Points'

    def formula_1999(individu, period, parameters):
        salaire_de_reference = parameters(period).secteur_prive.regimes_complementaires.arrco.salaire_de_reference.salaire_reference_en_euros
        taux_appel = parameters(period).secteur_prive.regimes_complementaires.arrco.prelevements_sociaux.taux_appel
        cotisation = individu('arrco_cotisation', period)
        return cotisation / salaire_de_reference / taux_appel

    def formula_1957(individu, period, parameters):
        salaire_de_reference = parameters(period).secteur_prive.regimes_complementaires.unirs.salaire_de_reference.salaire_reference_en_euros
        taux_appel = parameters(period).secteur_prive.regimes_complementaires.arrco.prelevements_sociaux.taux_appel
        cotisation = individu('arrco_cotisation', period)
        return cotisation / salaire_de_reference / taux_appel

class arrco_points_minimum_garantis(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Points minimum garantis'