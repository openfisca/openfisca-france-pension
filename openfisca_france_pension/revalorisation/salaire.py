from pathlib import Path
import pandas as pd
import pkg_resources


from openfisca_france_pension.revalorisation import build_revalorisation_dataframe, yaml


directory_path = (
    Path(pkg_resources.get_distribution("openfisca-france-pension").location)
    / "openfisca_france_pension"
    / "parameters"
    / "retraites"
    / "secteur_prive"
    / "regime_general_cnav"
    )


def get_annee_salaire_item(df, annee_salaire):
    start_date = f"{annee_salaire}-12-31"
    value_first_day_of_first_year = df.value.get(f"{annee_salaire + 1}-01-01")
    if value_first_day_of_first_year is None:
        df.loc[pd.to_datetime(f"{annee_salaire + 1}-01-01")] = 1.0
        df.sort_index(inplace = True)

    formatted = df.loc[start_date:, ["value"]].cumprod()
    formatted["period_str"] = formatted.reset_index()['period'].dt.strftime("%Y-%m-%d").astype(str).values
    values = formatted.set_index("period_str", drop = True).to_dict("index")
    return {
        "description": f"Coefficient pour année {annee_salaire}",
        "values": values,
        }


def build_coefficient_by_annee_salaire(export = True):
    df = build_revalorisation_dataframe(revalorisation_parameter_path = directory_path / "reval_s.yaml")

    coefficient_by_annee_salaire = dict(
        (annee_salaire, get_annee_salaire_item(df, annee_salaire))
        for annee_salaire in range(2021, 1948, -1)
        )
    coefficient_by_annee_salaire_complete = dict()
    coefficient_by_annee_salaire_complete['description'] = "Coefficient de revalorisation cummulée par année de perception des salaires"
    coefficient_by_annee_salaire_complete.update(coefficient_by_annee_salaire)

    if export:
        revalorisation_salaire_cummulee_path = directory_path / "revalorisation_salaire_cummulee.yaml"
        with open(revalorisation_salaire_cummulee_path, "w", encoding = 'utf-8') as yaml_file:
            yaml.dump(coefficient_by_annee_salaire_complete, yaml_file, encoding = 'utf-8', default_flow_style = False)  # ,, default_style = None)

    return coefficient_by_annee_salaire_complete


if __name__ == "__main__":
    import pprint
    coefficient_by_annee_salaire_complete = build_coefficient_by_annee_salaire(export = True)
    pprint.pprint(coefficient_by_annee_salaire_complete)  # noqa analysis:ignore
