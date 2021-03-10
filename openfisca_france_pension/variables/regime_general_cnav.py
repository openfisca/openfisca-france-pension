"""Abstract regimesdefinition."""
from openfisca_france_pension.tools import mean_over_k_nonzero_largest
from openfisca_france_pension.regimes.regime import AbstractRegimeDeBase
from openfisca_core.variables import Variable
from openfisca_core.periods import ETERNITY, MONTH, YEAR
import numpy as np
import functools
from openfisca_core.model_api import *
from openfisca_france_pension.entities import Household, Person
'Régime de base du secteur privé: régime général de la CNAV.'


class regime_general_cnav_salaire_de_reference(Variable):
    value_type = float
    entity = Person
    definition_period = ETERNITY
    label = 'Salaire de référence'


class regime_general_cnav_trimestres(Variable):
    value_type = int
    entity = Person
    definition_period = YEAR
    label = 'Trimestres'


class regime_general_cnav_majoration_pension(Variable):
    value_type = int
    entity = Person
    definition_period = MONTH
    label = 'Majoration de pension'


class regime_general_cnav_decote(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Décote'


class regime_general_cnav_decote_date_annulation(Variable):
    value_type = date
    entity = Person
    definition_period = YEAR
    label = 'Décote'


class regime_general_cnav_pension_brute(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Pension brute'

    def formula(individu, period, parameters):
        coefficient_de_proratisation = individu('secteur_prive.regime_general_cnav_coefficient_de_proratisation', period)
        salaire_de_reference = individu('secteur_prive.regime_general_cnav_salaire_de_reference', period)
        taux_de_liquidation = individu('secteur_prive.regime_general_cnav_taux_de_liquidation', period)
        return coefficient_de_proratisation * salaire_de_reference * taux_de_liquidation


class regime_general_cnav_pension(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Pension'

    def formula(individu, period):
        pension_brute = individu('secteur_prive.regime_general_cnav_pension_brute', period)
        majoration_pension = individu('secteur_prive.regime_general_cnav_majoration_pension', period)
        return pension_brute + majoration_pension


class regime_general_cnav_surcote_debut_date(Variable):
    value_type = date
    entity = Person
    definition_period = YEAR
    label = 'Date du début de la surcote'


class regime_general_cnav_decote_annulation_date(Variable):
    value_type = date
    entity = Person
    definition_period = YEAR
    label = "Date d'annulation de la décote'"


class regime_general_cnav_taux_plein_date(Variable):
    value_type = date
    entity = Person
    definition_period = YEAR
    label = 'Date du taux plein'


class regime_general_cnav_taux_de_liquidation(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Taux de liquidation de la pension'

    def formula(individu, period, parameters):
        decote = individu('secteur_prive.regime_general_cnav_decote', period)
        surcote = individu('secteur_prive.regime_general_cnav_surcote', period)
        taux_plein = parameters(period).regime_general_cnav.taux_plein.taux_plein
        return taux_plein * (1 - decote + surcote)


class regime_general_cnav_cotisation_retraite(Variable):
    value_type = float
    entity = Person
    definition_period = MONTH
    label = 'cotisation retraite'

    def formula(individu, period, parameters):
        salaire_de_base = individu('salaire_de_base', period)
        taux = parameters(period).regime_general_cnav.cotisation.taux
        return salaire_de_base * taux


class regime_general_cnav_trimestres(Variable):
    value_type = int
    entity = Person
    definition_period = YEAR
    label = 'Trimestres cotisés au régime général'


class regime_general_cnav_salaire_de_reference(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Salaire annuel moyen de base dit salaire de référence'

    def formula_1994(individu, period, parameters):
        OFFSET = 10
        date_de_naissance = individu('date_de_naissance', period)
        annee_de_naissance = int(individu('date_de_naissance', period).astype('datetime64[Y]').astype(int) + 1970)
        annees_de_naissance_distinctes = np.unique(annee_de_naissance)
        salaire_de_refererence = 0
        for _annee_de_naissance in sorted(annees_de_naissance_distinctes):
            n = int(parameters(period).secteur_prive.regime_general_cnav.sam.nombre_annees_carriere_entrant_en_jeu_dans_determination_salaire_annuel_moyen[date_de_naissance])
            mean_over_largest = functools.partial(mean_over_k_nonzero_largest, k=n)
            revalorisation = dict()
            revalorisation[period.start.year] = 1
            for annee_salaire in range(annee_de_naissance + OFFSET, period.start.year + 1):
                revalorisation[annee_salaire] = np.prod(np.array([parameters(_annee).secteur_prive.regime_general_cnav.reval_s.coefficient for _annee in range(annee_salaire + 1, period.start.year + 1)]))
            salaire_de_refererence = where(annee_de_naissance == _annee_de_naissance, np.apply_along_axis(mean_over_largest, axis=0, arr=np.vstack([min_(individu('salaire_de_base', period=year), parameters(year).prelevements_sociaux.pss.plafond_securite_sociale_annuel) * revalorisation[year] for year in range(period.start.year, _annee_de_naissance + OFFSET, -1)])), salaire_de_refererence)
        return salaire_de_refererence

    def formula_1972(individu, period, parameters):
        n = parameters(period).regime_general_cnav.sam.nombre_annees_carriere_entrant_en_jeu_dans_determination_salaire_annuel_moyen.ne_avant_1934_01_01
        mean_over_largest = functools.partial(mean_over_k_nonzero_largest, k=n)
        annee_initiale = (individu('date_de_naissance', period).astype('datetime64[Y]').astype(int) + 1970).min()
        salaire_de_refererence = np.apply_along_axis(mean_over_largest, axis=0, arr=np.vstack([min_(individu('salaire_de_base', period=year), parameters(year).prelevements_sociaux.pss.plafond_securite_sociale_annuel) for year in range(period.start.year, annee_initiale, -1)]))
        return salaire_de_refererence


class regime_general_cnav_coefficient_de_proratisation(Variable):
    value_type = float
    entity = Person
    definition_period = ETERNITY
    label = 'Coefficient de proratisation'

    def formula_2011_07_01(individu, period, parameters):
        date_de_naissance = individu('date_de_naissance', period)
        duree_de_proratisation = parameters(period).regime_general_cnav.prorat.nombre_trimestres_maximal_pris_en_compte_proratisation_par_generation[date_de_naissance]
        aad_annee = parameters(period).regime_general_cnav.aad.age_annulation_decote_en_fonction_date_naissance[date_de_naissance].annee
        aad_mois = parameters(period).regime_general_cnav.aad.age_annulation_decote_en_fonction_date_naissance[date_de_naissance].mois
        coefficient_minoration_par_trimestre = parameters(period).regime_general_cnav.decote.coefficient_minoration_par_trimestres_manquants.taux_minore_taux_plein_1_decote_nombre_trimestres_manquants[date_de_naissance]
        liquidation_date = individu('secteur_prive.regime_general_cnav_liquidation_date', period)
        age_en_mois_a_la_liquidation = (liquidation_date - individu('date_de_naissance', period)).astype('timedelta64[M]').astype(int)
        trimestres_apres_add = max_(0, np.trunc((age_en_mois_a_la_liquidation - aad_annee * 12 - aad_mois) / 3))
        age = individu('age_au_31_decembre', period)
        trimestres = individu('secteur_prive.regime_general_cnav_trimestres', period)
        duree_assurance_corrigee = min_(duree_de_proratisation, trimestres * (1 + trimestres_apres_add * coefficient_minoration_par_trimestre))
        coefficient = min_(1, duree_assurance_corrigee / duree_de_proratisation)
        return coefficient

    def formula_1983_04_01(individu, period, parameters):
        date_de_naissance = individu('date_de_naissance', period)
        duree_de_proratisation = parameters(period).regime_general_cnav.prorat.nombre_trimestres_maximal_pris_en_compte_proratisation_par_generation[date_de_naissance]
        aad = parameters(period).regime_general_cnav.aad.age_annulation_decote_en_fonction_date_naissance.ne_avant_1951_07_01.annee
        coefficient_minoration_par_trimestre = parameters(period).regime_general_cnav.decote.coefficient_minoration_par_trimestres_manquants.taux_minore_taux_plein_1_decote_nombre_trimestres_manquants[date_de_naissance]
        liquidation_date = individu('secteur_prive.regime_general_cnav_liquidation_date', period)
        age_en_mois_a_la_liquidation = (liquidation_date - individu('date_de_naissance', period)).astype('timedelta64[M]').astype(int)
        trimestres_apres_add = max_(0, np.trunc((age_en_mois_a_la_liquidation - aad * 12) / 3))
        age = individu('age_au_31_decembre', period)
        trimestres = individu('secteur_prive.regime_general_cnav_trimestres', period)
        duree_assurance_corrigee = min_(duree_de_proratisation, trimestres * (1 + trimestres_apres_add * coefficient_minoration_par_trimestre))
        coefficient = min_(1, duree_assurance_corrigee / duree_de_proratisation)
        return coefficient

    def formula_1948(individu, period, parameters):
        trimestres = individu('secteur_prive.regime_general_cnav_trimestres', period)
        duree_de_proratisation = parameters(period).regime_general_cnav.prorat.nombre_trimestres_maximal_pris_en_compte_proratisation_par_generation.ne_avant_1944_01_01
        duree_assurance_corrigee = trimestres + (duree_de_proratisation - trimestres) / 2
        coefficient = min_(1, duree_assurance_corrigee / duree_de_proratisation)
        return coefficient

    def formula_1946(individu, period, parameters):
        duree_de_proratisation = parameters(period).regime_general_cnav.prorat.nombre_trimestres_maximal_pris_en_compte_proratisation_par_generation.ne_avant_1944_01_01
        trimestres = individu('secteur_prive.regime_general_cnav_trimestres', period)
        coefficient = min_(1, trimestres / duree_de_proratisation)
        return coefficient


class regime_general_cnav_decote(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Décote'

    def formula_2011_07_01(individu, period, parameters):
        date_de_naissance = individu('date_de_naissance', period)
        aad_annee = parameters(period).regime_general_cnav.aad.age_annulation_decote_en_fonction_date_naissance[date_de_naissance].annee
        aad_mois = parameters(period).regime_general_cnav.aad.age_annulation_decote_en_fonction_date_naissance[date_de_naissance].mois
        coefficient_minoration_par_trimestre = parameters(period).regime_general_cnav.decote.coefficient_minoration_par_trimestres_manquants.taux_minore_taux_plein_1_decote_nombre_trimestres_manquants[date_de_naissance]
        trimestres_cibles_taux_plein = parameters(period).regime_general_cnav.trimtp.nombre_trimestres_cibles_par_generation[date_de_naissance]
        age_en_mois_a_la_liquidation = (individu('secteur_prive.regime_general_cnav_liquidation_date', period) - individu('date_de_naissance', period)).astype('timedelta64[M]').astype(int)
        trimestres_apres_add = np.trunc((aad_annee * 12 + aad_mois - age_en_mois_a_la_liquidation) / 3)
        trimestres = individu('secteur_prive.regime_general_cnav_trimestres', period)
        decote = coefficient_minoration_par_trimestre * max_(0, min_(trimestres_cibles_taux_plein - trimestres, trimestres_apres_add))
        return decote

    def formula_1983_04_01(individu, period, parameters):
        aad = 65
        date_de_naissance = individu('date_de_naissance', period)
        coefficient_minoration_par_trimestre = parameters(period).regime_general_cnav.decote.coefficient_minoration_par_trimestres_manquants.taux_minore_taux_plein_1_decote_nombre_trimestres_manquants[date_de_naissance]
        trimestres_cibles_taux_plein = parameters(period).regime_general_cnav.trimtp.nombre_trimestres_cibles_par_generation[date_de_naissance]
        liquidation_date = individu('secteur_prive.regime_general_cnav_liquidation_date', period)
        age_en_mois_a_la_liquidation = (liquidation_date - individu('date_de_naissance', period)).astype('timedelta64[M]').astype(int)
        trimestres_apres_add = np.trunc((aad * 12 - age_en_mois_a_la_liquidation) / 3)
        trimestres = individu('secteur_prive.regime_general_cnav_trimestres', period)
        decote = coefficient_minoration_par_trimestre * max_(0, min_(trimestres_cibles_taux_plein - trimestres, trimestres_apres_add))
        return decote

    def formula_1945(individu, period, parameters):
        coefficient_minoration_par_trimestre = parameters(period).regime_general_cnav.decote.coefficient_minoration_par_trimestres_manquants.taux_minore_taux_plein_1_decote_nombre_trimestres_manquants.ne_avant_1944_01_01
        aad = 65
        liquidation_date = individu('secteur_prive.regime_general_cnav_liquidation_date', period)
        age_en_mois_a_la_liquidation = (liquidation_date - individu('date_de_naissance', period)).astype('timedelta64[M]').astype(int)
        trimestres_apres_add = max_(0, np.trunc((aad * 12 - age_en_mois_a_la_liquidation) / 3))
        return coefficient_minoration_par_trimestre * trimestres_apres_add


class regime_general_cnav_liquidation_date(Variable):
    value_type = date
    entity = Person
    definition_period = ETERNITY
    label = 'Date de liquidation'


class regime_general_cnav_surcote(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Surcote'

    def formula_2009_04_01(individu, period, parameters):
        aod = 65
        taux_surcote = parameters(period).regime_general_cnav.surcote.taux_surcote_par_trimestre_cotise_selon_date_cotisation.apres_01_01_2004['partir_65_ans']
        date_de_naissance = individu('date_de_naissance', period)
        liquidation_date = individu('secteur_prive.regime_general_cnav_liquidation_date', period)
        age_en_mois_a_la_liquidation = (liquidation_date - individu('date_de_naissance', period)).astype('timedelta64[M]').astype(int)
        trimestres_apres_aod = max_(0, np.trunc((age_en_mois_a_la_liquidation - aod * 12) / 3))
        distance_a_2004_en_trimestres = max_(0, np.trunc((liquidation_date - np.datetime64('2004-01-01')).astype('timedelta64[M]').astype(int) / 3))
        trimestres = individu('secteur_prive.regime_general_cnav_trimestres', period)
        trimestres_cibles_taux_plein = parameters(period).regime_general_cnav.trimtp.nombre_trimestres_cibles_par_generation[date_de_naissance]
        trimestres_surcote = max_(0, min_(min_(distance_a_2004_en_trimestres, trimestres_apres_aod), trimestres - trimestres_cibles_taux_plein))
        return taux_surcote * trimestres_surcote

    def formula_2007_01_01(individu, period, parameters):
        aod = 65
        taux_surcote_par_trimestre_moins_de_4_trimestres = parameters(period).regime_general_cnav.surcote.taux_surcote_par_trimestre_cotise_selon_date_cotisation.apres_01_01_2004['moins_de_4_trimestres']
        taux_surcote_par_trimestre_plus_de_5_trimestres = parameters(period).regime_general_cnav.surcote.taux_surcote_par_trimestre_cotise_selon_date_cotisation.apres_01_01_2004['plus_de_5_trimestres']
        taux_surcote_par_trimestre_partir_65_ans = parameters(period).regime_general_cnav.surcote.taux_surcote_par_trimestre_cotise_selon_date_cotisation.apres_01_01_2004['partir_65_ans']
        date_de_naissance = individu('date_de_naissance', period)
        liquidation_date = individu('secteur_prive.regime_general_cnav_liquidation_date', period)
        age_en_mois_a_la_liquidation = (liquidation_date - individu('date_de_naissance', period)).astype('timedelta64[M]').astype(int)
        trimestres_apres_aod = max_(0, np.trunc((age_en_mois_a_la_liquidation - aod * 12) / 3))
        distance_a_2004_en_trimestres = max_(0, np.trunc((liquidation_date - np.datetime64('2004-01-01')).astype('timedelta64[M]').astype(int) / 3))
        trimestres = individu('secteur_prive.regime_general_cnav_trimestres', period)
        trimestres_cibles_taux_plein = parameters(period).regime_general_cnav.trimtp.nombre_trimestres_cibles_par_generation[date_de_naissance]
        trimestres_surcote = max_(0, min_(min_(distance_a_2004_en_trimestres, trimestres_apres_aod), trimestres - trimestres_cibles_taux_plein))
        trimestres_surcote_au_dela_de_65_ans = min_(trimestres_surcote, max_(0, np.trunc((age_en_mois_a_la_liquidation - 65 * 12) / 3)))
        trimestres_surcote_en_deca_de_65_ans = max_(0, trimestres_surcote - trimestres_surcote_au_dela_de_65_ans)
        surcote = taux_surcote_par_trimestre_moins_de_4_trimestres * min_(4, trimestres_surcote_en_deca_de_65_ans) + taux_surcote_par_trimestre_plus_de_5_trimestres * max_(0, trimestres_surcote_en_deca_de_65_ans - 4) + taux_surcote_par_trimestre_partir_65_ans * trimestres_surcote_au_dela_de_65_ans
        return surcote

    def formula_2004_01_01(individu, period, parameters):
        aod = 65
        taux_surcote_par_trimestre_moins_de_4_trimestres = parameters(period).regime_general_cnav.surcote.taux_surcote_par_trimestre_cotise_selon_date_cotisation.apres_01_01_2004['moins_de_4_trimestres']
        date_de_naissance = individu('date_de_naissance', period)
        liquidation_date = individu('secteur_prive.regime_general_cnav_liquidation_date', period)
        age_en_mois_a_la_liquidation = (liquidation_date - individu('date_de_naissance', period)).astype('timedelta64[M]').astype(int)
        trimestres_apres_aod = max_(0, np.trunc((age_en_mois_a_la_liquidation - aod * 12) / 3))
        distance_a_2004_en_trimestres = max_(0, np.trunc((liquidation_date - np.datetime64('2004-01-01')).astype('timedelta64[M]').astype(int) / 3))
        trimestres = individu('secteur_prive.regime_general_cnav_trimestres', period)
        trimestres_cibles_taux_plein = parameters(period).regime_general_cnav.trimtp.nombre_trimestres_cibles_par_generation[date_de_naissance]
        trimestres_surcote = max_(0, min_(min_(distance_a_2004_en_trimestres, trimestres_apres_aod), trimestres - trimestres_cibles_taux_plein))
        return taux_surcote_par_trimestre_moins_de_4_trimestres * trimestres_surcote

    def formula_1983_04_01(individu, period):
        return individu.empty_array()

    def formula_1945(individu, period):
        coefficient_majoration_par_trimestre = 0.1 / 4
        aad = 65
        liquidation_date = individu('secteur_prive.regime_general_cnav_liquidation_date', period)
        age_en_mois_a_la_liquidation = (liquidation_date - individu('date_de_naissance', period)).astype('timedelta64[M]').astype(int)
        trimestres_apres_add = max_(0, np.trunc((age_en_mois_a_la_liquidation - aad * 12) / 3))
        return coefficient_majoration_par_trimestre * trimestres_apres_add


class regime_general_cnav_pension_minimale(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Pension minimale'


class regime_general_cnav_pension_maximale(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Pension maximale'