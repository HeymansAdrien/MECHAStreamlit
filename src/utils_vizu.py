

import xml.etree.ElementTree as ET
import geopandas as gpd
from shapely.ops import polygonize
import matplotlib.pyplot as plt
import streamlit as st
import numpy as np
from shapely.geometry import LineString, Polygon
from typing import Tuple, Dict, List


def get_root_section(xml_file_path: str) -> gpd.GeoDataFrame:
    """
    Parses a MECHA root section XML file and constructs cell polygons.

    If polygonization fails for a cell (open or disjoint boundary),
    a fallback method orders all cell wall points around their centroid
    and creates a Polygon manually.

    Args
    ----
    xml_file_path : str
        Path to the MECHA XML file.

    Returns
    -------
    gpd.GeoDataFrame
        Columns: id_cell, type, geometry (Polygon).
    """
    # --- Parse XML safely ---
    try:
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
    except Exception as e:
        return gpd.GeoDataFrame(columns=["id_cell", "type", "geometry"])

    # --- Parse groups (cell types) ---
    group_map = {}
    cellgroups_elem = root.find("groups/cellgroups")
    if cellgroups_elem is not None:
        for group_elem in cellgroups_elem.findall("group"):
            group_id = int(group_elem.get("id"))
            if group_id == 4:
                group_name = "cortex"
            elif group_id == 3:
                group_name = "endodermis"
            else:
                group_name = group_elem.get("name")
            group_map[group_id] = group_name

    # --- Parse walls into shapely LineStrings ---
    wall_linestrings: Dict[str, LineString] = {}
    walls_elem = root.find("walls")
    if walls_elem is not None:
        for wall_elem in walls_elem.findall("wall"):
            wall_id = int(wall_elem.get("id"))
            points_elem = wall_elem.find("points")
            if points_elem is None:
                continue

            points = [
                (float(p.get("x")), float(p.get("y")))
                for p in points_elem.findall("point")
                if p.get("x") and p.get("y")
            ]

            if len(points) >= 2:
                wall_linestrings[wall_id] = LineString(points)

    # --- Helper: order points around centroid (fallback) ---
    def order_polygon(points: List[Tuple[float, float]]) -> Polygon:
        """
        Given a list of (x, y) coordinates, order them around the centroid.
        """
        arr = np.array(points)
        cx, cy = arr[:, 0].mean(), arr[:, 1].mean()
        angles = np.arctan2(arr[:, 1] - cy, arr[:, 0] - cx)
        ordered = arr[np.argsort(angles)]
        return Polygon(ordered)

    # --- Parse cells and reconstruct polygons ---
    records = []
    cells_elem = root.find("cells")
    if cells_elem is not None:
        for cell_elem in cells_elem.findall("cell"):
            cell_id = int(cell_elem.get("id"))
            group_id = int(cell_elem.get("group"))
            cell_type = group_map.get(group_id, f"unknown_group_{group_id}")

            # Gather walls forming the cell boundary
            cell_lines: List[LineString] = []
            cell_points: List[Tuple[float, float]] = []

            walls_ref_elem = cell_elem.find("walls")
            if walls_ref_elem is not None:
                for wall_ref in walls_ref_elem.findall("wall"):
                    wall_id = int(wall_ref.get("id"))
                    wall = wall_linestrings.get(wall_id)
                    if wall is not None:
                        cell_lines.append(wall)
                        cell_points.extend(list(wall.coords))

            # Try polygonize first
            cell_polygon = None
            if cell_lines:
                polygons = list(polygonize(cell_lines))
                if polygons:
                    cell_polygon = polygons[0]
                else:
                    print(f"Cell {cell_id} could not form a valid polygon. Fallback: use ordered centroid method")
                    cell_polygon = order_polygon(cell_points)
                    cell_type = "fallback"

            if cell_polygon is not None and not cell_polygon.is_empty:
                records.append({
                    "id_cell": int(cell_id),
                    "type": cell_type,
                    "geometry": cell_polygon
                })
            else:
                print(cell_points)

    # --- Create GeoDataFrame ---
    gdf = gpd.GeoDataFrame(records, crs="EPSG:4326")
    return gdf


def plot_root_section(root_gdf: gpd.GeoDataFrame):
    """Display the root section as polygons using GeoPandas and Matplotlib."""
    if root_gdf.empty:
        print("GeoDataFrame is empty, cannot plot.")
        return

    # GeoPandas handles the figure creation and geometry plotting
    # It automatically groups and colors by the column specified in 'column'
    fig, ax = plt.subplots(figsize=(8, 8))
    
    root_gdf.plot(
        ax=ax, 
        column='type',           # Color polygons by the 'type' column
        cmap='viridis',          # Use a nice color map
        edgecolor='black',       # Outline the cells
        linewidth=0.5,           # Line width for the outline
        alpha=0.5,               # Transparency
        legend=True,             # Display the legend
        legend_kwds={'title': 'Cell Type', 'loc': 'best'}
    )

    ax.set_aspect("equal", "box")
    ax.set_xlabel("x (mm)")
    ax.set_ylabel("y (mm)")
    ax.set_title("Root Cross Section Preview (GeoPandas Polygons)")
    plt.tight_layout()
    st.pyplot(fig) # Use this in your Streamlit app
    # plt.show() # Use this for local testing