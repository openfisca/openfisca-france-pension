from pathlib import Path
import pandas as pd
import pkg_resources


from openfisca_france_pension.revalorisation import build_revalorisation_dataframe, yaml


directory_path = (
    Path(pkg_resources.get_distribution("openfisca-france-pension").location)
    / "openfisca_france_pension"
    / "parameters"
    / "secteur_prive"
    / "regime_general_cnav"
    )


def get_yearly_revalorisation_pension_servie_coefficient_at_period(year, revalorisation_parameter_path):
    start_date = pd.to_datetime(f"{year - 1}-12-31")
    end_date = pd.to_datetime(f"{year}-12-31")

    df = build_revalorisation_dataframe(revalorisation_parameter_path)
    df = df.loc[(start_date < df.index) & (df.index <= end_date)]
    if df.empty:
        return {"value": 1.0}

    reval = df.sort_index().value.cumprod()
    reval = reval.reset_index()
    reval['share'] = reval.period.shift(-1).dt.month - reval.period.dt.month
    reval.loc[reval.index[-1], 'share'] = 12 - reval['share'].sum()
    reval['share'] = reval['share'] / reval['share'].sum()
    coefficient = (reval['share'] * reval['value']).sum()
    return {"value": float(coefficient)}


def get_yearly_revalorisation_pension_au_31_decembre_coefficient_at_period(year, revalorisation_parameter_path):
    start_date = pd.to_datetime(f"{year - 1}-12-31")
    end_date = pd.to_datetime(f"{year}-12-31")

    df = build_revalorisation_dataframe(revalorisation_parameter_path)
    df = df.loc[(start_date < df.index) & (df.index <= end_date)]

    if df.empty:
        return {"value": 1.0}

    coefficient = df.sort_index().value.cumprod()
    return {"value": float(coefficient.loc[coefficient.index[-1]])}


def build_coefficients_by_annee_pension(export = True):
    revalorisation_parameter_path = directory_path / "reval_p.yaml"
    df = build_revalorisation_dataframe(revalorisation_parameter_path)
    year_min, year_max = df.index.min().year, df.index.max().year

    coefficient_by_annee_pension = dict(
        (f"{annee_pension}-01-01", get_yearly_revalorisation_pension_servie_coefficient_at_period(annee_pension, revalorisation_parameter_path))
        for annee_pension in range(year_max, year_min, -1)
        )

    coefficient_by_annee_pension_complete = dict()
    coefficient_by_annee_pension_complete['description'] = "Coefficient de revalorisation par année de perception des pensions servies par rapport à la pension au 31 décembre"
    coefficient_by_annee_pension_complete.update(dict(values = coefficient_by_annee_pension))

    if export:
        revalorisation_pension_servie_path = directory_path / "revalorisation_pension_servie.yaml"
        with open(revalorisation_pension_servie_path, "w", encoding = 'utf-8') as yaml_file:
            yaml.dump(coefficient_by_annee_pension_complete, yaml_file, encoding = 'utf-8', default_flow_style = False)  # ,, default_style = None)

    coefficient_by_annee_pension = dict(
        (f"{annee_pension}-01-01", get_yearly_revalorisation_pension_au_31_decembre_coefficient_at_period(annee_pension, revalorisation_parameter_path))
        for annee_pension in range(year_max, year_min, -1)
        )
    coefficient_by_annee_pension_complete = dict()
    coefficient_by_annee_pension_complete['description'] = "Coefficient de revalorisation cummulée par année de perception de la valeur des pensions au 31 décembre"
    coefficient_by_annee_pension_complete.update(dict(values = coefficient_by_annee_pension))

    if export:
        revalorisation_pension_servie_path = directory_path / "revalorisation_pension_au_31_decembre.yaml"
        with open(revalorisation_pension_servie_path, "w", encoding = 'utf-8') as yaml_file:
            yaml.dump(coefficient_by_annee_pension_complete, yaml_file, encoding = 'utf-8', default_flow_style = False)  # ,, default_style = None)


if __name__ == "__main__":
    build_coefficients_by_annee_pension(export = True)