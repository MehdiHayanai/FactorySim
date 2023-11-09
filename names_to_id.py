# team name to ids_dict
import json
import pandas as pd

name_to_id = {}
data = pd.read_csv("data/extended/ranking_extended240.csv", index_col=0)
for indx, row in data.iterrows():
    name_to_id[row["teamName"]] = row["id"]

# save as json file
with open("data/ids/name_to_id.json", "w") as f:
    json.dump(name_to_id, f)
