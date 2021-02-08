from datetime import date
from openfisca_core.model_api import max_
from openfisca_core.periods import ETERNITY, MONTH, YEAR
from openfisca_core.variables import Variable
from openfisca_france_pension.entities import Household, Person

class regime_de_base_salaire_de_base(Variable):
    value_type = float
    entity = Person
    definition_period = MONTH
    label = 'Salaire brut'

class regime_de_base_surcote_debut_date(Variable):
    value_type = date
    entity = Person
    definition_period = ETERNITY
    label = 'Date du début de la surcote'

class regime_de_base_decote_annulation_date(Variable):
    value_type = date
    entity = Person
    definition_period = ETERNITY
    label = "Date d'annulation de la décote'"

class regime_de_base_taux_plein_date(Variable):
    value_type = date
    entity = Person
    definition_period = ETERNITY
    label = 'Date du taux plein'

class regime_de_base_taux_de_liquidation(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Taux de liquidation de la pension'

    def formula(individu, period, parameters):
        decote = individu('regime_de_base_decote', period)
        surcote = individu('regime_de_base_surcote', period)
        taux_plein = parameters(period).regime_de_base.taux_plein
        return taux_plein * (1 - decote + surcote)

class regime_de_base_cotisation_retraite(Variable):
    value_type = float
    entity = Person
    definition_period = MONTH
    label = 'cotisation retraite'

    def formula(individu, period, parameters):
        salaire_de_base = individu('salaire_de_base', period)
        taux = parameters(period).regime_de_base.cotisation.taux
        return salaire_de_base * taux

class regime_de_base_salaire_de_reference(Variable):
    value_type = float
    entity = Person
    definition_period = ETERNITY
    label = 'Salaire de référence'

class regime_de_base_trimestres(Variable):
    value_type = int
    entity = Person
    definition_period = YEAR
    label = 'Trimestres'

class regime_de_base_majoration_pension(Variable):
    value_type = int
    entity = Person
    definition_period = MONTH
    label = 'Majoration de pension'

class regime_de_base_decote(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Décote'

    def formula(individu, period, parameters):
        taux = parameters(period).regime_de_base.decote.taux
        trimestres_debut = parameters(period).regime_de_base.decote.trimestres_debut
        trimestres = individu('regime_de_base_trimestres', period)
        return taux * max_(trimestres - trimestres_debut, 0)

class regime_de_base_pension_brute(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Pension brute'

    def formula(individu, period, parameters):
        coefficent_de_proratisation = individu('regime_de_base_coefficent_de_proratisation', period)
        salaire_de_reference = individu('regime_de_base_salaire_de_reference', period)
        taux_de_liquidation = individu('regime_de_base_taux_de_liquidation', period)
        return coefficent_de_proratisation * salaire_de_reference * taux_de_liquidation

class regime_de_base_pension(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Pension'

    def formula(individu, period):
        pension_brute = individu('regime_de_base_pension_brute', period)
        majoration_pension = individu('regime_de_base_majoration_pension', period)
        return pension_brute + majoration_pension