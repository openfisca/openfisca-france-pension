"""Abstract regimes definition."""


from datetime import datetime
import numpy as np

from openfisca_core.model_api import *
from openfisca_core.errors.variable_not_found_error import VariableNotFoundError

# Import the Entities specifically defined for this tax and benefit system
from openfisca_france_pension.entities import Person


class AbstractRegime(object):
    name = None
    variable_prefix = None
    parameters = None

    class cotisation(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "cotisation retraite employeur"

        def formula(individu, period):
            return individu("regime_name_cotisation_employeur", period) + individu("regime_name_cotisation_salarie", period)

    class liquidation_date(Variable):
        value_type = date
        entity = Person
        definition_period = ETERNITY
        label = 'Date de liquidation'
        default_value = datetime.max.date()

    class cotisation_employeur(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "cotisation retraite employeur"

        def formula(individu, period, parameters):
            NotImplementedError

    class cotisation_salarie(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "cotisation retraite employeur"

        def formula(individu, period, parameters):
            NotImplementedError

    class majoration_pension(Variable):
        value_type = int
        entity = Person
        definition_period = MONTH
        label = "Majoration de pension"

        def formula(individu, period, parameters):
            NotImplementedError

    class pension(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Pension"

        def formula(individu, period, parameters):
            NotImplementedError

    class pension_brute(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Pension brute"

        def formula(individu, period, parameters):
            NotImplementedError

    class pension_servie(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Pension servie"

        def formula(individu, period, parameters):
            NotImplementedError


class AbstractRegimeDeBase(AbstractRegime):
    name = "Régime de base"
    variable_prefix = "regime_de_base"
    parameters = "regime_de_base"

    class decote(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Décote"

    class duree_assurance(Variable):
        value_type = int
        entity = Person
        definition_period = YEAR
        label = "Durée d'assurance (en trimestres)"

    class duree_assurance_cotisee(Variable):
        value_type = int
        entity = Person
        definition_period = YEAR
        label = "Durée d'assurance cotisée donc hors majoration de durée d'assurance (en trimestres cotisés jusqu'à l'année considérée)"

    class duree_assurance_assimilee_annuelle(Variable):
        value_type = int
        entity = Person
        definition_period = YEAR
        label = "Durée d'assurance validée au titre des périodes assimilées (en trimestres cotisés seulement l'année considérée)"

    class duree_assurance_travail_annuelle(Variable):
        value_type = int
        entity = Person
        definition_period = YEAR
        label = "Durée d'assurance annuelle pour les périodes cotisées ou faisant l'objet d'un report de salaire au compte (en trimestres cotisés seulement l'année considérée)"

    class majoration_pension(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Majoration de pension"

    class majoration_pension_servie(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Majoration de pension servie"

        def formula(individu, period, parameters):
            annee_de_liquidation = individu('regime_name_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970
            # Raccouci pour arrêter les calculs dans le passé quand toutes les liquidations ont lieu dans le futur
            if all(annee_de_liquidation > period.start.year):
                return individu.empty_array()
            last_year = period.start.period('year').offset(-1)
            majoration_pension_servie_annee_precedente = individu('regime_name_majoration_pension_servie', last_year)
            revalorisation = parameters(period).regime_name.reval_p.coefficient
            majoration_pension = individu('regime_name_majoration_pension', period)
            return revalorise(
                majoration_pension_servie_annee_precedente,
                majoration_pension,
                annee_de_liquidation,
                revalorisation,
                period,
                )

    class pension(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Pension"

        def formula(individu, period):
            pension_brute = individu('regime_name_pension_brute', period)
            majoration_pension = individu('regime_name_majoration_pension', period)
            return pension_brute + majoration_pension

    class pension_avant_minimum_et_plafonnement(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Pension brute"

        def formula(individu, period):
            coefficient_de_proratisation = individu('regime_name_coefficient_de_proratisation', period)
            salaire_de_reference = individu('regime_name_salaire_de_reference', period)
            taux_de_liquidation = individu('regime_name_taux_de_liquidation', period)
            return coefficient_de_proratisation * salaire_de_reference * taux_de_liquidation

    class pension_brute_servie(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Pension servie"

        def formula(individu, period, parameters):
            annee_de_liquidation = individu('regime_name_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970
            # Raccouci pour arrêter les calculs dans le passé quand toutes les liquidations ont lieu dans le futur
            if all(annee_de_liquidation > period.start.year):
                return individu.empty_array()
            last_year = period.start.period('year').offset(-1)
            pension_brute_servie_annee_precedente = individu('regime_name_pension_brute_servie', last_year)
            revalorisation = parameters(period).regime_name.reval_p.coefficient
            pension_brute = individu('regime_name_pension_brute', period)
            return revalorise(
                pension_brute_servie_annee_precedente,
                pension_brute,
                annee_de_liquidation,
                revalorisation,
                period,
                )

    class pension_servie(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Pension servie"

        def formula(individu, period, parameters):
            annee_de_liquidation = individu('regime_name_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970
            # Raccouci pour arrêter les calculs dans le passé quand toutes les liquidations ont lieu dans le futur
            if all(annee_de_liquidation > period.start.year):
                return individu.empty_array()
            last_year = period.start.period('year').offset(-1)
            pension_servie_annee_precedente = individu('regime_name_pension_servie', last_year)
            revalorisation = parameters(period).regime_name.reval_p.coefficient
            pension = individu('regime_name_pension', period)
            return revalorise(
                pension_servie_annee_precedente,
                pension,
                annee_de_liquidation,
                revalorisation,
                period,
                )

    class salaire_de_reference(Variable):
        value_type = float
        entity = Person
        definition_period = ETERNITY
        label = "Salaire de référence"

    class surcote(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Surcote"

    class taux_de_liquidation(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Taux de liquidation de la pension"

        def formula(individu, period, parameters):
            decote = individu('regime_name_decote', period)
            surcote = individu('regime_name_surcote', period)
            taux_plein = parameters(period).regime_name.taux_plein.taux_plein
            return taux_plein * (1 - decote + surcote)


class AbstractRegimeComplementaire(AbstractRegime):

    class coefficient_de_minoration(Variable):
        value_type = float
        default_value = 1.0
        entity = Person
        definition_period = YEAR
        label = "Coefficient de minoration"

    class majoration_pension(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Majoration de pension"

        def formula_2012(individu, period, parameters):
            points_enfants = individu('regime_name_points_enfants', period)
            valeur_du_point = parameters(period).regime_name.point.valeur_point_en_euros
            points_enfants = individu('regime_name_points_enfants', period)
            valeur_du_point = parameters(period).regime_name.point.valeur_point_en_euros
            # Plafond fixé à 1000 € en 2012 et évoluant comme le point
            plafond = 1000 * valeur_du_point / parameters(2012).regime_name.point.valeur_point_en_euros
            return where(
                individu('date_de_naissance', period) >= np.datetime64("1951-08-02"),
                min_(points_enfants * valeur_du_point, plafond),
                points_enfants * valeur_du_point
                )

        def formula_1999(individu, period, parameters):
            points_enfants = individu('regime_name_points_enfants', period)
            valeur_du_point = parameters(period).regime_name.point.valeur_point_en_euros
            return points_enfants * valeur_du_point

        def formula(individu, period, parameters):
            return individu.empty_array()

    class majoration_pension_servie(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Majoration de pension servie"

        def formula(individu, period, parameters):
            annee_de_liquidation = individu('regime_name_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970
            # Raccouci pour arrêter les calculs dans le passé quand toutes les liquidations ont lieu dans le futur
            if all(period.start.year < annee_de_liquidation):
                return individu.empty_array()
            majoration_pension = individu('regime_name_majoration_pension', period)
            return revalorise(majoration_pension, majoration_pension, annee_de_liquidation, 1, period)

    class pension(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Pension"

        def formula(individu, period):
            pension_brute = individu("regime_name_pension_brute", period)
            majoration_pension = individu("regime_name_majoration_pension", period)
            coefficient_de_minoration = individu("regime_name_coefficient_de_minoration", period)
            try:
                decote = individu("regime_name_decote", period)
            except VariableNotFoundError:
                decote = 0
            pension = (
                (pension_brute + majoration_pension)
                * (1 - decote)
                * coefficient_de_minoration
                )
            return pension

    class pension_brute(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Pension brute"

        def formula(individu, period, parameters):
            valeur_du_point = parameters(period).regime_name.point.valeur_point_en_euros
            points = individu("regime_name_points", period)
            points_minimum_garantis = individu("regime_name_points_minimum_garantis", period)
            pension_brute = (points + points_minimum_garantis) * valeur_du_point
            return pension_brute

    class pension_brute_servie(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Pension servie"

        def formula(individu, period, parameters):
            annee_de_liquidation = individu('regime_name_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970
            # Raccouci pour arrêter les calculs dans le passé quand toutes les liquidations ont lieu dans le futur
            if all(period.start.year < annee_de_liquidation):
                return individu.empty_array()
            pension_brute = individu('regime_name_pension_brute', period)
            return revalorise(pension_brute, pension_brute, annee_de_liquidation, 1, period)

    class pension_servie(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Pension servie"

        def formula(individu, period, parameters):
            annee_de_liquidation = individu('regime_name_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970

            # Raccouci pour arrêter les calculs dans le passé quand toutes les liquidations ont lieu dans le futur
            if all(period.start.year < annee_de_liquidation):
                return individu.empty_array()

            pension = individu('regime_name_pension', period)
            return revalorise(pension, pension, annee_de_liquidation, 1, period)

    class points(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Points"

        def formula(individu, period, parameters):
            annee_de_liquidation = individu('regime_name_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970
            last_year = period.start.period('year').offset(-1)
            points_annee_precedente = individu('regime_name_points', last_year)

            salaire_de_reference = parameters(period).regime_name.salaire_de_reference.salaire_reference_en_euros
            taux_appel = parameters(period).regime_name.prelevements_sociaux.taux_appel
            cotisation = individu("regime_name_cotisation", period)
            points_annee_courante = cotisation / salaire_de_reference / taux_appel

            if all(points_annee_precedente == 0):
                return points_annee_courante

            points = select(
                [
                    period.start.year > annee_de_liquidation,
                    period.start.year <= annee_de_liquidation,
                    ],
                [
                    points_annee_precedente,
                    points_annee_precedente + points_annee_courante,
                    ]
                )

            return points

    class points_enfants_a_charge(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Points enfants à charge"

    class points_enfants_nes_et_eleves(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Points enfants nés et élevés"

    class points_enfants(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Points enfants"

        def formula(individu, period, parameters):
            """
            Deux types de majorations pour enfants peuvent s'appliquer :
                - pour enfant à charge au moment du départ en retraite
                - pour enfant nés et élevés en cours de carrière (majoration sur la totalité des droits acquis)
                C'est la plus avantageuse qui s'applique.
            """
            points_enfants_a_charge = individu('regime_name_points_enfants_a_charge', period)
            points_enfants_nes_et_eleves = individu('regime_name_points_enfants_nes_et_eleves', period)
            return max_(points_enfants_a_charge, points_enfants_nes_et_eleves)

    class points_minimum_garantis(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Points minimum garantis"


def revalorise(variable_servie_annee_precedente, variable_originale, annee_de_liquidation, revalorisation, period):
    return select(
        [
            annee_de_liquidation > period.start.year,
            annee_de_liquidation == period.start.year,
            annee_de_liquidation < period.start.year,
            ],
        [
            0,
            variable_originale,
            variable_servie_annee_precedente * revalorisation
            ]
        )
