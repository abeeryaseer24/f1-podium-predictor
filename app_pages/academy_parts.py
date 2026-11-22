"""3D Part Explorer: rotate a Formula 1 car and its systems, explode them and tap any part."""
import streamlit as st

import part_explorer as PX
from academy import academy_css

academy_css()
names = list(PX.ASSEMBLIES)
pick = st.segmented_control("Model", names, default="Whole car", key="px_model") or "Whole car"
st.caption(PX.ASSEMBLIES[pick]["blurb"] + " Drag the Explode slider to take it apart; tap a part to read about it, "
           "then Isolate it to see it alone.")
PX.explorer(pick, dark=st.session_state.dark)
st.caption("Our own simplified models built from basic shapes, not any team's car. Proportions are illustrative.")
