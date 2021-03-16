"""Abstract regimesdefinition."""

from openfisca_core.model_api import *

# Import the Entities specifically defined for this tax and benefit system
from openfisca_france_pension.entities import Household, Person


class AbstractRegime(object):
    name = None
    variable_prefix = None
    parameters = None

    class surcote_debut_date(Variable):
        value_type = date
        entity = Person
        definition_period = YEAR
        label = "Date du début de la surcote"

    class decote_annulation_date(Variable):
        value_type = date
        entity = Person
        definition_period = YEAR
        label = "Date d'annulation de la décote'"

    class taux_plein_date(Variable):
        value_type = date
        entity = Person
        definition_period = YEAR
        label = "Date du taux plein"

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

    class cotisation_retraite(Variable):
        value_type = float
        entity = Person
        definition_period = MONTH
        label = "cotisation retraite"

        def formula(individu, period, parameters):
            salaire_de_base = individu('salaire_de_base', period)
            taux = parameters(period).regime_name.cotisation.taux
            return salaire_de_base * taux


class AbstractRegimeDeBase(AbstractRegime):
    name = "Régime de base"
    variable_prefix = "regime_de_base"
    parameters = "regime_de_base"

    class salaire_de_reference(Variable):
        value_type = float
        entity = Person
        definition_period = ETERNITY
        label = "Salaire de référence"

    class trimestres(Variable):
        value_type = int
        entity = Person
        definition_period = YEAR
        label = "Trimestres"

    class majoration_pension(Variable):
        value_type = int
        entity = Person
        definition_period = MONTH
        label = "Majoration de pension"

    class decote(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Décote"

    class surcote(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Surcote"

    class pension_brute(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Pension brute"

        def formula(individu, period, parameters):
            coefficient_de_proratisation = individu('regime_name_coefficient_de_proratisation', period)
            salaire_de_reference = individu('regime_name_salaire_de_reference', period)
            taux_de_liquidation = individu('regime_name_taux_de_liquidation', period)
            return coefficient_de_proratisation * salaire_de_reference * taux_de_liquidation

    class pension(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Pension"

        def formula(individu, period):
            pension_brute = individu('regime_name_pension_brute', period)
            majoration_pension = individu('regime_name_majoration_pension', period)
            return pension_brute + majoration_pension


# class RegimeComplementaires(Regime):
#     def nombre_points(self, data, sali_for_regime):
#         ''' Détermine le nombre de point à liquidation de la pension dans les
#         régimes complémentaires (pour l'instant Ok pour ARRCO/AGIRC)
#         Pour calculer ces points, il faut diviser la cotisation annuelle
#         ouvrant des droits par le salaire de référence de l'année concernée
#         et multiplier par le taux d'acquisition des points'''
#         Plong_regime = reduce(getattr, self.param_name.split('.'), self.P_longit)
#         # getattr(self.P_longit.prive.complementaire,  self.name)
#         salref = Plong_regime.sal_ref
#         taux_cot = Plong_regime.taux_cot_moy
#         sali_plaf = sali_for_regime
#         assert len(salref) == sali_plaf.shape[1] == len(taux_cot)
#         nombre_points = zeros(sali_plaf.shape)
#         for ix_year in range(sali_plaf.shape[1]):
#             if salref[ix_year] > 0:
#                 nombre_points[:, ix_year] = (taux_cot[ix_year].calc(sali_plaf[:, ix_year]) / salref[ix_year])
#         nb_points_by_year = nombre_points.round(2)
#         return nb_points_by_year

#     def coefficient_age(self, data, nb_trimesters, trim_decote):
#         ''' TODO: add surcote  pour avant 1955 '''
#         P = reduce(getattr, self.param_name.split('.'), self.P)
#         coef_mino = P.coef_mino
#         agem = data.info_ind['agem']
#         # print data.info_ind.dtype.names
#         age_annulation_decote = self.P.prive.RG.decote.age_null
#         diff_age = divide(age_annulation_decote - agem, 12) * (age_annulation_decote > agem)
#         if P.cond_taux_plein == 1:
#             diff_trim = minimum(diff_age, divide(trim_decote, 4))
#         coeff_min = zeros(len(agem))
#         for nb_annees, coef_mino in coef_mino._tranches:
#             coeff_min += (diff_trim == nb_annees) * coef_mino
#         coeff_min += P.coeff_maj * diff_age
#         if P.cond_taux_plein == 1:
#             # Dans ce cas, la minoration ne s'applique que si la durée de cotisation
#             # au régime général est inférieure à celle requise pour le taux plein
#             n_trim = self.P.prive.RG.plein.n_trim
#             # la bonne formule est la suivante :
#             coeff_min = coeff_min * (n_trim > nb_trimesters) + (n_trim <= nb_trimesters)
#             # mais on a ça...
#             coeff_min = 1
#         return coeff_min

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

#     def nb_points_cot(self, nombre_points):
#         return nombre_points.sum(axis=1)

#     def pension(self, data, coefficient_age, pension_brute_b,
#                 majoration_pension, trim_decote):
#         ''' le régime Arrco ne tient pas compte du coefficient de
#         minoration pour le calcul des majorations pour enfants '''
#         P = reduce(getattr, self.param_name.split('.'), self.P)
#         pension = pension_brute_b + majoration_pension
#         decote = trim_decote * P.taux_decote
#         pension = (1 - decote) * pension
#         return pension * coefficient_age

#     def pension_brute(self, nb_points, minimum_points):
#         P = reduce(getattr, self.param_name.split('.'), self.P)
#         val_point = P.val_point
#         pension_brute = (nb_points + minimum_points) * val_point
#         return pension_brute

#     def cotisations(self, sali_for_regime):
#         ''' Calcul des cotisations passées par année'''
#         sali = sali_for_regime.copy()
#         assert self.P_cot is not None, 'self.P_cot should be not None'
#         Pcot_regime = reduce(getattr, self.param_name.split('.'), self.P_cot)
#         # getattr(self.P_longit.prive.complementaire,  self.name)
#         taux_pat = Pcot_regime.cot_pat
#         taux_sal = Pcot_regime.cot_sal
#         assert len(taux_pat) == sali.shape[1] == len(taux_sal)
#         cot_sal_by_year = zeros(sali.shape)
#         cot_pat_by_year = zeros(sali.shape)
#         for ix_year in range(sali.shape[1]):
#             cot_sal_by_year[:, ix_year] = taux_sal[ix_year].calc(sali[:, ix_year])
#             cot_pat_by_year[:, ix_year] = taux_pat[ix_year].calc(sali[:, ix_year])
#         if not self.sal_nominal:
#             revalo = self.P_longit.prive.RG.revalo
#             revalo = array(revalo)
#             for i in range(1, len(revalo)):
#                 revalo[:i] *= revalo[i]
#             cot_sal_by_year = multiply(cot_sal_by_year, revalo)
#             cot_pat_by_year = multiply(cot_pat_by_year, revalo)
#         return {'sal': cot_sal_by_year, 'pat': cot_pat_by_year}
