"""
Author: Peter Akioyamen
Github: @peter-ai

A web application which uses audio feature data from the Free Music Archive (FMA; 2018)
to create visual acoustic fingerprints of songs and compare audio characteristics across the
music catalogue. The app uses a MySQL backend and is built on Streamlit.

Songs Page of the Acoustic Print web app
"""
# import external dependencies
import numpy as np
import pandas as pd
import streamlit as st

# import user defined package
from acoustic_helpers import (
    generate_fingerprint,
    get_sql_connect_str,
    plot_acoustic_print,
)


def main():
    # define local page config
    st.set_page_config(layout="wide", page_title="Acoustic Print - Home", page_icon="🎵")

    st.write("Hello world")

    # TODO
    # 2-3 columns - acoustic print, spider chart (song vs. genre vs. current selection), and bars (song vs. genre vs. current_)
    # progress bar
    # filterable
    # table with all tracks
    # 


# main program
if __name__ == "__main__":
    main()
