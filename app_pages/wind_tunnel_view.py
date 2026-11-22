"""Wind Tunnel: a live 2D airflow simulation. Change the shape and the angle, watch the air."""
import streamlit as st

from wind_tunnel import tunnel

st.caption("A real fluid simulation running in your browser. Change the shape and the angle and watch the air "
           "turn, separate and form a wake. Forces are relative, not real newtons.")
tunnel(dark=st.session_state.dark)
left, right = st.columns([3, 2], vertical_alignment="center")
left.caption("2D lattice-Boltzmann solver at a low Reynolds number: shows how flow behaves, not real F1 figures.")
right.page_link("app_pages/academy_m4.py", label="Learn it: Academy 4.3 Lift, drag and efficiency",
                icon=":material/school:", query_params={"ch": "4.3"})
