import pandas as pd
import numpy as np

# Informations sur les produits
producs_info = [
    {
        "name": "Barre de silicium",
        "unit_price": 150,
        "delai": 4,
        "security_stock": 1000,
    },
    {
        "name": "kit laminage",
        "unit_price": 70,
        "delai": 4,
        "security_stock": 1000,
    },
    {
        "name": "Kit électronique",
        "unit_price": 50,
        "delai": 6,
        "security_stock": 2000,
    },
    {
        "name": "Structure",
        "unit_price": 20,
        "delai": 6,
        "security_stock": 2000,
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
