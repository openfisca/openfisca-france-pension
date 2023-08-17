"""Abstract regimes definition."""


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

        def formula(individu, period, parameters):
            NotImplementedError

    class liquidation_date(Variable):
        value_type = date
        entity = Person
        definition_period = ETERNITY
        label = 'Date de liquidation'
        default_value = date(2250, 12, 31)

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


class AbstractRegimeEnAnnuites(AbstractRegime):
    name = "Régime en annuités"
    variable_prefix = "regime_en_annuites"
    parameters = "regime_en_annuites"

    class decote(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Décote"

    class duree_assurance_chomage_annuelle(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Durée d'assurance au titre du chômage (en trimestres cotisés jusqu'à l'année considérée)"

    class duree_assurance_maladie_annuelle(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Durée d'assurance au titre de la maladie (en trimestres validés l'année considérée)"

    class duree_assurance_accident_du_travail_annuelle(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Durée d'assurance au titre des accidents du travail (en trimestres validés l'année considérée)"

    class duree_assurance_invalidite_annuelle(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Durée d'assurance au titre de l'invalidté (en trimestres validés l'année considérée)"

    class duree_assurance_rachetee_annuelle(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Durée d'assurance rachetée l'année considérée)"

    class duree_assurance_service_national_annuelle(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Durée d'assurance au titre du service national (en trimestres validés l'année considérée)"

    class duree_assurance_autre_annuelle(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Durée d'assurance au titre des autres périodes assimilées (en trimestres validés l'année considérée)"

    class duree_assurance_periode_assimilee(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Durée d'assurance pour période assimilée cumullée "

    class majoration_duree_assurance(Variable):
        value_type = float
        entity = Person
        definition_period = ETERNITY
        label = "Majoration de durée d'assurance"

        def formula(individu, period):
            return (
                individu("regime_name_majoration_duree_assurance_enfant", period)
                + individu("regime_name_majoration_duree_assurance_autre", period)
                )

    class majoration_duree_assurance_autre(Variable):
        value_type = float
        entity = Person
        definition_period = ETERNITY
        label = "Majoration de durée d'assurance autre que celle attribuée au motif des enfants"

    class majoration_pension(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Majoration de pension"

    class majoration_pension_au_31_decembre(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Majoration de pension au 31 décembre"

        def formula(individu, period, parameters):
            annee_de_liquidation = individu('regime_name_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970
            # Raccouci pour arrêter les calculs dans le passé quand toutes les liquidations ont lieu dans le futur
            if all(annee_de_liquidation > period.start.year):
                return individu.empty_array()
            last_year = period.last_year
            majoration_pension_au_31_decembre_annee_precedente = individu('regime_name_majoration_pension_au_31_decembre', last_year)
            revalorisation = parameters(period).regime_name.revalorisation_pension_au_31_decembre
            majoration_pension = individu('regime_name_majoration_pension', period)
            return revalorise(
                majoration_pension_au_31_decembre_annee_precedente,
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

    class pension_au_31_decembre(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Pension"

        def formula(individu, period):
            pension_brute_au_31_decembre = individu('regime_name_pension_brute_au_31_decembre', period)
            majoration_pension_au_31_decembre = individu('regime_name_majoration_pension_au_31_decembre', period)
            return pension_brute_au_31_decembre + majoration_pension_au_31_decembre

    class pension_brute_au_31_decembre(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Pension brute au 31 décembre"

        def formula(individu, period, parameters):
            annee_de_liquidation = individu('regime_name_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970
            # Raccouci pour arrêter les calculs dans le passé quand toutes les liquidations ont lieu dans le futur
            if all(period.start.year < annee_de_liquidation):
                return individu.empty_array()
            last_year = period.last_year
            pension_brute_au_31_decembre_annee_precedente = individu('regime_name_pension_brute_au_31_decembre', last_year)
            revalorisation = parameters(period).regime_name.revalorisation_pension_au_31_decembre
            pension_brute = individu('regime_name_pension_brute', period)
            return revalorise(
                pension_brute_au_31_decembre_annee_precedente,
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
            last_year = period.last_year
            pension_au_31_decembre_annee_precedente = individu('regime_name_pension_au_31_decembre', last_year)
            revalorisation = parameters(period).regime_name.revalarisation_pension_servie
            pension = individu('regime_name_pension_au_31_decembre', period)
            return revalorise(
                pension_au_31_decembre_annee_precedente,
                pension,
                annee_de_liquidation,
                revalorisation,
                period,
                )

    class salaire_de_base(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = 'Salaire de base (salaire brut)'
        set_input = set_input_divide_by_period

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


class AbstractRegimeEnPoints(AbstractRegime):

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

    class majoration_pension_au_31_decembre(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Majoration de pension au 31 décembre"

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

    class pension_brute_au_31_decembre(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Pension brute au 31 décembre"

        def formula(individu, period, parameters):
            annee_de_liquidation = individu('regime_name_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970
            # Raccouci pour arrêter les calculs dans le passé quand toutes les liquidations ont lieu dans le futur
            if all(period.start.year < annee_de_liquidation):
                return individu.empty_array()
            pension_brute = individu('regime_name_pension_brute', period)
            return revalorise(pension_brute, pension_brute, annee_de_liquidation, 1, period)

    class pension_au_31_decembre(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Pension brute au 31 décembre"

        def formula(individu, period, parameters):
            annee_de_liquidation = individu('regime_name_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970
            # Raccouci pour arrêter les calculs dans le passé quand toutes les liquidations ont lieu dans le futur
            if all(period.start.year < annee_de_liquidation):
                return individu.empty_array()
            pension = individu('regime_name_pension', period)
            return revalorise(pension, pension, annee_de_liquidation, 1, period)

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
            last_year = period.last_year
            points_annee_precedente = individu('regime_name_points', last_year)
            points_annuels_annee_courante = (
                individu('regime_name_points_annuels', period)
                + individu('regime_name_points_a_la_liquidation', period) * (annee_de_liquidation == period.start.year)
                )

            if all(points_annee_precedente == 0):
                return points_annuels_annee_courante

            points = select(
                [
                    period.start.year > annee_de_liquidation,
                    period.start.year <= annee_de_liquidation,
                    ],
                [
                    points_annee_precedente,
                    points_annee_precedente + points_annuels_annee_courante
                    ]
                )

            return points

    class points_a_la_liquidation(Variable):
        value_type = float
        entity = Person
        definition_period = ETERNITY
        label = "Points à la liquidation"

    class points_minimum_garantis(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Points minimum garantis"


def revalorise(variable_31_decembre_annee_precedente, variable_originale, annee_de_liquidation, revalorisation, period):
    return select(
        [
            annee_de_liquidation > period.start.year,
            annee_de_liquidation == period.start.year,
            annee_de_liquidation < period.start.year,
            ],
        [
            0,
            variable_originale,
            variable_31_decembre_annee_precedente * revalorisation
            ]
        )
