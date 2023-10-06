"""
Author: Peter Akioyamen
Github: @peter-ai

A web application which uses audio feature data from the Free Music Archive (FMA; 2018)
to create visual acoustic fingerprints of songs and compare audio characteristics across the
music catalogue. The app uses a MySQL backend and is built on Streamlit.

Songs Page of the Acoustic Print web app
"""
# import packages from standard libraries
import os

# import external dependencies
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv
from plotly.subplots import make_subplots


def main():
    # define local page config
    st.set_page_config(layout="wide", page_title="Acoustic Print - Home", page_icon="🎵")

    st.write("Hello world")


# main program
if __name__ == "__main__":
    main()
