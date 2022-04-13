"""Abstract regimes definition."""
import numpy as np
from openfisca_core.model_api import *
from openfisca_core.errors.variable_not_found_error import VariableNotFoundError
from openfisca_france_pension.entities import Person

def revalorise(variable_31_decembre_annee_precedente, variable_originale, annee_de_liquidation, revalorisation, period):
    return select([annee_de_liquidation > period.start.year, annee_de_liquidation == period.start.year, annee_de_liquidation < period.start.year], [0, variable_originale, variable_31_decembre_annee_precedente * revalorisation])
'Régime de base de la fonction publique.'
import numpy as np
from openfisca_core.model_api import *
from openfisca_core.parameters import ParameterNotFound
from openfisca_france_pension.entities import Person
from openfisca_france_pension.regimes.regime import AbstractRegimeDeBase

class TypesCategorieActivite(Enum):
    __order__ = 'sedentaire actif'
    sedentaire = 'Sédentaire'
    actif = 'Actif'

class fonction_publique_actif_a_la_liquidation(Variable):
    value_type = bool
    entity = Person
    definition_period = YEAR
    label = "Atteinte des quinze ans d'activité"

    def formula(individu, period, parameters):
        date_quinze_ans_actif = individu('fonction_publique_date_quinze_ans_actif', period)
        actif_annee = parameters(period).secteur_public.duree_seuil_actif.duree_service_minimale_considere_comme_actif[date_quinze_ans_actif]
        actif = individu('fonction_publique_nombre_annees_actif', period) >= actif_annee
        return actif

class fonction_publique_annee_age_ouverture_droits(Variable):
    value_type = int
    entity = Person
    definition_period = YEAR
    label = 'Annee_age_ouverture_droits'

    def formula_2006(individu, period, parameters):
        date_de_naissance = individu('date_de_naissance', period)
        aod_active = parameters(period).secteur_public.aod_a.age_ouverture_droits_fonction_publique_active_selon_annee_naissance
        aod_sedentaire = parameters(period).secteur_public.aod_s.age_ouverture_droits_fonction_publique_sedentaire_selon_annee_naissance
        if period.start.year <= 2011:
            aod_sedentaire_annee = aod_sedentaire.before_1951_07_01.annee
            aod_sedentaire_mois = 0
            aod_active_annee = aod_active.before_1956_07_01.annee
            aod_active_mois = 0
        else:
            aod_sedentaire_annee = aod_sedentaire[date_de_naissance].annee
            aod_sedentaire_mois = aod_sedentaire[date_de_naissance].mois
            aod_active_annee = aod_active[date_de_naissance].annee
            aod_active_mois = aod_active[date_de_naissance].mois
        actif_a_la_liquidation = individu('fonction_publique_actif_a_la_liquidation', period)
        aod_annee = where(actif_a_la_liquidation, aod_active_annee, aod_sedentaire_annee)
        aod_mois = where(actif_a_la_liquidation, aod_active_mois, aod_sedentaire_mois)
        annee_age_ouverture_droits = np.trunc(date_de_naissance.astype('datetime64[Y]').astype('int') + 1970 + aod_annee + ((date_de_naissance.astype('datetime64[M]') - date_de_naissance.astype('datetime64[Y]')).astype('int') + aod_mois) / 12).astype(int)
        return annee_age_ouverture_droits

class fonction_publique_aod(Variable):
    value_type = int
    entity = Person
    definition_period = YEAR
    label = "Äge d'ouvertue des droits"

    def formula(individu, period, parameters):
        date_de_naissance = individu('date_de_naissance', period)
        aod_active = parameters(period).secteur_public.aod_a.age_ouverture_droits_fonction_publique_active_selon_annee_naissance[date_de_naissance]
        aod_sedentaire = parameters(period).secteur_public.aod_s.age_ouverture_droits_fonction_publique_sedentaire_selon_annee_naissance[date_de_naissance]
        actif_a_la_liquidation = individu('fonction_publique_actif_a_la_liquidation', period)
        return where(actif_a_la_liquidation, aod_active, aod_sedentaire)

class fonction_publique_bonification_cpcm(Variable):
    value_type = float
    entity = Person
    label = 'bonification pour enfants'
    definition_period = YEAR

    def formula_2004(individu, period, parameters):
        bonification_par_enfant_av_2004 = parameters(period).secteur_public.bonification_enfant.nombre_trimestres_par_enfant_bonification.before_2004_01_01
        nombre_enfants_nes_avant_2004 = individu('fonction_publique_nombre_enfants_nes_avant_2004', period)
        bonification_cpcm = bonification_par_enfant_av_2004 * nombre_enfants_nes_avant_2004
        bonification_par_enfant_pr_2004 = parameters(period).secteur_public.bonification_enfant.nombre_trimestres_par_enfant_bonification.after_2004_01_01
        nombre_enfants_nes_apres_2004 = individu('nombre_enfants', period) - nombre_enfants_nes_avant_2004
        bonification_cpcm = bonification_par_enfant_av_2004 * nombre_enfants_nes_avant_2004 + bonification_par_enfant_pr_2004 * nombre_enfants_nes_apres_2004
        annee_de_liquidation = individu('fonction_publique_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970
        liquidation = annee_de_liquidation == period.start.year
        return bonification_cpcm * liquidation

    def formula_1948(individu, period, parameters):
        bonification_par_enfant_av_2004 = parameters(period).secteur_public.bonification_enfant.nombre_trimestres_par_enfant_bonification.before_2004_01_01
        nombre_enfants = individu('nombre_enfants', period)
        bonification_cpcm = bonification_par_enfant_av_2004 * nombre_enfants
        annee_de_liquidation = individu('fonction_publique_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970
        liquidation = annee_de_liquidation == period.start.year
        return bonification_cpcm * liquidation

class fonction_publique_categorie_activite(Variable):
    value_type = Enum
    possible_values = TypesCategorieActivite
    default_value = TypesCategorieActivite.sedentaire
    entity = Person
    label = "Catégorie d'activité des emplois publics"
    definition_period = YEAR
    set_input = set_input_dispatch_by_period

class fonction_publique_coefficient_de_proratisation(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Coefficient de proratisation'

    def formula(individu, period, parameters):
        date_de_naissance = individu('date_de_naissance', period)
        duree_de_service_effective = individu('fonction_publique_duree_assurance', period)
        bonification_cpcm = individu('fonction_publique_bonification_cpcm', period)
        super_actif = False
        bonification_du_cinquieme = super_actif * min_(duree_de_service_effective / 5, 5)
        duree_assurance_requise = parameters(period).secteur_public.trimtp.nombre_trimestres_cibles_taux_plein_par_generation[date_de_naissance]
        coefficient_de_proratisation = max_(min_(1, (duree_de_service_effective + bonification_du_cinquieme) / duree_assurance_requise), min_(80 / 75, (min_(duree_de_service_effective, duree_assurance_requise) + bonification_cpcm) / duree_assurance_requise))
        return coefficient_de_proratisation

class fonction_publique_cotisation(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'cotisation retraite employeur'

    def formula(individu, period):
        return individu('fonction_publique_cotisation_employeur', period) + individu('fonction_publique_cotisation_salarie', period)

class fonction_publique_cotisation_employeur(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'cotisation retraite employeur'

    def formula(individu, period, parameters):
        NotImplementedError

class fonction_publique_cotisation_salarie(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'cotisation retraite employeur'

    def formula(individu, period, parameters):
        NotImplementedError

class fonction_publique_date_quinze_ans_actif(Variable):
    value_type = date
    entity = Person
    definition_period = YEAR
    label = "Date d'atteinte des quinze ans d'activité en tant qu'actif"

    def formula(individu, period):
        last_year = period.start.period('year').offset(-1)
        nombre_annees_actif_annee_courante = individu('fonction_publique_nombre_annees_actif', period)
        date_actif_annee_precedente = individu('fonction_publique_date_quinze_ans_actif', last_year)
        date = select([date_actif_annee_precedente < np.datetime64('2250-12-31'), nombre_annees_actif_annee_courante <= 15, date_actif_annee_precedente == np.datetime64('2250-12-31')], [date_actif_annee_precedente, np.datetime64('2250-12-31'), np.datetime64(str(period.start))], default=np.datetime64('2250-12-31'))
        return date

class fonction_publique_decote(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'annee_age_ouverture_droits'

    def formula_2006(individu, period, parameters):
        annee_age_ouverture_droits = individu('fonction_publique_annee_age_ouverture_droits', period)
        decote_trimestres = individu('fonction_publique_decote_trimestres', period)
        taux_decote = (annee_age_ouverture_droits >= 2006) * parameters(period).secteur_public.decote.taux_decote_selon_annee_age_ouverture_droits.taux_minore_taux_plein_1_decote_nombre_trimestres_manquants[np.clip(annee_age_ouverture_droits, 2006, 2015)]
        return taux_decote * decote_trimestres

class fonction_publique_decote_trimestres(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'decote trimestres'

    def formula_2006(individu, period, parameters):
        date_de_naissance = individu('date_de_naissance', period)
        actif_a_la_liquidation = individu('fonction_publique_actif_a_la_liquidation', period)
        annee_age_ouverture_droits = individu('fonction_publique_annee_age_ouverture_droits', period)
        aad_en_nombre_trimestres_par_rapport_limite_age = parameters(period).secteur_public.aad.age_annulation_decote_selon_annee_ouverture_droits_en_nombre_trimestres_par_rapport_limite_age
        reduction_add_en_mois = where((2019 >= annee_age_ouverture_droits) * (annee_age_ouverture_droits >= 2006), 3 * aad_en_nombre_trimestres_par_rapport_limite_age[np.clip(annee_age_ouverture_droits, 2006, 2019)], 0)
        aad_en_mois = individu('fonction_publique_limite_d_age', period) * 12 + reduction_add_en_mois
        age_en_mois_a_la_liquidation = (individu('fonction_publique_liquidation_date', period) - individu('date_de_naissance', period)).astype('timedelta64[M]').astype(int)
        trimestres_avant_aad = max_(0, np.ceil((aad_en_mois - age_en_mois_a_la_liquidation) / 3))
        duree_assurance_requise_sedentaires = parameters(period).secteur_public.trimtp.nombre_trimestres_cibles_taux_plein_par_generation[date_de_naissance]
        duree_assurance_requise_actifs = parameters(period).secteur_public.trimtp_a.nombre_trimestres_cibles_taux_plein_par_generation_actifs[date_de_naissance]
        duree_assurance_requise = where(actif_a_la_liquidation, duree_assurance_requise_actifs, duree_assurance_requise_sedentaires)
        trimestres = individu('duree_assurance_cotisee_tous_regimes', period)
        decote_trimestres = min_(max_(0, min_(trimestres_avant_aad, duree_assurance_requise - trimestres)), 20)
        return where(annee_age_ouverture_droits >= 2006, decote_trimestres, 0)

class fonction_publique_dernier_indice_atteint(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Dernier indice connu dans la fonction publique'

    def formula_1970(individu, period, parameters):
        salaire_de_base = individu('salaire_de_base', period)
        taux_de_prime = individu('taux_de_prime', period)
        valeur_point_indice = parameters(period).marche_travail.remuneration_dans_fonction_publique.indicefp.point_indice_en_euros
        dernier_indice = where(salaire_de_base > 0, salaire_de_base / (1 + taux_de_prime) / valeur_point_indice, individu('fonction_publique_dernier_indice_atteint', period.last_year))
        return dernier_indice

class fonction_publique_duree_assurance(Variable):
    value_type = int
    entity = Person
    definition_period = YEAR
    label = "Durée d'assurance (trimestres validés dans la fonction publique)"

class fonction_publique_duree_assurance_assimilee_annuelle(Variable):
    value_type = int
    entity = Person
    definition_period = YEAR
    label = "Durée d'assurance validée au titre des périodes assimilées (en trimestres cotisés seulement l'année considérée)"

class fonction_publique_duree_assurance_cotisee(Variable):
    value_type = int
    entity = Person
    definition_period = YEAR
    label = "Durée d'assurance (trimestres cotisés dans la fonction publique)"

class fonction_publique_duree_assurance_cotisee_annuelle(Variable):
    value_type = int
    entity = Person
    definition_period = YEAR
    label = "Durée d'assurance annuelle pour les périodes cotisées ou faisant l'objet d'un report de salaire au compte (en trimestres cotisés seulement l'année considérée)"

class fonction_publique_limite_d_age(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = "Limite d'âge"

    def formula(individu, period, parameters):
        date_de_naissance = individu('date_de_naissance', period)
        actif_a_la_liquidation = individu('fonction_publique_actif_a_la_liquidation', period)
        limite_age_active = parameters(period).secteur_public.la_a.age_limite_fonction_publique_active_selon_annee_naissance
        limite_age_sedentaire = parameters(period).secteur_public.la_s.age_limite_fonction_publique_sedentaire_selon_annee_naissance
        if period.start.year <= 2011:
            limite_age_active_annee = limite_age_active.before_1956_07_01.annee
            limite_age_active_mois = 0
            limite_age_sedentaire_annee = limite_age_sedentaire.before_1951_07_01.annee
            limite_age_sedentaire_mois = 0
        else:
            limite_age_active_annee = limite_age_active[date_de_naissance].annee
            limite_age_active_mois = limite_age_active[date_de_naissance].mois
            limite_age_sedentaire_annee = limite_age_sedentaire[date_de_naissance].annee
            limite_age_sedentaire_mois = limite_age_sedentaire[date_de_naissance].mois
        limite_age_actif = limite_age_active_annee + limite_age_active_mois / 12
        limite_age_sedentaire = limite_age_sedentaire_annee + limite_age_sedentaire_mois / 12
        return where(actif_a_la_liquidation, limite_age_actif, limite_age_sedentaire)

class fonction_publique_liquidation_date(Variable):
    value_type = date
    entity = Person
    definition_period = ETERNITY
    label = 'Date de liquidation'
    default_value = date(2250, 12, 31)

class fonction_publique_majoration_pension(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Majoration de pension'

    def formula_2004(individu, period):
        nombre_enfants = individu('nombre_enfants', period)
        pension_brute = individu('fonction_publique_pension_brute', period)
        return pension_brute * (0.1 * (nombre_enfants >= 3) + 0.05 * max_(nombre_enfants - 3, 0))

class fonction_publique_majoration_pension_au_31_decembre(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Majoration de pension au 31 décembre'

    def formula(individu, period, parameters):
        annee_de_liquidation = individu('fonction_publique_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970
        if all(annee_de_liquidation > period.start.year):
            return individu.empty_array()
        last_year = period.start.period('year').offset(-1)
        majoration_pension_au_31_decembre_annee_precedente = individu('fonction_publique_majoration_pension_au_31_decembre', last_year)
        revalorisation = parameters(period).secteur_public.revalorisation_pension_au_31_decembre
        majoration_pension = individu('fonction_publique_majoration_pension', period)
        return revalorise(majoration_pension_au_31_decembre_annee_precedente, majoration_pension, annee_de_liquidation, revalorisation, period)

class fonction_publique_minimum_garanti(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Minimum garanti de la fonction publique'
    reference = 'Loi 75-1242 du 27 décembre 1975'

    def formula_1976(individu, period, parameters):
        date_de_naissance = individu('date_de_naissance', period)
        liquidation_date = individu('fonction_publique_liquidation_date', period)
        annee_de_liquidation = individu('fonction_publique_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970
        duree_de_service_effective = individu('fonction_publique_duree_assurance', period)
        decote = individu('fonction_publique_decote', period)
        service_public = parameters(period).secteur_public
        minimum_garanti = service_public.minimum_garanti
        points_moins_40_ans = minimum_garanti.points_moins_40_ans.point_annee_supplementaire_moins_40_ans[liquidation_date]
        points_plus_15_ans = minimum_garanti.points_plus_15_ans.point_annee_supplementaire_plus_15_ans[liquidation_date]
        annee_moins_40_ans = minimum_garanti.annee_moins_40_ans.annee_supplementaire_moins_40_ans[liquidation_date]
        part_fixe = service_public.part_valeur_indice_majore.part_indice_majore_en_euros[liquidation_date]
        indice_majore = service_public.valeur_indice_maj.indice_majore_en_euros[liquidation_date]
        pt_indice = parameters(period).marche_travail.remuneration_dans_fonction_publique.indicefp.point_indice_en_euros
        duree_assurance_requise = service_public.trimtp.nombre_trimestres_cibles_taux_plein_par_generation[date_de_naissance]
        coefficient_moins_15_ans = duree_de_service_effective / duree_assurance_requise
        coefficient_plus_15_ans = part_fixe + max_(duree_de_service_effective - 4 * 15, 0) * points_plus_15_ans
        coefficient_plus_30_ans = part_fixe + 4 * 15 * points_plus_15_ans + max_(duree_de_service_effective - annee_moins_40_ans, 0) * points_moins_40_ans
        coefficient_plus_40_ans = 1
        condition_absence_decote = decote == 0
        condition_duree = duree_de_service_effective > duree_assurance_requise
        post_condition = where(annee_de_liquidation < 2011, True, condition_duree + condition_absence_decote)
        return post_condition * indice_majore * pt_indice * select([duree_de_service_effective < 60, duree_de_service_effective < annee_moins_40_ans, duree_de_service_effective < 160, duree_de_service_effective >= 160], [coefficient_moins_15_ans, coefficient_plus_15_ans, coefficient_plus_30_ans, coefficient_plus_40_ans])

class fonction_publique_nombre_annees_actif(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = "Nombre d'années travaillant en tant qu'actif"

    def formula(individu, period):
        annee_de_liquidation = individu('fonction_publique_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970
        if all(period.start.year > annee_de_liquidation):
            return individu.empty_array()
        last_year = period.start.period('year').offset(-1)
        nombre_annees_actif_annee_precedente = individu('fonction_publique_nombre_annees_actif', last_year)
        categorie_activite = individu('fonction_publique_categorie_activite', period)
        return nombre_annees_actif_annee_precedente + 1 * (categorie_activite == TypesCategorieActivite.actif)

class fonction_publique_nombre_enfants_nes_avant_2004(Variable):
    value_type = int
    entity = Person
    label = "Nombre d'enfants nés avant 2004"
    definition_period = ETERNITY

class fonction_publique_pension(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Pension'

    def formula(individu, period):
        pension_brute = individu('fonction_publique_pension_brute', period)
        majoration_pension = individu('fonction_publique_majoration_pension', period)
        pension_maximale = individu('fonction_publique_salaire_de_reference', period)
        return min_(pension_brute + majoration_pension, pension_maximale)

class fonction_publique_pension_au_31_decembre(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Pension'

    def formula(individu, period):
        pension_brute_au_31_decembre = individu('fonction_publique_pension_brute_au_31_decembre', period)
        majoration_pension_au_31_decembre = individu('fonction_publique_majoration_pension_au_31_decembre', period)
        return pension_brute_au_31_decembre + majoration_pension_au_31_decembre

class fonction_publique_pension_avant_minimum_et_plafonnement(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Pension brute'

    def formula(individu, period):
        coefficient_de_proratisation = individu('fonction_publique_coefficient_de_proratisation', period)
        salaire_de_reference = individu('fonction_publique_salaire_de_reference', period)
        taux_de_liquidation = individu('fonction_publique_taux_de_liquidation', period)
        return coefficient_de_proratisation * salaire_de_reference * taux_de_liquidation

class fonction_publique_pension_brute(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Pension brute'

    def formula(individu, period, parameters):
        pension_avant_minimum_et_plafonnement = individu('fonction_publique_pension_avant_minimum_et_plafonnement', period)
        minimum_garanti = individu('fonction_publique_minimum_garanti', period)
        return max_(pension_avant_minimum_et_plafonnement, minimum_garanti)

class fonction_publique_pension_brute_au_31_decembre(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Pension brute au 31 décembre'

    def formula(individu, period, parameters):
        annee_de_liquidation = individu('fonction_publique_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970
        if all(annee_de_liquidation > period.start.year):
            return individu.empty_array()
        last_year = period.start.period('year').offset(-1)
        pension_brute_au_31_decembre_annee_precedente = individu('fonction_publique_pension_brute_au_31_decembre', last_year)
        revalorisation = parameters(period).secteur_public.revalorisation_pension_au_31_decembre
        pension_brute = individu('fonction_publique_pension_brute', period)
        return revalorise(pension_brute_au_31_decembre_annee_precedente, pension_brute, annee_de_liquidation, revalorisation, period)

class fonction_publique_pension_servie(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Pension servie'

    def formula(individu, period, parameters):
        annee_de_liquidation = individu('fonction_publique_liquidation_date', period).astype('datetime64[Y]').astype(int) + 1970
        if all(annee_de_liquidation > period.start.year):
            return individu.empty_array()
        last_year = period.start.period('year').offset(-1)
        pension_au_31_decembre_annee_precedente = individu('fonction_publique_pension_au_31_decembre', last_year)
        revalorisation = parameters(period).secteur_public.revalarisation_pension_servie
        pension = individu('fonction_publique_pension_au_31_decembre', period)
        return revalorise(pension_au_31_decembre_annee_precedente, pension, annee_de_liquidation, revalorisation, period)

class fonction_publique_salaire_de_reference(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Traitement de référence'

    def formula(individu, period, parameters):
        dernier_indice_atteint = individu('fonction_publique_dernier_indice_atteint', period)
        try:
            valeur_point_indice = parameters(period).marche_travail.remuneration_dans_fonction_publique.indicefp.point_indice_en_euros
        except ParameterNotFound:
            valeur_point_indice = 0
        return dernier_indice_atteint * valeur_point_indice

class fonction_publique_surcote(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Surcote'

    def formula_2004(individu, period, parameters):
        surcote_trimestres = individu('fonction_publique_surcote_trimestres_avant_minimum', period)
        actif_a_la_liquidation = individu('fonction_publique_actif_a_la_liquidation', period)
        taux_surcote = parameters(period).secteur_public.surcote.taux_surcote_par_trimestre
        return where(actif_a_la_liquidation, 0, taux_surcote * surcote_trimestres)

class fonction_publique_surcote_trimestres(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Trimestres surcote'

    def formula_2004(individu, period):
        minimum_garanti = individu('fonction_publique_minimum_garanti', period)
        pension_brute = individu('fonction_publique_pension_brute', period)
        surcote_trimestres_avant_minimum = individu('fonction_publique_surcote_trimestres_avant_minimum', period)
        return where(pension_brute > minimum_garanti, surcote_trimestres_avant_minimum, 0)

class fonction_publique_surcote_trimestres_avant_minimum(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Trimestres surcote avant application du minimum garanti'

    def formula_2004(individu, period, parameters):
        liquidation_date = individu('fonction_publique_liquidation_date', period)
        date_de_naissance = individu('date_de_naissance', period)
        aod_sedentaire = parameters(period).secteur_public.aod_s.age_ouverture_droits_fonction_publique_sedentaire_selon_annee_naissance
        if period.start.year <= 2011:
            aod_sedentaire_annee = aod_sedentaire.before_1951_07_01.annee
            aod_sedentaire_mois = 0
        else:
            aod_sedentaire_annee = aod_sedentaire[date_de_naissance].annee
            aod_sedentaire_mois = aod_sedentaire[date_de_naissance].mois
        age_en_mois_a_la_liquidation = (individu('fonction_publique_liquidation_date', period) - individu('date_de_naissance', period)).astype('timedelta64[M]').astype(int)
        arrondi_trimestres_aod = np.ceil if period.start.year <= 2009 else np.floor
        trimestres_apres_aod = max_(0, (age_en_mois_a_la_liquidation - (12 * aod_sedentaire_annee + aod_sedentaire_mois)) / 3)
        duree_assurance_requise = parameters(period).secteur_public.trimtp.nombre_trimestres_cibles_taux_plein_par_generation[date_de_naissance]
        duree_assurance_excedentaire = individu('duree_assurance_cotisee_tous_regimes', period) - duree_assurance_requise
        trimestres_surcote = max_(0, arrondi_trimestres_aod(min_(trimestres_apres_aod, duree_assurance_excedentaire)))
        return where(liquidation_date < np.datetime64('2010-11-11'), min_(trimestres_surcote, 20), trimestres_surcote)

class fonction_publique_taux_de_liquidation(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Taux de liquidation de la pension'

    def formula(individu, period, parameters):
        decote = individu('fonction_publique_decote', period)
        surcote = individu('fonction_publique_surcote', period)
        taux_plein = parameters(period).secteur_public.taux_plein.taux_plein
        return taux_plein * (1 - decote + surcote)

class fonction_publique_taux_de_liquidation_proratise(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Taux de liquidation proratisé'

    def formula(individu, period):
        return individu('fonction_publique_taux_de_liquidation', period) * individu('fonction_publique_coefficient_de_proratisation', period)