import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster, Draw
from streamlit_folium import st_folium
import geopandas as gpd
from shapely.geometry import Point
import pyproj
import numpy as np

def set_streamlit_settings():
    st.set_page_config(
    page_title="Test",
    page_icon="♨️",
    layout="centered",
    initial_sidebar_state="expanded")
    
    with open("src/styles/main.css") as f:
        st.markdown("<style>{}</style>".format(f.read()), unsafe_allow_html=True)

    st.markdown(
        """
        <style>
        [data-testid="collapsedControl"] svg {
            height: 3rem;
            width: 3rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

def return_lat(x):
    return float(x.split()[3].replace(",", ""))

def return_lng(x):
    return float(x.split()[1].replace(",", ""))

@st.cache_data
def import_df(filename):
    df = pd.read_csv(filename, low_memory=False).head(5000)
    return df

def main():
    set_streamlit_settings()
    df = import_df(filename = "src\Bergvarme_filtered.csv")
    df2 = import_df(filename = "src\Fjernvarme_filtered.csv")
    df['lat'] = df['SHAPE'].apply(return_lat)
    df['lng'] = df['SHAPE'].apply(return_lng)
    geometry = [Point(lon, lat) for lon, lat in zip(df['lng'], df['lat'])]
    gdf = gpd.GeoDataFrame(df, geometry=geometry, crs = "25832")

    map = folium.Map(location=[59.29028230604963, 11.118593215942385], zoom_start=15, scrollWheelZoom=True, tiles='CartoDB positron')

    def create_cluster_icon(cluster):
        blue_icon = folium.Icon(color='blue', icon='info-sign')
        return blue_icon

    marker_cluster = MarkerCluster(
        name='Cluster',
        control=False,  # Do not add this cluster layer to the layer control
        overlay=True,   # Add this cluster layer to the map
        #icon_create_function=create_cluster_icon,  # Disable the default icon creation function
        options={
            #'maxClusterRadius': 4,  # Maximum radius of the cluster in pixels
            'disableClusteringAtZoom': 17  # Disable clustering at this zoom level and lower
        }).add_to(map)
        
    folium.GeoJson(gdf, name='geojson', marker=folium.CircleMarker()).add_to(marker_cluster)

#    if st.checkbox("Tegne?"):
#        draw = Draw()
#        draw.add_to(map)

    st_map = st_folium(map, 
                    use_container_width=True,
                    height=450,
                    #returned_objects = [returned] 
                    #returned_objects=["last_active_drawing"]
                    #returned_objects=["last_circle_polygon"]
                    )
    with st.expander("Returnert"):
        st.write(st_map)

    if st_map["zoom"] > 18:
        st.warning("Du må zoome lenger ut")
    else:
        original_crs = pyproj.CRS("EPSG:4326")  # WGS84 (latitude and longitude)
        target_crs = pyproj.CRS("EPSG:25832")

        bounding_box = st_map["bounds"]

        transformer = pyproj.Transformer.from_crs(original_crs, target_crs, always_xy=True)
        min_lon, min_lat = transformer.transform(bounding_box["_southWest"]["lng"], bounding_box["_southWest"]["lat"])
        max_lon, max_lat = transformer.transform(bounding_box["_northEast"]["lng"], bounding_box["_northEast"]["lat"])

        # Filter GeoDataFrame based on bounding box
        filtered_gdf = gdf.cx[min_lon:max_lon, min_lat:max_lat]


        effekt = (round(int(np.sum(filtered_gdf["_nettutveksling_vintereffekt"]) * 1000), 1))
        
        # Print the filtered GeoDataFrame
        st.metric(label = "Areal", value = f"{round(int(np.sum(filtered_gdf['BRUKSAREAL_TOTALT'])), -3):,} m2".replace(",", " "))
        st.metric(label = "Effekt", value = f"{effekt:,} kW".replace(",", " "))

main()

    
