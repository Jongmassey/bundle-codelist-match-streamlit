import json
from pathlib import Path

import pandas as pd
import streamlit as st


st.set_page_config(layout="wide")

df = pd.read_csv("data/candidate_matches_jaccard.csv")
fixed_columns = list(df.columns.values)
df[["match"]] = False

matches_path = Path("matches.json")
matches = []
if matches_path.exists():
    with matches_path.open() as f:
        matches = json.load(f)
    for match in matches:
        bundle_id = match["bundle_id"]
        refset_url = match["refset_url"]
        df.loc[
            (df.bundle_id == bundle_id) & (df.refset_url == refset_url), ["match"]
        ] = True


def df_edited_callback():
    edited_rows = st.session_state["df_data"]["edited_rows"]
    for k, v in edited_rows.items():
        match = v["match"]
        bundle_id, refset_url = df.loc[int(k), ["bundle_id", "refset_url"]].values
        match_dict = {"bundle_id": bundle_id, "refset_url": refset_url}
        if match and match_dict not in matches:
            matches.append(match_dict)
        else:
            if match_dict in matches:
                matches.remove(match_dict)
    with matches_path.open("w") as f:
        json.dump(matches, f, indent=4)


st.data_editor(
    data=df,
    column_config={
        "match": st.column_config.CheckboxColumn("Good Match?", default=False)
    },
    hide_index=True,
    disabled=fixed_columns,
    key="df_data",
    on_change=df_edited_callback,
)
