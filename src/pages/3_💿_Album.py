"""
Author: Peter Akioyamen
Github: @peter-ai

A web application which uses audio feature data from the Free Music Archive (FMA; 2018)
to create visual acoustic fingerprints of songs and compare audio characteristics across the
music catalogue. The app uses a MySQL backend and is built on Streamlit.

Album Page of the Acoustic Print web app
"""
# import external dependencies
import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode


def main():
    # define local page config
    st.set_page_config(layout="wide", page_title="Acoustic Print - Home", page_icon="")

    with st.sidebar:
        st.write("Love")
        AgGrid(
            pd.DataFrame({"Recommended Albums": [1, 2, 3, 4, 5, 6, 7 ,8]}),
            fit_columns_on_grid_load=True,
            theme="streamlit",
        )


if __name__ == "__main__":
    main()
