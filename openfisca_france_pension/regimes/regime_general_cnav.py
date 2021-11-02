"""Régime de base du secteur privé: régime général de la CNAV."""

import functools

import numpy as np

from openfisca_core.model_api import *
from openfisca_core.parameters import ParameterNotFound
from openfisca_core.periods import YEAR
from openfisca_core.variables import Variable

from openfisca_france_pension.entities import Person
from openfisca_france_pension.regimes.regime import AbstractRegimeDeBase
from openfisca_france_pension.tools import mean_over_k_nonzero_largest
from openfisca_france_pension.variables.hors_regime import TypesCategorieSalarie
from openfisca_france_pension.variables.hors_regime import TypesRaisonDepartTauxPleinAnticipe


def compute_salaire_de_reference(mean_over_largest, arr, salaire_de_refererence, filter):
    salaire_de_refererence[filter] = np.apply_along_axis(
        mean_over_largest,
        axis = 0,
        arr = arr,
        )


def make_mean_over_largest(k):
    def mean_over_largest(vector):
        return mean_over_k_nonzero_largest(vector, k = int(k))

    return mean_over_largest


class RegimeGeneralCnav(AbstractRegimeDeBase):
    name = "Régime de base du secteur privé: régime général de la Cnav"
    variable_prefix = "regime_general_cnav"
    parameters_prefix = "secteur_prive.regime_general_cnav"

    class age_annulation_decote_droit_commun(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Âge auquel un individu peut partir au taux plein hors départ anticipé"

        def formula_2011_07_01(individu, period, parameters):
            date_de_naissance = individu('date_de_naissance', period)
            aad_annee = parameters(period).regime_name.aad.age_annulation_decote_en_fonction_date_naissance[date_de_naissance].annee
            aad_mois = parameters(period).regime_name.aad.age_annulation_decote_en_fonction_date_naissance[date_de_naissance].mois
            return aad_annee + aad_mois / 12

        def formula_1945(individu, period, parameters):
            return parameters(period).regime_name.aad.age_annulation_decote_en_fonction_date_naissance.ne_avant_1951_07_01.annee

    class age_annulation_decote(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Âge auquel un individu peut partir au taux plein (éventuellement de façon anticipée)"
        # default_value = 65 can be kept and firs formula removed
        # not clean, clear nor readable but may save memory

        def formula_1976_07_01(individu, period, parameters):
            # TODO use legislative parameter
            aad_anciens_deportes = parameters(period).regime_name.aad.age_annulation_decote_anciens_deportes
            aad_inaptitude = parameters(period).regime_name.aad.age_annulation_decote_inaptitude
            aad_anciens_anciens_combattants = parameters(period).regime_name.aad.age_annulation_decote_anciens_combattants
            aad_anciens_travailleurs_manuels = parameters(period).regime_name.aad.travailleurs_manuels.age_annulation_decote
            aad_droit_commun = individu("regime_name_age_annulation_decote_droit_commun", period)
            # TODO Ajouter durée d'assurance pour les travailleurs manuels
            raison_depart_taux_plein_anticipe = individu("raison_depart_taux_plein_anticipe", period)
            aad = switch(
                raison_depart_taux_plein_anticipe,
                {
                    TypesRaisonDepartTauxPleinAnticipe.non_concerne: aad_droit_commun,
                    TypesRaisonDepartTauxPleinAnticipe.ancien_deporte: aad_anciens_deportes,
                    TypesRaisonDepartTauxPleinAnticipe.inapte: aad_inaptitude,
                    TypesRaisonDepartTauxPleinAnticipe.ancien_combattant: aad_anciens_anciens_combattants,
                    TypesRaisonDepartTauxPleinAnticipe.travailleur_manuel: aad_anciens_travailleurs_manuels,
                    }
                )
            return aad

        def formula_1974_01_01(individu, period, parameters):
            # TODO use legislative parameter
            aad_droit_commun = 65
            aad_anciens_deportes = parameters(period).regime_name.aad.age_annulation_decote_anciens_deportes
            aad_inaptitude = parameters(period).regime_name.aad.age_annulation_decote_inaptitude
            aad_anciens_anciens_combattants = parameters(period).regime_name.aad.age_annulation_decote_anciens_combattants

            raison_depart_taux_plein_anticipe = individu("raison_depart_taux_plein_anticipe", period)
            aad = switch(
                raison_depart_taux_plein_anticipe,
                {
                    TypesRaisonDepartTauxPleinAnticipe.non_concerne: aad_droit_commun,
                    TypesRaisonDepartTauxPleinAnticipe.ancien_deporte: aad_anciens_deportes,
                    TypesRaisonDepartTauxPleinAnticipe.inapte: aad_inaptitude,
                    TypesRaisonDepartTauxPleinAnticipe.ancien_combattant: aad_anciens_anciens_combattants,
                    }
                )
            return aad

        def formula_1972_01_01(individu, period, parameters):
            # TODO use legislative parameter
            aad_droit_commun = 65
            aad_anciens_deportes = parameters(period).regime_name.aad.age_annulation_decote_anciens_deportes
            aad_inaptitude = parameters(period).regime_name.aad.age_annulation_decote_inaptitude
            raison_depart_taux_plein_anticipe = individu("raison_depart_taux_plein_anticipe", period)
            aad = switch(
                raison_depart_taux_plein_anticipe,
                {
                    TypesRaisonDepartTauxPleinAnticipe.non_concerne: aad_droit_commun,
                    TypesRaisonDepartTauxPleinAnticipe.ancien_deporte: aad_anciens_deportes,
                    TypesRaisonDepartTauxPleinAnticipe.inapte: aad_inaptitude,
                    }
                )
            return aad

        def formula_1965_05_01(individu, period, parameters):
            # TODO use legislative parameter
            aad_droit_commun = 65
            aad_anciens_deportes = parameters(period).regime_name.aad.age_annulation_decote_anciens_deportes
            raison_depart_taux_plein_anticipe = individu("raison_depart_taux_plein_anticipe", period)
            aad = switch(
                raison_depart_taux_plein_anticipe,
                {
                    TypesRaisonDepartTauxPleinAnticipe.non_concerne: aad_droit_commun,
                    TypesRaisonDepartTauxPleinAnticipe.ancien_deporte: aad_anciens_deportes,
                    }
                )
            return aad

        def formula_1945(individu, period, parameters):
            # TODO use legislative parameter
            aad_droit_commun = 65
            return aad_droit_commun

    class duree_assurance(Variable):
        value_type = int
        entity = Person
        definition_period = YEAR
        label = "Durée d'assurance (trimestres validés au régime général)"

        def formula(individu, period, parameters):
            duree_assurance_cotisee = individu("regime_name_duree_assurance_cotisee", period)
            majoration_duree_assurance = individu("regime_name_majoration_duree_assurance", period)
            return duree_assurance_cotisee + majoration_duree_assurance

    class duree_assurance_cotisee(Variable):
        value_type = int
        entity = Person
        definition_period = YEAR
        label = "Durée d'assurance cotisée (trimestres cotisés au régime général)"

        def formula(individu, period, parameters):
            salaire_de_base = individu("salaire_de_base", period)
            try:
                salaire_validant_un_trimestre = parameters(period).regime_name.salval.salaire_validant_trimestre.metropole
            except ParameterNotFound:
                import openfisca_core.periods as periods
                salaire_validant_un_trimestre = parameters(periods.period(1930)).regime_name.salval.salaire_validant_trimestre.metropole
            trimestres_valides_avant_cette_annee = individu("regime_name_duree_assurance_cotisee", period.last_year)
            trimestres_valides_dans_l_annee = min_(
                (salaire_de_base / salaire_validant_un_trimestre).astype(int),
                4
                )
            return trimestres_valides_avant_cette_annee + trimestres_valides_dans_l_annee

    # def trim_maj_ini(self, trim_maj_mda_ini):  # sert à comparer avec pensipp
    #     return trim_maj_mda_ini

    # def trim_maj(self, data, trim_maj_mda):
    #     if 'maj_other_RG' in data.info_ind.dtype.names:
    #         trim_maj = trim_maj_mda + data.info_ind.trim_other_RG
    #     else:
    #         trim_maj = trim_maj_mda
    #     return trim_maj

    class coefficient_de_proratisation(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Coefficient de proratisation"

        def formula_2011_07_01(individu, period, parameters):
            date_de_naissance = individu('date_de_naissance', period)
            duree_de_proratisation = (
                parameters(period).regime_name.prorat.nombre_trimestres_maximal_pris_en_compte_proratisation_par_generation[date_de_naissance]
                )
            aad = individu('regime_name_age_annulation_decote', period)
            coefficient_minoration_par_trimestre = parameters(period).regime_name.decote.coefficient_minoration_par_trimestres_manquants.taux_minore_taux_plein_1_decote_nombre_trimestres_manquants[date_de_naissance]
            liquidation_date = individu('regime_name_liquidation_date', period)
            age_en_mois_a_la_liquidation = (
                liquidation_date
                - individu('date_de_naissance', period)
                ).astype("timedelta64[M]").astype(int)
            # TODO definition exacte trimestres ?
            trimestres_apres_aad = max_(
                0,
                np.trunc(
                    (age_en_mois_a_la_liquidation - aad * 12) / 3
                    )
                )
            trimestres = individu("regime_name_duree_assurance", period)
            duree_assurance_corrigee = min_(
                duree_de_proratisation,
                trimestres * (
                    1
                    + trimestres_apres_aad * coefficient_minoration_par_trimestre
                    )
                )
            coefficient = min_(1, duree_assurance_corrigee / duree_de_proratisation)
            return coefficient

        def formula_1983_04_01(individu, period, parameters):
            date_de_naissance = individu('date_de_naissance', period)
            duree_de_proratisation = (
                parameters(period).regime_name.prorat.nombre_trimestres_maximal_pris_en_compte_proratisation_par_generation[date_de_naissance]
                )
            aad = individu('regime_name_age_annulation_decote', period)
            coefficient_minoration_par_trimestre = parameters(period).regime_name.decote.coefficient_minoration_par_trimestres_manquants.taux_minore_taux_plein_1_decote_nombre_trimestres_manquants[date_de_naissance]
            liquidation_date = individu('regime_name_liquidation_date', period)
            age_en_mois_a_la_liquidation = (
                liquidation_date
                - individu('date_de_naissance', period)
                ).astype("timedelta64[M]").astype(int)
            # TODO definition exacte trimestres ?
            trimestres_apres_aad = max_(
                0,
                np.trunc(
                    (age_en_mois_a_la_liquidation - aad * 12) / 3
                    )
                )
            trimestres = individu("regime_name_duree_assurance", period)
            duree_assurance_corrigee = min_(
                duree_de_proratisation,
                trimestres * (
                    1
                    + trimestres_apres_aad * coefficient_minoration_par_trimestre
                    )
                )
            coefficient = min_(1, duree_assurance_corrigee / duree_de_proratisation)
            return coefficient

        def formula_1948(individu, period, parameters):
            trimestres = individu("regime_name_duree_assurance", period)
            duree_de_proratisation = (
                parameters(period).regime_name.prorat.nombre_trimestres_maximal_pris_en_compte_proratisation_par_generation.ne_avant_1944_01_01
                )
            duree_assurance_corrigee = (
                trimestres
                + (duree_de_proratisation - trimestres) / 2
                )
            coefficient = min_(1, duree_assurance_corrigee / duree_de_proratisation)
            return coefficient

        def formula_1946(individu, period, parameters):
            duree_de_proratisation = (
                parameters(period).regime_name.prorat.nombre_trimestres_maximal_pris_en_compte_proratisation_par_generation.ne_avant_1944_01_01
                )
            trimestres = individu("regime_name_duree_assurance", period)
            coefficient = min_(1, trimestres / duree_de_proratisation)
            return coefficient

    class cotisation_employeur(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Cotisation employeur"

        def formula(individu, period, parameters):
            categorie_salarie = individu("categorie_salarie", period)
            salaire_de_base = individu("salaire_de_base", period)
            plafond_securite_sociale = parameters(period).prelevements_sociaux.pss.plafond_securite_sociale_annuel
            employeur = parameters(period).regime_name.prelevements_sociaux.employeur
            salarie_concerne = (
                (categorie_salarie == TypesCategorieSalarie.prive_non_cadre)
                + (categorie_salarie == TypesCategorieSalarie.prive_cadre)
                + (categorie_salarie == TypesCategorieSalarie.public_non_titulaire)
                )
            return salarie_concerne * (
                employeur.vieillesse_deplafonnee.calc(salaire_de_base, factor = plafond_securite_sociale)
                + employeur.vieillesse_plafonnee.calc(salaire_de_base, factor = plafond_securite_sociale)
                )

    class cotisation_salarie(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Cotisation salarié"

        def formula(individu, period, parameters):
            categorie_salarie = individu("categorie_salarie", period)
            salaire_de_base = individu("salaire_de_base", period)
            plafond_securite_sociale = parameters(period).prelevements_sociaux.pss.plafond_securite_sociale_annuel
            salarie = parameters(period).regime_name.prelevements_sociaux.salarie
            salarie_concerne = (
                (categorie_salarie == TypesCategorieSalarie.prive_non_cadre)
                + (categorie_salarie == TypesCategorieSalarie.prive_cadre)
                + (categorie_salarie == TypesCategorieSalarie.public_non_titulaire)
                )
            return salarie_concerne * (
                salarie.vieillesse_deplafonnee.calc(salaire_de_base, factor = plafond_securite_sociale)
                + salarie.vieillesse_plafonnee.calc(salaire_de_base, factor = plafond_securite_sociale)
                )

    class decote(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Décote"

        def formula_1983_04_01(individu, period, parameters):
            date_de_naissance = individu('date_de_naissance', period)
            coefficient_minoration_par_trimestre = parameters(period).regime_name.decote.coefficient_minoration_par_trimestres_manquants.taux_minore_taux_plein_1_decote_nombre_trimestres_manquants[date_de_naissance]
            decote_trimestres = individu('regime_name_decote_trimestres', period)
            decote = coefficient_minoration_par_trimestre * decote_trimestres
            return decote

        def formula_1945(individu, period, parameters):
            decote_trimestres = individu('regime_name_decote_trimestres', period)
            coefficient_minoration_par_trimestre = parameters(period).regime_name.decote.coefficient_minoration_par_trimestres_manquants.taux_minore_taux_plein_1_decote_nombre_trimestres_manquants.ne_avant_1944_01_01
            return coefficient_minoration_par_trimestre * decote_trimestres

    class decote_trimestres(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Trimestres de décote"

        def formula_2011_07_01(individu, period, parameters):
            date_de_naissance = individu('date_de_naissance', period)
            aad = individu('regime_name_age_annulation_decote', period)
            duree_assurance_cible_taux_plein = (
                parameters(period).regime_name.trimtp.nombre_trimestres_cibles_par_generation[date_de_naissance]
                )
            age_en_mois_a_la_liquidation = (
                individu('regime_name_liquidation_date', period)
                - individu('date_de_naissance', period)
                ).astype("timedelta64[M]").astype(int)
            trimestres_avant_aad = np.trunc(
                (aad * 12 - age_en_mois_a_la_liquidation) / 3
                )
            duree_assurance_tous_regimes = individu('duree_assurance_tous_regimes', period)
            decote_trimestres = max_(
                0,
                min_(
                    duree_assurance_cible_taux_plein - duree_assurance_tous_regimes,
                    trimestres_avant_aad
                    )
                )
            return decote_trimestres

        def formula_1983_04_01(individu, period, parameters):
            aad = individu("regime_name_age_annulation_decote", period)
            date_de_naissance = individu("date_de_naissance", period)
            duree_assurance_cible_taux_plein = (
                parameters(period).regime_name.trimtp.nombre_trimestres_cibles_par_generation[date_de_naissance]
                )
            age_en_mois_a_la_liquidation = (
                individu("regime_name_liquidation_date", period)
                - individu("date_de_naissance", period)
                ).astype("timedelta64[M]").astype(int)
            trimestres_avant_aad = np.trunc(
                (aad * 12 - age_en_mois_a_la_liquidation) / 3
                )
            duree_assurance_tous_regimes = individu("duree_assurance_tous_regimes", period)
            decote_trimestres = max_(
                0,
                min_(
                    duree_assurance_cible_taux_plein - duree_assurance_tous_regimes,
                    trimestres_avant_aad
                    )
                )
            return decote_trimestres

        def formula_1945(individu, period, parameters):
            # TODO extract age by generation
            aad = individu("regime_name_age_annulation_decote", period)
            liquidation_date = individu('regime_name_liquidation_date', period)
            age_en_mois_a_la_liquidation = (
                liquidation_date
                - individu('date_de_naissance', period)
                ).astype("timedelta64[M]").astype(int)
            # TODO definition exacte trimestres ?
            decote_trimestres = max_(
                0,
                np.trunc(
                    (aad * 12 - age_en_mois_a_la_liquidation) / 3
                    )
                )
            return decote_trimestres

    class majoration_duree_assurance(Variable):
        value_type = int
        entity = Person
        definition_period = YEAR
        label = "Majoration de durée d'assurance (trimestres augmentant la durée d'assurance au régime général)"

        def formula(individu, period, parameters):
            annee_de_liquidation = individu('regime_name_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970
            liquidation = (annee_de_liquidation == period.start.year)
            # TODO créer une variable dédiée pour refléter la législation voir précis de législation retraite
            majoration_duree_assurance_enfant = individu('nombre_enfants', period) * 8
            return liquidation * majoration_duree_assurance_enfant

    class majoration_pension(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Majoration de pension"

    def formula(individu, period, parameters):
        # TODO Fix date, legislation parameters
        nombre_enfants = individu('nombre_enfants', period)
        pension_brute = individu('pension_brute', period)
        return .1 * pension_brute * (nombre_enfants >= 3)

    class pension_minimale(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Pension minimale (minimum contributif du régime général)"

        # TODO Peut-on réutiliser la formule de 2004
        def formula_2004_01_01(individu, period, parameters):
            regime_general_cnav = parameters(period).secteur_prive.regime_general_cnav
            minimum_contributif = regime_general_cnav.montant_mico
            mico = minimum_contributif.minimum_contributif
            mico_majoration = minimum_contributif.minimum_contributif_majore - mico

            date_de_naissance = individu("date_de_naissance", period)
            duree_de_proratisation = regime_general_cnav.prorat.nombre_trimestres_maximal_pris_en_compte_proratisation_par_generation[date_de_naissance]
            duree_assurance_cible_taux_plein = regime_general_cnav.trimtp.nombre_trimestres_cibles_par_generation[date_de_naissance]

            duree_assurance_regime_general = individu("regime_name_duree_assurance", period)
            duree_assurance_cotisee_regime_general = individu("regime_name_duree_assurance_cotisee", period)

            duree_assurance_tous_regimes = individu("duree_assurance_tous_regimes", period)
            duree_assurance_cotisee_tous_regimes = individu("duree_assurance_cotisee_tous_regimes", period)

            mono_pensionne_regime_general_ou_polypensionne_carriere_incomplete = (
                duree_assurance_tous_regimes == duree_assurance_regime_general
                ) + (
                duree_assurance_tous_regimes < duree_assurance_cible_taux_plein
                )  # Incomplete car pas trop de majoration
            polypensionne_cotisant_moins_que_duree_requise = (
                not_(mono_pensionne_regime_general_ou_polypensionne_carriere_incomplete)
                + (duree_assurance_cotisee_tous_regimes < duree_de_proratisation)
                )
            polypensionne_cotisant_moins_plus_duree_requise = (
                not_(mono_pensionne_regime_general_ou_polypensionne_carriere_incomplete)
                + (duree_assurance_cotisee_tous_regimes >= duree_de_proratisation)
                )
            numerateur_montant_de_base = select(
                [
                    mono_pensionne_regime_general_ou_polypensionne_carriere_incomplete,
                    polypensionne_cotisant_moins_que_duree_requise,
                    polypensionne_cotisant_moins_plus_duree_requise,
                    ],
                [
                    duree_assurance_regime_general,
                    duree_assurance_regime_general,
                    duree_assurance_regime_general,
                    ]
                )
            denominateur_montant_de_base = select(
                [
                    mono_pensionne_regime_general_ou_polypensionne_carriere_incomplete,
                    polypensionne_cotisant_moins_que_duree_requise,
                    polypensionne_cotisant_moins_plus_duree_requise,
                    ],
                [
                    duree_de_proratisation,
                    duree_assurance_tous_regimes,
                    duree_assurance_tous_regimes,
                    ]
                )
            numerateur_majoration = select(
                [
                    mono_pensionne_regime_general_ou_polypensionne_carriere_incomplete,
                    polypensionne_cotisant_moins_que_duree_requise,
                    polypensionne_cotisant_moins_plus_duree_requise,
                    ],
                [
                    duree_assurance_cotisee_regime_general,
                    duree_assurance_cotisee_tous_regimes,
                    duree_assurance_regime_general,
                    ]
                )
            denominateur_majoration = select(
                [
                    mono_pensionne_regime_general_ou_polypensionne_carriere_incomplete,
                    ],
                [
                    duree_de_proratisation,
                    duree_de_proratisation,
                    duree_assurance_tous_regimes,
                    ]
                )

            coefficient_de_proratisation_montant_de_base = min_(
                1,
                numerateur_montant_de_base / denominateur_montant_de_base
                )
            coefficient_de_proratisation_majoration = min_(
                1,
                numerateur_majoration / denominateur_majoration
                )
            return (
                coefficient_de_proratisation_montant_de_base * mico
                + coefficient_de_proratisation_majoration * mico_majoration
                )

        def formula_1983_01_01(individu, period, parameters):
            mico = parameters(period).secteur_prive.regime_general_cnav.montant_mico
            trimestres_regime = individu("regime_name_duree_assurance", period)
            date_de_naissance = individu("date_de_naissance", period)
            duree_de_proratisation = (
                parameters(period).regime_name.prorat.nombre_trimestres_maximal_pris_en_compte_proratisation_par_generation[date_de_naissance]
                )
            coefficient_de_proratisation = min_(1, trimestres_regime / duree_de_proratisation)
            return coefficient_de_proratisation * mico

        def formula_1941_01_01(indiivdu, period, parameters):
            # TODO limite d'âge bonification etc voir section 5 précis
            avts = parameters(period).prestations_sociales.solidarite_insertion.minimum_vieillesse_droits_non_contributifs_de_retraite.avts_av_1961
            return avts

        # ''' MICO du régime général : allocation différentielle
        # RQ :
        # 1) ASPA et minimum vieillesse sont gérés par OF
        # 2) Le minimum contributif est calculé sans prendre ne compte les majoration pour enfants à charge
        # et la surcote (rajouté ensuite)

        # Il est attribué quels que soient les revenus dont dispose le retraité en plus de ses pensions :
        # loyers, revenus du capital, activité professionnelle...
        # + mécanisme de répartition si cotisations à plusieurs régimes
        # TODO: coder toutes les évolutions et rebondissements 2004/2008'''
        # P = reduce(getattr, self.param_name.split('.'), self.P)
        # # pension_RG, pension, trim_RG, trim_cot, trim
        # trim_regime = nb_trimesters + trim_maj
        # coeff = minimum(1, divide(trim_regime, P.prorat.n_trim))
        # if P.mico.dispositif == 0:
        #     # Avant le 1er janvier 1983, comparé à l'AVTS
        #     min_pension = self.P.common.avts
        #     return maximum(min_pension - pension_brute, 0) * coeff
        # elif P.mico.dispositif == 1:
        #     # TODO: Voir comment gérer la limite de cumul relativement
        #     # complexe (Doc n°5 du COR)
        #     mico = P.mico.entier
        #     return maximum(mico - pension_brute, 0) * coeff
        # elif P.mico.dispositif == 2:
        #     # A partir du 1er janvier 2004 les périodes cotisées interviennent
        #     # (+ dispositif transitoire de 2004)
        #     nb_trim = P.prorat.n_trim
        #     trim_regime = nb_trimesters  # + sum(trim_maj)
        #     mico_entier = P.mico.entier * minimum(divide(trim_regime, nb_trim), 1)
        #     maj = (P.mico.entier_maj - P.mico.entier) * divide(trimesters_tot.sum(axis=1), nb_trim)
        #     mico = mico_entier + maj * (trimesters_tot.sum(axis=1) >= P.mico.trim_min)
        #     return (mico - pension_brute) * (mico > pension_brute) * (pension_brute > 0)

    class pension_maximale(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Pension maximale"

        def formula(individu, period, parameters):

            # TODO: gérer les plus de 65 ans au 1er janvier 1983'''
            plafond_securite_sociale = parameters(period).prelevements_sociaux.pss.plafond_securite_sociale_annuel
            taux_plein = parameters(period).regime_name.taux_plein.taux_plein
            pension_plafond_hors_sucote = taux_plein * plafond_securite_sociale
            pension_brute = individu('regime_name_pension_brute', period)
            taux_de_liquidation = individu('regime_name_taux_de_liquidation', period)
            surcote = individu('regime_name_surcote', period)
            pension_surcote = (pension_brute / taux_de_liquidation) * taux_plein * surcote
            return min_(pension_brute - pension_surcote, pension_plafond_hors_sucote) + pension_surcote

    class salaire_de_reference(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Salaire annuel moyen de base dit salaire de référence"

        def formula_1994(individu, period, parameters):
            OFFSET = 10  # do not start working before 10 year
            liquidation_date = individu('regime_name_liquidation_date', period)
            annee_de_naissance = (
                individu('date_de_naissance', period).astype('datetime64[Y]').astype(int) + 1970
                )
            annees_de_naissance_distinctes = np.unique(
                annee_de_naissance[liquidation_date >= np.datetime64(period.start)]
                )
            salaire_de_reference = individu.empty_array()
            for _annee_de_naissance in sorted(annees_de_naissance_distinctes):
                if _annee_de_naissance + OFFSET >= period.start.year:
                    break
                k = int(
                    parameters(period).secteur_prive.regime_general_cnav.sam.nombre_annees_carriere_entrant_en_jeu_dans_determination_salaire_annuel_moyen[
                        np.array(str(_annee_de_naissance), dtype="datetime64[Y]")
                        ]
                    )
                mean_over_largest = make_mean_over_largest(k)
                revalorisation = dict()
                REVAL_S_YEAR_MIN = 1949
                revalorisation[period.start.year] = 1
                for annee_salaire in range(max(_annee_de_naissance + OFFSET, REVAL_S_YEAR_MIN), period.start.year + 1):
                    # Pour un salaire 2020 tu le multiplies par le coefficient 01/01/2021 si tu veux sa valeur après le 1er janvier 21
                    revalorisation[annee_salaire] = (
                        np.prod(
                            np.array([
                                parameters(_annee).secteur_prive.regime_general_cnav.reval_s.coefficient
                                for _annee in range(annee_salaire + 1, period.start.year + 1)
                                ])
                            )
                        )
                # print(period.start.year, _annee_de_naissance + OFFSET)
                filter = annee_de_naissance == _annee_de_naissance,
                # TODO try boolean indexing instead of where to lighten the burden on vstack and apply along_axis ?
                arr = np.vstack([
                    min_(
                        individu('salaire_de_base', period = year)[filter],
                        parameters(year).prelevements_sociaux.pss.plafond_securite_sociale_annuel
                        )
                    * revalorisation[year]
                    for year in range(period.start.year, _annee_de_naissance + OFFSET, -1)
                    ])
                compute_salaire_de_reference(mean_over_largest, arr, salaire_de_reference, filter)

            return salaire_de_reference

        def formula_1972(individu, period, parameters):
            # TODO test and adapt like 1994 formula
            n = parameters(period).regime_name.sam.nombre_annees_carriere_entrant_en_jeu_dans_determination_salaire_annuel_moyen.ne_avant_1934_01_01
            mean_over_largest = functools.partial(mean_over_k_nonzero_largest, k = n)
            annee_initiale = (individu('date_de_naissance', period).astype('datetime64[Y]').astype(int) + 1970).min()
            salaire_de_refererence = np.apply_along_axis(
                mean_over_largest,
                axis = 0,
                arr = np.vstack([
                    min_(
                        individu('salaire_de_base', period = year),
                        parameters(year).prelevements_sociaux.pss.plafond_securite_sociale_annuel
                        )
                    for year in range(period.start.year, annee_initiale, -1)
                    ]),
                )
            return salaire_de_refererence

    class surcote(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "Surcote"

        def formula_2009_04_01(individu, period, parameters):
            aod = 65
            taux_surcote = (
                parameters(period).regime_name.surcote.taux_surcote_par_trimestre_cotise_selon_date_cotisation.apres_01_01_2004['partir_65_ans']
                )
            date_de_naissance = individu('date_de_naissance', period)
            liquidation_date = individu('regime_name_liquidation_date', period)
            age_en_mois_a_la_liquidation = (
                liquidation_date
                - individu('date_de_naissance', period)
                ).astype("timedelta64[M]").astype(int)
            # TODO definition exacte trimestres ?
            trimestres_apres_aod = max_(
                0,
                np.trunc(
                    (age_en_mois_a_la_liquidation - aod * 12) / 3
                    )
                )
            distance_a_2004_en_trimestres = max_(
                0,
                np.trunc(
                    (liquidation_date - np.datetime64("2004-01-01")).astype("timedelta64[M]").astype(int)
                    / 3
                    )
                )
            duree_assurance_tous_regimes = individu('duree_assurance_tous_regimes', period)
            duree_assurance_cible_taux_plein = (
                parameters(period).regime_name.trimtp.nombre_trimestres_cibles_par_generation[date_de_naissance]
                )
            trimestres_surcote = max_(
                0,
                min_(
                    min_(
                        distance_a_2004_en_trimestres,
                        trimestres_apres_aod
                        ),
                    duree_assurance_tous_regimes - duree_assurance_cible_taux_plein
                    )
                )
            return taux_surcote * trimestres_surcote

        def formula_2007_01_01(individu, period, parameters):
            aod = 65
            taux_surcote_par_trimestre = parameters(period).regime_name.surcote.taux_surcote_par_trimestre_cotise_selon_date_cotisation.apres_01_01_2004
            taux_surcote_par_trimestre_moins_de_4_trimestres = taux_surcote_par_trimestre['moins_de_4_trimestres']
            taux_surcote_par_trimestre_plus_de_5_trimestres = taux_surcote_par_trimestre['plus_de_5_trimestres']
            taux_surcote_par_trimestre_partir_65_ans = taux_surcote_par_trimestre['partir_65_ans']

            date_de_naissance = individu('date_de_naissance', period)
            liquidation_date = individu('regime_name_liquidation_date', period)
            age_en_mois_a_la_liquidation = (
                liquidation_date
                - individu('date_de_naissance', period)
                ).astype("timedelta64[M]").astype(int)
            # TODO definition exacte trimestres ?
            trimestres_apres_aod = max_(
                0,
                np.trunc(
                    (age_en_mois_a_la_liquidation - aod * 12) / 3
                    )
                )
            distance_a_2004_en_trimestres = max_(
                0,
                np.trunc(
                    (liquidation_date - np.datetime64("2004-01-01")).astype("timedelta64[M]").astype(int)
                    / 3
                    )
                )
            duree_assurance_tous_regimes = individu('duree_assurance_tous_regimes', period)
            duree_assurance_cible_taux_plein = (
                parameters(period).regime_name.trimtp.nombre_trimestres_cibles_par_generation[date_de_naissance]
                )
            trimestres_surcote = max_(
                0,
                min_(
                    min_(
                        distance_a_2004_en_trimestres,
                        trimestres_apres_aod
                        ),
                    duree_assurance_tous_regimes - duree_assurance_cible_taux_plein
                    )
                )
            trimestres_surcote_au_dela_de_65_ans = min_(
                trimestres_surcote,
                max_(
                    0,
                    np.trunc(
                            (age_en_mois_a_la_liquidation - 65 * 12) / 3
                        )
                    )
                )
            trimestres_surcote_en_deca_de_65_ans = max_(
                0,
                (
                    trimestres_surcote
                    - trimestres_surcote_au_dela_de_65_ans
                    )
                )
            surcote = (
                taux_surcote_par_trimestre_moins_de_4_trimestres * min_(4, trimestres_surcote_en_deca_de_65_ans)
                + taux_surcote_par_trimestre_plus_de_5_trimestres * max_(0, trimestres_surcote_en_deca_de_65_ans - 4)
                + taux_surcote_par_trimestre_partir_65_ans * trimestres_surcote_au_dela_de_65_ans
                )
            return surcote

        def formula_2004_01_01(individu, period, parameters):
            aod = 65
            taux_surcote_par_trimestre_moins_de_4_trimestres = (
                parameters(period).regime_name.surcote.taux_surcote_par_trimestre_cotise_selon_date_cotisation.apres_01_01_2004['moins_de_4_trimestres']
                )
            date_de_naissance = individu('date_de_naissance', period)
            liquidation_date = individu('regime_name_liquidation_date', period)
            age_en_mois_a_la_liquidation = (
                liquidation_date
                - individu('date_de_naissance', period)
                ).astype("timedelta64[M]").astype(int)
            # TODO definition exacte trimestres ?
            trimestres_apres_aod = max_(
                0,
                np.trunc(
                    (age_en_mois_a_la_liquidation - aod * 12) / 3
                    )
                )
            distance_a_2004_en_trimestres = max_(
                0,
                np.trunc(
                    (liquidation_date - np.datetime64("2004-01-01")).astype("timedelta64[M]").astype(int)
                    / 3
                    )
                )
            duree_assurance_tous_regimes = individu('duree_assurance_tous_regimes', period)
            duree_assurance_cible_taux_plein = (
                parameters(period).regime_name.trimtp.nombre_trimestres_cibles_par_generation[date_de_naissance]
                )
            trimestres_surcote = max_(
                0,
                min_(
                    min_(
                        distance_a_2004_en_trimestres,
                        trimestres_apres_aod
                        ),
                    duree_assurance_tous_regimes - duree_assurance_cible_taux_plein
                    )
                )
            return taux_surcote_par_trimestre_moins_de_4_trimestres * trimestres_surcote

        def formula_1983_04_01(individu, period):
            return individu.empty_array()

        def formula_1945(individu, period):
            # TODO absent des paramètres
            coefficient_majoration_par_trimestre = .1 / 4
            aad = 65
            liquidation_date = individu('regime_name_liquidation_date', period)
            age_en_mois_a_la_liquidation = (
                liquidation_date
                - individu('date_de_naissance', period)
                ).astype("timedelta64[M]").astype(int)
            # TODO definition exacte trimestres ?
            trimestres_apres_aad = max_(
                0,
                np.trunc(
                    (age_en_mois_a_la_liquidation - aad * 12) / 3
                    )
                )
            return coefficient_majoration_par_trimestre * trimestres_apres_aad
