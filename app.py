
import streamlit as st
import numpy as np
import os
import matplotlib.pyplot as plt
import pandas as pd
import shutil
from src.mecha_function import update_xml_attributes, mecha, set_hydraulic_scenario
from src.utils_vizu import get_root_section, plot_root_section

# --- Directory setup ---
CELLSET_DIR = "./MECHA/cellsetdata/"
GEOM_PATH_INIT = "./MECHA/Projects/granar/in/Default_Geometry.xml"
HYDRAULICS_PATH_INIT = "./MECHA/Projects/granar/in/Default_Maize_Hydraulics.xml"
GEOM_PATH = "./MECHA/Projects/granar/in/Geometry.xml"
HYDRAULICS_PATH = "./MECHA/Projects/granar/in/Hydraulics.xml"
PARAM_DIR = "./MECHA/Projects/granar/in/"
GEOM_PATH_PRE = "./MECHA/Projects/granar/in/Preloaded_Geometry.xml"

# --- Parameter metadata ---
PARAM_INFO = {
    "cell wall thickness": {
        "default": 1.5,
        "conversion": 1,
        "unit": "µm",
        "desc": "Typical primary cell wall thickness in maize roots ranges from 0.2–2 µm; affects radial water resistance mainly through apoplastic pathway."
    },
    "membrane permeability": {
        "default": 3.0,
        "conversion": 1e-5,
        "unit": "cm·d⁻¹·hPa⁻¹",
        "desc": "Average plasma membrane permeability from the biphospholipid layer."
    },
    "AQP contribution to cell membrane permeability": {
        "default": 4.3,
        "conversion": 1e-4,
        "unit": "cm·d⁻¹·hPa⁻¹",
        "desc": "Aquaporin contribution to total cell membrane permeability"
    },
    "cell wall conductance": {
        "default": 2.4,
        "conversion": 1e-4,
        "unit": "cm²·s⁻¹·hPa⁻¹",
        "desc": "Conductance of water through apoplastic space; low and dominated by porosity of the wall matrix; typical values in 10⁻⁴–10⁻⁵ range."
    },
    "plasmodesmata conductance": {
        "default": 5.3,
        "conversion": 1e-12,
        "unit": "cm³·d⁻¹·hPa⁻¹plasmodesmata⁻¹",
        "desc": "Effective conductance for symplastic flow between cells via plasmodesmata; literature suggests 10⁻¹²–10⁻¹³ cm³·s⁻¹·MPa⁻¹ per PD connection."
    }
}

# ------- Utils ------------------

def safe_copy(src, dst):
    """Copy file only if src and dst are different."""
    if os.path.abspath(src) == os.path.abspath(dst):
        print(f"Skipping copy: {src} and {dst} are the same file")
        return
    shutil.copy(src, dst)

# ----------------------------------------------------------
# Streamlit UI
# ----------------------------------------------------------

st.set_page_config(page_title="MECHA Streamlit App", layout="centered")
st.title("💧 MECHA parameter exploration")

st.write("Upload MECHA input files and explore how anatomical or hydraulic parameters affect simulated conductivity.")

preloaded = os.listdir(CELLSET_DIR)
use_preloaded = st.checkbox("Use a pre-loaded root geometry", value=True)

if use_preloaded and preloaded:
    chosen = st.selectbox("Select existing cellsetdata", preloaded)
    cellset_path = os.path.join(CELLSET_DIR, chosen)
    # Construct corresponding geometry path
    geom_path = os.path.join(PARAM_DIR, f"Geometry_{os.path.splitext(chosen)[0]}.xml")
    st.info(f"Using pre-loaded file: {chosen}")
    if os.path.splitext(chosen)[0] == "current_root":
        safe_copy(os.path.join("./MECHA/", "current_root.xml"), os.path.join(CELLSET_DIR, "current_root.xml"))
    else:
        safe_copy(cellset_path, os.path.join(CELLSET_DIR, "current_root.xml"))
        
    safe_copy(geom_path, os.path.join(PARAM_DIR, "Preloaded_Geometry.xml"))
    

else:
    st.write("Upload a new pair of files:")
    cellset_file = st.file_uploader("cellsetdata.xml", type=["xml"])
    geometry_file = st.file_uploader("geometry.xml", type=["xml"])

    if cellset_file and geometry_file:
        # save to target locations
        cellset_path = os.path.join(CELLSET_DIR, "current_root.xml")
        with open(cellset_path, "wb") as f:
            f.write(cellset_file.read())    
        with open(GEOM_PATH, "wb") as f:
            f.write(geometry_file.read())   
        st.success("✅ Uploaded and saved")
    else:
        st.stop()

# --- If we have a geometry, parse and show it ---
if os.path.exists(os.path.join(CELLSET_DIR, "current_root.xml")):
    try:
        root_section = pd.DataFrame()
        root_section = get_root_section(os.path.join(CELLSET_DIR, "current_root.xml"))
        with st.expander("Root cross-section preview", expanded=False):
            plot_root_section(root_section)
    except Exception as e:
        st.error(f"Could not parse geometry: {e}")

# --- Parameter selection ---
st.subheader("Parameter selection")
param = st.selectbox("Choose parameter to vary:", list(PARAM_INFO.keys()))

col1, col2 = st.columns([2, 3])

with col1:
    default_val = PARAM_INFO[param]["default"]
    unit = PARAM_INFO[param]["unit"]
    conv = PARAM_INFO[param]["conversion"]

    st.write(f"**Default value:** {default_val:g} {unit}")
    mode = st.radio("Mode", ["Single value", "Range (0.1× to 10× default)"], horizontal=True)

    if mode == "Single value":
        value = st.number_input(
            f"Enter {param} value ({conv} {unit})",
            value=float(default_val),
            step=0.1
        )
        values = [value*conv]

    else:
        # Define allowed limits
        min_limit = default_val / 10
        max_limit = default_val * 10

        st.write(f"Allowed range: {min_limit:g} x {conv} → {max_limit:g} x {conv} {unit}")

        # Let user pick min and max within those limits
        selected_min, selected_max = st.slider(
            f"Select {param} range ({unit})",
            min_value=float(min_limit),
            max_value=float(max_limit),
            value=(float(min_limit), float(max_limit))
        )

        # Generate 10 evenly spaced values between chosen bounds
        values = np.linspace(selected_min*conv, selected_max*conv, 10)

        st.write(f"Running 10 steps from {selected_min:g} to {selected_max:g} {conv} {unit} ")

with col2:
    st.markdown(f"**Description:** {PARAM_INFO[param]['desc']}")

scenarios = st.multiselect("Select hydraulic scenarios", [0, 1, 3, 4], default=[1])

# --- Run button ---
if st.button("Run MECHA simulation"):

    # Clean start
    if use_preloaded:
        safe_copy(GEOM_PATH_PRE, GEOM_PATH)
    else:
        safe_copy(GEOM_PATH_INIT, GEOM_PATH)
    safe_copy(HYDRAULICS_PATH_INIT, HYDRAULICS_PATH)

    set_hydraulic_scenario(GEOM_PATH, scenarios)
    st.success(f"Hydraulic scenario(s) {scenarios} activated.")

    results = []
    progress = st.progress(0)
    for i, v in enumerate(values):
        progress.progress((i + 1) / len(values))
        if param == "cell wall thickness":
            update_xml_attributes(GEOM_PATH, "thickness", "thickness", {"value": f"{v:.3f}"})
        elif param == "membrane permeability":
            update_xml_attributes(HYDRAULICS_PATH, "km", "km", {"value": f"{v:.6f}"})
        elif param == "AQP contribution to cell membrane permeability":
            update_xml_attributes(HYDRAULICS_PATH, "kAQPrange", "kAQP", {"value": f"{v:.6f}"})
        elif param == "cell wall conductance":
            update_xml_attributes(HYDRAULICS_PATH, "kwrange", "kw", {"value": f"{v:.6f}"})
        elif param == "plasmodesmata conductance":
            update_xml_attributes(HYDRAULICS_PATH, "Kplrange", "Kpl", {"value": f"{v:.3e}"})
        
        # Run MECHA
        kr = mecha()
        for i_sc, n_sc in enumerate(scenarios):
            results.append({"parameter_value": v, "kr": kr[i_sc], "hydraulic_scenario": n_sc})


    # --- Display results ---
    df = pd.DataFrame(results)
    st.success("✅ Simulation complete")

    # Plot grouped by scenario
    fig, ax = plt.subplots(figsize=(7,5))
    for n_sc in sorted(df["hydraulic_scenario"].unique()):
        subset = df[df["hydraulic_scenario"] == n_sc]
        ax.plot(subset["parameter_value"], subset["kr"], 'o-', alpha=0.3, label=f"Hydraulic Scenario {n_sc}")

    ax.set_xlabel(param)
    ax.set_ylabel("kr (cm·hPa⁻¹·d⁻¹)")
    ax.set_title(f"MECHA simulation — {param}")
    ax.legend()
    st.pyplot(fig)

    st.download_button(
        "Download CSV",
        data=df.to_csv(index=False),
        file_name=f"mecha_results_{param.replace(' ', '_')}.csv",
        mime="text/csv"
    )
