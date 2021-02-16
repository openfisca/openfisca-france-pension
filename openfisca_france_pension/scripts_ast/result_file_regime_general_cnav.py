from datetime import date
from openfisca_core.model_api import max_
from openfisca_core.periods import ETERNITY, MONTH, YEAR
from openfisca_core.variables import Variable
from openfisca_france_pension.entities import Household, Person
'Régime de base du secteur privé: régime général de la CNAV.'
from openfisca_france_pension.regimes.regime import AbstractRegimeDeBase
from openfisca_core.periods import ETERNITY, MONTH, YEAR
from openfisca_core.variables import Variable
from openfisca_france_pension.entities import Household, Person

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

    def formula(individu, period, parameters):
        taux = parameters(period).secteur_prive.regime_general_cnav.decote.taux
        trimestres_debut = parameters(period).secteur_prive.regime_general_cnav.decote.trimestres_debut
        trimestres = individu('regime_general_cnav_trimestres', period)
        return taux * max_(trimestres - trimestres_debut, 0)

class regime_general_cnav_pension_brute(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Pension brute'

    def formula(individu, period, parameters):
        coefficient_de_proratisation = individu('regime_general_cnav_coefficient_de_proratisation', period)
        salaire_de_reference = individu('regime_general_cnav_salaire_de_reference', period)
        taux_de_liquidation = individu('regime_general_cnav_taux_de_liquidation', period)
        return coefficient_de_proratisation * salaire_de_reference * taux_de_liquidation

class regime_general_cnav_pension(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Pension'

    def formula(individu, period):
        pension_brute = individu('regime_general_cnav_pension_brute', period)
        majoration_pension = individu('regime_general_cnav_majoration_pension', period)
        return pension_brute + majoration_pension

class regime_general_cnav_surcote_debut_date(Variable):
    value_type = date
    entity = Person
    definition_period = ETERNITY
    label = 'Date du début de la surcote'

class regime_general_cnav_decote_annulation_date(Variable):
    value_type = date
    entity = Person
    definition_period = ETERNITY
    label = "Date d'annulation de la décote'"

class regime_general_cnav_taux_plein_date(Variable):
    value_type = date
    entity = Person
    definition_period = ETERNITY
    label = 'Date du taux plein'

class regime_general_cnav_taux_de_liquidation(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Taux de liquidation de la pension'

    def formula(individu, period, parameters):
        decote = individu('regime_general_cnav_decote', period)
        surcote = individu('regime_general_cnav_surcote', period)
        taux_plein = parameters(period).secteur_prive.regime_general_cnav.taux_plein
        return taux_plein * (1 - decote + surcote)

class regime_general_cnav_cotisation_retraite(Variable):
    value_type = float
    entity = Person
    definition_period = MONTH
    label = 'cotisation retraite'

    def formula(individu, period, parameters):
        salaire_de_base = individu('salaire_de_base', period)
        taux = parameters(period).secteur_prive.regime_general_cnav.cotisation.taux
        return salaire_de_base * taux

class regime_general_cnav_trimestres_cotises(Variable):
    value_type = int
    entity = Person
    definition_period = YEAR
    label = 'Trimestres cotisés au régime général'

class regime_general_cnav_age_ouverture_des_droits(Variable):
    value_type = float
    entity = Person
    definition_period = ETERNITY
    label = "Age d'ouverture des droits"

class regime_general_cnav_salaire_de_reference(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Salaire annuel moyen de base dit salaire de référence'

class regime_general_cnav_age_annulation_decote(Variable):
    value_type = float
    entity = Person
    definition_period = ETERNITY
    label = "Age d'annulation de la décôte"

class regime_general_cnav_coefficient_de_proratisation(Variable):
    value_type = float
    entity = Person
    definition_period = ETERNITY
    label = 'Coefficient de proratisation'

class regime_general_cnav_surcote(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Surcote'

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