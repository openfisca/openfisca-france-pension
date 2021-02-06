"""Variables communes à tout les régimes."""

from openfisca_core.model_api import *
# from openfisca_core.periods import ETERNITY, MONTH, YEAR
# from openfisca_core.variables import Variable
from openfisca_france_pension.entities import Person


class salaire_de_base(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = 'Salaire de base (salaire brut)'
