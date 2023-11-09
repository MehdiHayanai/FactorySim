import requests
import pandas as pd
import numpy as np
from typing import Dict, List, Any


class FactorySimAPI:
    def __init__(
        self,
        SESSION: str,
        VERIFICATION: str,
        USERID: str,
        host: str,
    ):
        self.host = host
        self.USERID = USERID
        self.SESSION = SESSION
        self.VERIFICATION = VERIFICATION
        self.session = self.init_session()

    def init_session(self):
        headers = {
            "Host": "app.factorysim.fr",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3",
            "Accept-Encoding": "gzip, deflate",
            "Referer": "http://app.factorysim.fr/Account/Login?ReturnUrl=%2F",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

        cookies = {
            "__RequestVerificationToken": f"{self.VERIFICATION}",
            ".AspNet.ApplicationCookie": f"{self.SESSION}",
        }
        session = requests.Session()
        session.headers.update(headers)
        session.cookies.update(cookies)
        response = session.get(self.host)

        if response.status_code == 200:
            print("Connection successful")
            return session
        else:
            print("Connection failed")

    def get_current_day(self) -> int:
        current_day_url = self.host + f"CurrentDay/CurrentDay/{self.USERID}"
        day = self.session.get(current_day_url).json()
        return day

    def get_materials(self, day: int) -> List[Dict[str, Any]]:
        materials_url = (
            self.host
            + f"RawMaterialStockHistory/RawMaterialStockHistoryAsync/{self.USERID}?displayLegend=False&maxPointsToShow=365&previousDay=-1&currentDay={day}"
        )
        materials = self.session.get(materials_url)
        return materials.json()

    def get_demand(self, day: int) -> List[Dict[str, Any]]:
        demand_url = (
            self.host
            + f"DemandHistory/DemandHistoryAsync/{self.USERID}?displayLegend=False&maxPointsToShow=365&previousDay=-1&currentDay={day}"
        )
        demand = self.session.get(demand_url)
        return demand.json()

    def get_contracts_type(self, USERID: str = "") -> List[Dict[str, Any]]:
        USERID_TO_SEARCH = self.USERID if USERID == "" else USERID
        contracts_url = (
            self.host
            + f"/IncomeHistory/IncomeHistoryAsync/{USERID_TO_SEARCH}?displayLegend=False&maxPointsToShow=50&previousDay=-1&currentDay=365"
        )

        contracts = self.session.get(contracts_url)
        return contracts.json()

    def get_contract_values(self, USERID: str = "") -> pd.DataFrame:
        contract_type = self.get_contracts_type(USERID)
        columns = []
        data = []
        for option in contract_type["datasets"][:-1]:
            columns.append(option["label"])
            data.append(option["data"])
        contracts = pd.DataFrame(data=np.array(data).T, columns=columns)
        contracts["Choice"] = contracts.apply(lambda x: x.max(), axis=1)

        return contracts

    @staticmethod
    def parse_json_to_columns(data: Dict[str, Any]) -> Dict[str, Any]:
        row = {
            "id": data["id"],
            "teamName": data["teamName"].strip(),
            "cash": str(data["cash"]),
            "currentDay": data["currentDay"],
            "workshopCount": data["workshopCount"],
            "ordersCount": data["ordersCount"],
        }

        workshops = data.get("workshops", [])
        for i, workshop in enumerate(workshops, 1):
            workshop_id = workshop["id"]
            workshop_machine_count = workshop["machineCount"]
            row[f"workshop_{i}_id"] = workshop_id
            row[f"workshop_{i}_machineCount"] = workshop_machine_count

        return row

    def get_rankings(self) -> pd.DataFrame:
        data = []
        rankings_url = self.host + f"Ranking/Ranking/{self.USERID}"
        rankings = self.session.get(rankings_url).json()
        for factory in rankings["factories"]:
            data.append(FactorySimAPI.parse_json_to_columns(factory))
        rankings_data = pd.DataFrame(data)
        return rankings_data

    def get_ranking_reduced(self) -> pd.DataFrame:
        rankings_data = self.get_rankings()
        ranking_reduced = rankings_data[["teamName", "ordersCount", "cash"]]
        ranking_reduced.columns = ["Team", "Orders Out", "Cash"]
        return ranking_reduced

    def save_ranking_to_dir(self, dir="data/history"):
        ranking_reduced = self.get_ranking_reduced()
        day = self.get_current_day()
        absolute_dir = dir + f"/ranking{day}.csv"
        ranking_reduced.to_csv(absolute_dir)
        print(f"Saving ranking to {absolute_dir}")

    def save_extended_ranking_to_dir(self, dir="data/extended"):
        rankings_data = self.get_rankings()
        day = self.get_current_day()
        absolute_dir = dir + f"/ranking_extended{day}.csv"
        rankings_data.to_csv(absolute_dir)
        print(f"Saving ranking to {absolute_dir}")

    def save_all_rankings(self):
        self.save_ranking_to_dir()
        self.save_extended_ranking_to_dir()
