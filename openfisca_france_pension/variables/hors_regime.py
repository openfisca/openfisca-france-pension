"""Variables communes à tout les régimes."""

from openfisca_core.model_api import *
# from openfisca_core.periods import ETERNITY, MONTH, YEAR
# from openfisca_core.variables import Variable
from openfisca_france_pension.entities import Person


class age_au_31_decembre(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Age'

    def formula(individu, period):
        # https://stackoverflow.com/questions/13648774/get-year-month-or-day-from-numpy-datetime64
        annee_de_naissance = individu('date_de_naissance', period).astype('datetime64[Y]').astype(int) + 1970
        return period.start.year - annee_de_naissance

class salaire_de_base(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Salaire de base (salaire brut)'


class date_de_naissance(Variable):
    value_type = date
    entity = Person
    definition_period = ETERNITY
    label = 'Date de naissance'
