import pandas as pd
import numpy as np
import glob

# Informations sur les produits
producs_info = [
    {
        "name": "Barre de silicium",
        "unit_price": 150,
        "delai": 4,
        "security_stock": 2000,
        "EC": 4000,
        "PC": 2000,
    },
    {
        "name": "kit laminage",
        "unit_price": 70,
        "delai": 4,
        "security_stock": 2000,
        "EC": 5000,
        "PC": 2000,
    },
    {
        "name": "Kit électronique",
        "unit_price": 50,
        "delai": 6,
        "security_stock": 3250,
        "EC": 6000,
        "PC": 3250,
    },
    {
        "name": "Structure",
        "unit_price": 20,
        "delai": 6,
        "security_stock": 3250,
        "EC": 8250,
        "PC": 3250,
    },
]


def moving_average_growth_rate(
    df: pd.DataFrame, window: int = 3, column: str = "Demand"
) -> pd.DataFrame:
    """Calcule la moyenne mobile et le taux de croissance"""
    df["MA"] = df[column].rolling(window=window).mean()
    df["GR_MA"] = df["MA"].pct_change()
    return df


def weighted_moving_average_rate(
    df: pd.DataFrame,
    window: int = 3,
    column: str = "Demand",
    security_rate: float = 1.0,
) -> pd.DataFrame:
    """Calcule la moyenne mobile pondérée et le taux de croissance"""
    weights = np.exp(np.arange(1, window + 1) * (1 / window))
    weights = weights / weights.sum()
    df["WMA"] = (
        df[column].rolling(window=window).apply(lambda x: np.dot(x, weights))
        * security_rate
    )
    df["GR_WMA"] = df["WMA"].pct_change()
    return df


def predict_demande_using_weighted_moving_average(
    df: pd.DataFrame,
    window: int = 3,
    column: str = "Demand",
    security_rate: float = 1.0,
) -> pd.DataFrame:
    """Prédit la demande en utilisant la moyenne mobile pondérée"""
    weights = np.exp(np.arange(1, window + 1) * (1 / window))
    weights = weights / weights.sum()
    df["WMA"] = (
        df[column].rolling(window=window).apply(lambda x: np.dot(x, weights))
        * security_rate
    )
    return df


def forcast_n_nexth_days(
    df: pd.DataFrame,
    forcast_n: int = 3,
    method: str = "WMA",
) -> list[float]:
    """Prédit la demande pour les prochains jours"""
    last_known_value = df.iloc[-1][method]
    forcast = []

    for i in range(forcast_n):
        forcast_value = last_known_value * (1 + df.iloc[-1][f"GR_{method}"])
        forcast.append(forcast_value)
        last_known_value = forcast_value

    return forcast


def calculate_economique_size_based_on_n_observation(
    df: pd.DataFrame,
    unit_price: float,
    order_fee: float = 1500.0,
    taux_stockage: float = 0.3,
    n_observation: int = 3,
) -> float:
    """Calcule la taille économique basée sur les observations"""
    forcast_next_n_days = df.iloc[-n_observation:]["Demand"].to_numpy()
    total_quantity = forcast_next_n_days.sum() * 10 / n_observation * 365
    Qe = np.sqrt(2 * order_fee * total_quantity / (unit_price * taux_stockage))

    return Qe, Qe * unit_price


def clear_history_text(x):
    """Clear text from history dataframe row
    Args:
        x (str): text to clear
    Returns:
        x (str): cleared text
    """
    x = str(x)
    if "€" in x:
        x = (
            x.replace(" ", "")
            .replace("€", "")
            .replace("$", "")
            .replace(",", ".")
            .replace("\xa0", "")
        )
    else:
        x = (
            x.replace(" ", "")
            .replace("€", "")
            .replace("$", "")
            .replace(",", "")
            .replace("\xa0", "")
        )

    # print(x)
    if "(" in x:
        x = x.replace(" ", "")
        x = x.replace("(", "").replace(")", "")
        x = "-" + str(x)
    else:
        x = x.replace(" ", "")
        x = str(x)
    return x


def make_history_df(team_name: str = "Serious team", path: str = "data/history/*.csv"):
    """Make history dataframe from csv files
    Args:
        team_name (str, optional): team name. Defaults to "Serious team".
        path (str, optional): path to csv files. Defaults to "data/history/*.csv".
    Returns:
        team_data (pd.DataFrame): team data
    """
    history_data = glob.glob(path)
    dataframes = []

    for csv in history_data:
        df = pd.read_csv(csv, index_col=0)
        df["model"] = int(
            csv.split("\\")[-1]
            .split(".")[0]
            .replace("ranking", "")
            .replace("-missing", "")
        )
        dataframes.append(df)

    df = pd.concat(dataframes)
    team_data = df[df["Team"] == team_name].copy()

    team_data["Cash"] = (
        team_data["Cash"].apply(lambda x: clear_history_text(x)).astype(float)
    )
    team_data.sort_values(by=["model"], inplace=True, ascending=True)

    team_data["Cash_diff"] = team_data["Cash"].diff()
    team_data["Orders_diff"] = team_data["Orders Out"].diff()
    team_data["Net_gain"] = (
        team_data["Cash_diff"] / team_data["Orders_diff"] - 2900
    ) * team_data["Orders_diff"]
    team_data["Positive_net_gain"] = team_data["Net_gain"].apply(
        lambda x: x if x > 0 else 0
    )

    return team_data
