"""Abstract regimes definition."""


from datetime import datetime


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
        label = "Durée d'assurance cotisée (en trimestres cotisés)"

    class majoration_pension(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Majoration de pension"

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

            pension_servie = select(
                [
                    annee_de_liquidation > period.start.year,
                    annee_de_liquidation == period.start.year,
                    annee_de_liquidation < period.start.year,
                    ],
                [
                    0,
                    pension,
                    pension_servie_annee_precedente * revalorisation
                    ]
                )

            return pension_servie

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

#     def nb_points_enf(self, data, nombre_points):
#         ''' Application de la majoration pour enfants à charge. Deux types de
#         majorations peuvent s'appliquer :
#           - pour enfant à charge au moment du départ en retraite
#           - pour enfant nés et élevés en cours de carrière (majoration sur la totalité des droits acquis)
#         C'est la plus avantageuse qui s'applique.'''
#         P = reduce(getattr, self.param_name.split('.'), self.P)
#         P_long = reduce(getattr, self.param_name.split('.'), self.P_longit).maj_enf
#         nb_pac = data.info_ind['nb_pac'].copy()
#         nb_born = data.info_ind['nb_enf_all'].copy()
#         # 1- Calcul des points pour enfants à charge
#         taux_pac = P.maj_enf.pac.taux
#         points_pac = nombre_points.sum(axis=1) * taux_pac * nb_pac

#         # 2- Calcul des points pour enfants nés ou élevés
#         points_born = zeros(len(nb_pac))
#         nb_enf_maj = zeros(len(nb_pac))
#         for num_dispo in [0, 1]:
#             P_dispositif = getattr(P.maj_enf.born, 'dispositif' + str(num_dispo))
#             selected_dates = getattr(P_long.born, 'dispositif' + str(num_dispo)).dates
#             taux_dispositif = P_dispositif.taux
#             nb_enf_min = P_dispositif.nb_enf_min
#             nb_points_dates = multiply(nombre_points, selected_dates).sum(axis=1)
#             nb_points_enf = nb_points_dates * taux_dispositif * (nb_born >= nb_enf_min)
#             if hasattr(P_dispositif, 'taux_maj'):
#                 taux_maj = P_dispositif.taux_maj
#                 plaf_nb = P_dispositif.nb_enf_count
#                 nb_enf_maj = maximum(minimum(nb_born, plaf_nb) - nb_enf_min, 0)
#                 nb_points_enf += nb_enf_maj * taux_maj * nb_points_dates

#             points_born += nb_points_enf
#         # Retourne la situation la plus avantageuse
#         return maximum(points_born, points_pac)

#     def majoration_pension(self, nb_points_enf):
#         P = reduce(getattr, self.param_name.split('.'), self.P)
#         val_point = P.val_point
#         return nb_points_enf * val_point

    class majoration_pension(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Majoration de pension"

    class points_minimum_garantis(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Points minimum garantis"

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

            pension = individu('regime_name_pension', period)
            pension_servie = select(
                [
                    annee_de_liquidation >= period.start.year,
                    annee_de_liquidation < period.start.year,
                    ],
                [
                    pension,
                    0
                    ]
                )
            return pension_servie
