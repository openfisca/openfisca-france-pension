"""OpenFisca-France-Pension Survey Scenario."""

import configparser
import logging
import os
import sys


import numpy as np
import pandas as pd
import pyreadr


from openfisca_core import periods
from openfisca_survey_manager import default_config_files_directory as config_files_directory
from openfisca_survey_manager.input_dataframe_generator import set_table_in_survey
from openfisca_survey_manager.scenarios import AbstractSurveyScenario


from openfisca_france_pension import CountryTaxBenefitSystem as FrancePensionTaxBenefitSystem


log = logging.getLogger(__name__)


config_parser = configparser.ConfigParser()
config_parser.read(os.path.join(config_files_directory, 'raw_data.ini'))


class DestinieSurveyScenario(AbstractSurveyScenario):
    """OpenFisca survey scenario to compute French Pensions."""

    def __init__(self, tax_benefit_system = None, baseline_tax_benefit_system = None, year = None,
            data = None, dataframe_variables = None, comportement_de_depart = None):
        super(DestinieSurveyScenario, self).__init__()

        if tax_benefit_system is None:
            tax_benefit_system = FrancePensionTaxBenefitSystem()

        if comportement_de_depart is not None:
            tax_benefit_system = comportement_de_depart(tax_benefit_system)
            if baseline_tax_benefit_system is not None:
                baseline_tax_benefit_system = comportement_de_depart(baseline_tax_benefit_system)

        self.set_tax_benefit_systems(
            tax_benefit_system = tax_benefit_system,
            baseline_tax_benefit_system = baseline_tax_benefit_system,
            )

        assert (
            'input_data_frame_by_entity_by_period' in data
            or 'input_data_table_by_entity_by_period'
            )

        assert dataframe_variables is not None
        self.used_as_input_variables = list(
            set(tax_benefit_system.variables.keys()).intersection(dataframe_variables)
            )

        # period = min(list(data['input_data_frame_by_entity_by_period'].keys()))
        self.year = periods.period(1909)
        self.collection = "destinie"
        self.init_from_data(data = data)
        self.simulation.max_spiral_loops = np.infty
        if self.baseline_simulation is not None:
            self.baseline_simulation.max_spiral_loops = np.infty


def create_input_data(sample_size = None, save_to_disk = False):
    """Creates input data from destinie data output to use in DestinieSurveyScenario.

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

    ech = (
        pyreadr.read_r(os.path.join(destinie_path, ech_file_name))['ech']
        .rename(columns = dict(Id = "person_id"))
        .eval('person_id = person_id - 1')
        )
    emp = (
        pyreadr.read_r(os.path.join(destinie_path, emp_file_name))['emp']
        .rename(columns = dict(Id = "person_id"))
        .eval('person_id = person_id - 1')
        )
    fam = (
        pyreadr.read_r(os.path.join(destinie_path, fam_file_name))['fam']
        .rename(columns = dict(Id = "person_id"))
        .eval('person_id = person_id - 1')
        )
    assert set(ech.person_id.unique()) >= set(emp.person_id.unique())
    assert set(ech.person_id.unique()) == set(fam.person_id.unique())

    if sample_size is not None:
        if sample_size >= len(ech.person_id.unique()):
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

    # TODO: use https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.to_numeric.html instead of this hack

    def int_dtype_from_values(values):
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
    _periods = list(range(emp.period.min(), emp.period.max() + 1))
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

    # Initialize regime_general_cnav_trimestres to avoid infinite loop
    input_data_frame_by_entity_by_period[initial_period]['person']['regime_general_cnav_trimestres'] = 0

    period = min(list(input_data_frame_by_entity_by_period.keys()))
    dataframe_variables = set()
    for entity_dataframe in input_data_frame_by_entity_by_period[period].values():
        if not isinstance(entity_dataframe, pd.DataFrame):
            continue
        dataframe_variables = dataframe_variables.union(set(entity_dataframe.columns))

    if not save_to_disk:
        return input_data_frame_by_entity_by_period, dataframe_variables

    collection = 'destinie'
    table_by_entity_by_period = dict()

    for period, input_data_frame_by_entity in input_data_frame_by_entity_by_period.items():
        table_by_entity_by_period[period] = table_by_entity = dict()
        for entity, input_dataframe in input_data_frame_by_entity.items():
            set_table_in_survey(input_dataframe, entity, period, collection, survey_name = 'input')
            table_by_entity[entity] = entity + '_' + str(period)

    return table_by_entity_by_period, dataframe_variables


def get_input_data():
    """Gets input data.

    Returns:
        [dict]: data information to run the initialize the scenario's simulation
    """
    table_by_entity_by_period = dict()
    entity = "person"
    for period_ in range(1909, 2070 + 1):
        period = periods.period(period_)
        table_by_entity_by_period[period] = table_by_entity = dict()
        table_by_entity[entity] = entity + '_' + str(period)

    data = dict(
        input_data_table_by_entity_by_period = table_by_entity_by_period,
        survey = 'input',
        )
    return data


if __name__ == "__main__":
    logging.basicConfig(level = logging.DEBUG, stream = sys.stdout)
    from openfisca_france_pension.reforms.comportement_de_depart.age_fixe import create_depart_a_age_fixe
    # input_data_frame_by_entity_by_period, dataframe_variables = create_input_data(sample_size = None)
    # data = dict(input_data_frame_by_entity_by_period = input_data_frame_by_entity_by_period)

    # table_by_entity_by_period, dataframe_variables = create_input_data(sample_size = None, save_to_disk = True)

    dataframe_variables = [
        'date_de_naissance',
        'person_id',
        'regime_general_cnav_trimestres',
        'salaire_de_base'
        ]

    data = get_input_data()

    survey_secnario = DestinieSurveyScenario(
        comportement_de_depart = create_depart_a_age_fixe(65),
        data = data,
        dataframe_variables = dataframe_variables,
        )

    date_de_naissance = survey_secnario.calculate_variable('date_de_naissance', period = 2000)
    date_de_liquidation = survey_secnario.calculate_variable('regime_general_cnav_liquidation_date', period = 2000)
    import time
    start = time.process_time()
    salaire_de_reference = survey_secnario.calculate_variable('regime_general_cnav_salaire_de_reference', period = 2000)
    log.debug(time.process_time() - start)

    _periods = [2018, 2019, 2020]
    for period in _periods:
        salaire_de_base = survey_secnario.calculate_variable('salaire_de_base', period = period)
        log.debug(period, salaire_de_base)

        trimestres = survey_secnario.calculate_variable('regime_general_cnav_trimestres', period = period)
        log.debug(period, trimestres)


openfisca_by_destinie_name = {
    "findet": "age_de_fin_d_etude",
    # "typeFP" (0 état, 1teritoriale, 2 hospitalière)-> "categorie_salarie"
    #   'prive_non_cadre'
    #   'prive_cadre'
    #   'public_titulaire_etat'
    #   'public_titulaire_militaire'
    #   'public_titulaire_territoriale'
    #   'public_titulaire_hospitaliere'
    #   'public_non_titulaire'
    #   'non_pertinent'
    # "taux_prim" -> "primes_fonction_publique"
    # neFrance -> nationalite
    # emigrant -> ?
    #
    }
