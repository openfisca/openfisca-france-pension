import configparser
import logging
import os
import pandas as pd
import pyreadr



from openfisca_core import periods
from openfisca_survey_manager.scenarios import AbstractSurveyScenario
from openfisca_survey_manager import default_config_files_directory as config_files_directory

from openfisca_france_pension import CountryTaxBenefitSystem as FrancePensionTaxBenefitSystem



log = logging.getLogger(__name__)


config_parser = configparser.ConfigParser()
config_parser.read(os.path.join(config_files_directory, 'raw_data.ini'))


class DestinieSurveyScenario(AbstractSurveyScenario):
    """OpenFisca survey scenario to compute French Pensions"""

    def __init__(self, tax_benefit_system = None, baseline_tax_benefit_system = None, year = None,
            data = None):
        super(DestinieSurveyScenario, self).__init__()

        if tax_benefit_system is None:
            tax_benefit_system = FrancePensionTaxBenefitSystem()
        self.set_tax_benefit_systems(
            tax_benefit_system = tax_benefit_system,
            baseline_tax_benefit_system = baseline_tax_benefit_system,
            )

        assert 'input_data_frame_by_entity_by_period' in data
        period = max(list(data['input_data_frame_by_entity_by_period'].keys()))
        self.year = periods.period(2000)
        dataframe_variables = set()
        for entity_dataframe in data['input_data_frame_by_entity_by_period'][period].values():
            if not isinstance(entity_dataframe, pd.DataFrame):
                continue
            dataframe_variables = dataframe_variables.union(set(entity_dataframe.columns))
        self.used_as_input_variables = list(
            set(tax_benefit_system.variables.keys()).intersection(dataframe_variables)
            )

        self.init_from_data(data = data)


def create_input_data(sample_size = None):
    """Creates input data from liam2 output to use in DestinieSurveyScenario

    Returns:
        dict: Input data frames by entity by period
    """

    # https://framagit.org/ipp/retraites_ipp/-/blob/master/PENSIPP%200.2/Modele/Bios/BiosDestinie.R

    if not config_parser.has_section("destinie"):
        return

    destinie_path = config_parser.get('destinie', 'data_directory')
    ech_file_name = "ech_pour_IPP_cho7%_pib1,3%_date2017-07-12.Rda"
    emp_file_name = "emp_pour_IPP_cho7%_pib1,3%_date2017-07-12.Rda"
    fam_file_name = "fam_pour_IPP_cho7%_pib1,3%_date2017-07-12.Rda"

    ech = (pyreadr.read_r(os.path.join(destinie_path, ech_file_name))['ech']
        .rename(columns = dict(Id = "person_id"))
        .eval('person_id = person_id - 1')
        )
    emp = (pyreadr.read_r(os.path.join(destinie_path, emp_file_name))['emp']
        .rename(columns = dict(Id = "person_id"))
        .eval('person_id = person_id - 1')
        )
    fam = (pyreadr.read_r(os.path.join(destinie_path, fam_file_name))['fam']
        .rename(columns = dict(Id = "person_id"))
        .eval('person_id = person_id - 1')
        )
    assert set(ech.person_id.unique()) >= set(emp.person_id.unique())
    assert set(ech.person_id.unique()) == set(fam.person_id.unique())

    if sample_size is not None:
        if sample_size >= ech.person_id.max() + 1:
            log.info('Sample size argument is larger than orginal data. Use originale data')
        else:
            # TODO if statistic significane is needed use resampling and seed
            log.info(f'Sample size is {sample_size}')
            ech = ech.query('person_id < @sample_size')
            emp = emp.query('person_id < @sample_size')
            fam = fam.query('person_id < @sample_size')

    ech["date_de_naissance"] = pd.to_datetime(
        ech[['anaiss', 'moisnaiss']]
            .eval("day = 1")
            .rename(columns = dict(anaiss = "year", moisnaiss = "month"))
            .eval("month = month + 1")
        ).values.astype('datetime64[D]')

    ech = ech.drop(["anaiss", "moisnaiss"], axis = 1)
    emp = emp.merge(ech[["person_id", 'date_de_naissance']], on = "person_id")
    emp['period'] = emp.date_de_naissance.dt.year + emp.age

    def int_dtype_from_values(values):
        from math import log, floor
        if min(values) >= 0:
            prefix = 'u'
            top_value = max(values)
        else:
            prefix = ''
            top_value = 2 * max(max(values), -min(values))

        ns = [8, 16, 32, 64]
        for n in ns:
            if top_value < 2 ** n:
                return prefix + 'int' + str(n)

        return None

    emp = emp.astype(dict(
        person_id = int_dtype_from_values(emp.person_id),
        period = int_dtype_from_values(emp.period),
        ))

    _ids = list(sorted(emp.person_id.unique()))
    _periods = list(sorted(emp.period.unique()))
    complete_multiindex = pd.MultiIndex.from_product([_ids, _periods], names = ["person_id", 'period'])
    emp = (
        emp[["person_id", 'period', 'salaire']]
        .copy()
        .rename(columns = dict(salaire = "salaire_de_base"))
        )
    emp = (emp
        .set_index(["person_id", 'period'])
        .reindex(complete_multiindex)
        # .fillna({"decede": True})
        .fillna(method = 'ffill')
        .reset_index()
        )
    input_data_frame_by_entity_by_period = dict(
        (
            periods.period(int(period)),
            dict(person = emp.query("period == @period").drop("period", axis = 1))
            )
        for period in sorted(emp.period.unique())
        )

    # codes_statut_by_statut = dict(
    #     inactif = [6, 621, 623, 624, 63],
    #     chomeur = [5, 51, 52],
    #     non_cadre = [1, 11, 12, 13],
    #     cadre = 2,
    #     fonct_a = [311, 331, 312, 332],
    #     fonct_s = [321, 322],
    #     indep = 4,
    #     avpf = 9,
    #     preret = 7,
    #     )

    initial_period = periods.period(int(min(_periods)))
    variables = ["person_id", 'date_de_naissance']
    input_data_frame_by_entity_by_period[initial_period]['person'] = (
        input_data_frame_by_entity_by_period[initial_period]['person'].merge(
            ech[variables],
            on = "person_id"
            )
        )

    return input_data_frame_by_entity_by_period


if __name__ == "__main__":
    input_data_frame_by_entity_by_period = create_input_data(sample_size = None)
    data = dict(input_data_frame_by_entity_by_period = input_data_frame_by_entity_by_period)
    survey_secnario = DestinieSurveyScenario(data = data)
    salaire_de_reference = survey_secnario.calculate_variable('regime_general_cnav_salaire_de_reference', period = 2000)