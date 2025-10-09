# 💧 MECHA Streamlit App
A containerized web application for running MECHA hydraulic simulations and visualizing root cross-section anatomy.
Built with Streamlit, GeoPandas, and Shapely, this app lets you interactively upload or select geometries, adjust hydraulic parameters, and run simulations.

---

## Features:

- Upload or use pre-loaded XML geometries (cellsetdata.xml, geometry.xml)
- Visualize root cross-section anatomy (parsed directly from XML)
- Modify hydraulic parameters interactively:
  - Cell wall thickness
  - Membrane permeability (km)
  - Aquaporin contribution (kAQP)
  - Cell wall conductance (kw)
  - Plasmodesmata conductance (Kpl)
- Choose and run predefined hydraulic scenarios (0, 1, 3, 4)
- Compare simulated hydraulic conductivities across parameter ranges

## Prerequisites

You only need *Docker* installed on your machine.
No Python, Streamlit, or MECHA dependencies need to be set up manually.

```{bash}
docker push heymansadrien/mecha-streamlit:0.1.0
docker run -p 8501:8501 heymansadrien/mecha-streamlit:0.1.0
```

Then open your browser at 👉 [http://localhost:8501](http://localhost:8501)

### Build from source (optional)

If you prefer to build the image yourself:

```{bash}
git clone https://github.com/MECHARoot/MECHAStreamlit.git
cd MECHAStreamlit
docker build -t mecha-streamlit .
docker run -p 8501:8501 mecha-streamlit
```

## Citation

Please cite the GRANAR and MECHA tools if you use this workflow in your research:

> Heymans A., Couvreur V., LaRue T., Paez-Garcia A., Lobet G. (2020). **GRANAR, a computational tool to better understand the functional importance of monocotyledon root anatomy**. *Plant Physiology*, 182(2), 707-720. doi: [10.1104/pp.19.00617](https://doi.org/10.1104/pp.19.00617)

> Couvreur V., Faget M., Lobet G., Javaux M., Chaumont F., Draye X. (2018). **Going with the Flow: Multiscale Insights into the Composite Nature of Water Transport in Roots**. *Plant Physiology*, 178(4), 1689–1703. doi: [10.1104/pp.18.01006](https://doi.org/10.1104/pp.18.01006)

## Acknowledgements

Developed in UClouvain at the Eath and Life Institute for the study of plant hydraulic anatomy using GRANAR and MECHA.
Contributions and feedback are welcome.
