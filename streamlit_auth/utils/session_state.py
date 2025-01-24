import streamlit as st


def init_session_state(**kwargs):
    for key, value in kwargs.items():
        if not key in st.session_state.keys():
            st.session_state[key] = value
