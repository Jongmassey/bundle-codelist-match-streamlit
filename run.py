import csv
from io import StringIO

import pandas as pd
import streamlit as st
from streamlit import session_state as ss

from matching import matching
from opencodelists import opencodelists


st.set_page_config(layout="wide")

ss.matches = []


def df_edited_callback():
    edited_rows = ss.df_data["edited_rows"]
    for k, v in edited_rows.items():
        match = v["match"]
        bundle_id, codelist_url = ss.results_df.loc[
            int(k), ["bundle_id", "codelist_url"]
        ].values
        match_dict = {"bundle_id": bundle_id, "codelist_url": codelist_url}
        if match and match_dict not in ss.matches:
            ss.matches.append(match_dict)
        else:
            if match_dict in ss.matches:
                ss.matches.remove(match_dict)
    for match in ss.matches:
        bundle_id = match["bundle_id"]
        codelist_url = match["codelist_url"]
        ss.results_df.loc[
            (ss.results_df.bundle_id == bundle_id)
            & (ss.results_df.codelist_url == codelist_url),
            ["match"],
        ] = True


def fetch_codelists():
    ss.codelists = opencodelists.get_codelists(organisation=organisation)


def load_bundle():
    if bundle_file := ss.get("bundle_file"):
        bf_text = StringIO(bundle_file.getvalue().decode("utf-8"))
        ss.bundles = list(csv.DictReader(bf_text))


organisation = st.selectbox(
    label="OpenCodelists Organisation",
    options=opencodelists.ORGANISATIONS,
    key="organisation",
    index=None,
    placeholder="Select OpenCodelist Organisation...",
)

st.button(
    label="Fetch organisation codelists",
    disabled=(organisation is None),
    on_click=fetch_codelists,
)
st.text(
    f"{len(ss.codelists)} codelists loaded"
    if ss.get("codelists")
    else "No organistation loaded",
)

bundle_file = st.file_uploader(
    label="Bundle csv file", type="csv", on_change=load_bundle, key="bundle_file"
)


run_matching = st.button(
    label="Run matching",
    disabled=not bool(ss.get("codelists") and ss.get("bundles")),
)
if run_matching or "results_df" in ss:
    if "results_df" not in ss:
        results = matching.run_match(bundles=ss.bundles, codelists=ss.codelists)
        ss.matching_run = True
        df = pd.DataFrame(results)
        df[["match"]] = False
    else:
        df = ss.results_df
    ss.results_df = st.data_editor(
        data=df,
        column_config={
            "match": st.column_config.CheckboxColumn("Good Match?", default=False)
        },
        hide_index=True,
        disabled=[c for c in df.columns if c != "match"],
        key="df_data",
        on_change=df_edited_callback,
    )
