import pandas as pd
import warnings


def import_yaml():
    import yaml
    try:
        from yaml import CLoader as Loader
    except ImportError:
        message = [
            "libyaml is not installed in your environment.",
            "This can make your test suite slower to run. Once you have installed libyaml, ",
            "run 'pip uninstall pyyaml && pip install pyyaml --no-cache-dir'",
            "so that it is used in your Python environment."
            ]
        warnings.warn(" ".join(message))
        from yaml import SafeLoader as Loader
    return yaml, Loader


yaml, Loader = import_yaml()


def build_revalorisation_dataframe(revalorisation_parameter_path):
    yaml_data = yaml.load(revalorisation_parameter_path.open(), Loader = Loader)
    try:
        data = yaml_data['coefficient']["values"]
    except KeyError:
        data = yaml_data["values"]

    df = pd.DataFrame.from_dict(data, orient = 'index').rename_axis(index = "period").reset_index()
    df["period"] = pd.to_datetime(df.period)
    df.set_index("period", inplace = True)
    df.sort_index(inplace = True)

    df_test = df.reset_index()
    df_test["year"] = df_test.period.dt.year
    assert (df_test.groupby("year")["value"].count().value_counts(dropna = False) >= 1).all()
    return df
