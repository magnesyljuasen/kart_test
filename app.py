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
    layout="wide",
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
    c1, c2 = st.columns([2, 1])
    with c1:
        df = import_df(filename = "src\Bergvarme_filtered.csv")
        df2 = import_df(filename = "src\Fjernvarme_filtered.csv")
        df['lat'] = df['SHAPE'].apply(return_lat)
        df['lng'] = df['SHAPE'].apply(return_lng)
        geometry = [Point(lon, lat) for lon, lat in zip(df['lng'], df['lat'])]
        gdf = gpd.GeoDataFrame(df, geometry=geometry, crs = "25832")

        map = folium.Map(location=[59.29028230604963, 11.118593215942385], zoom_start=15, scrollWheelZoom=True, tiles='CartoDB positron')
        
        icon_create_function = """
        function (cluster) {
            var childCount = cluster.getChildCount();
            var c = ' marker-cluster-';
            if (childCount < 10) {
                c += 'small';
            } else if (childCount < 100) {
                c += 'medium';
            } else {
                c += 'large';
            }
            return new L.DivIcon({ html: '<div><span>' + childCount + '</span></div>', className: 'marker-cluster' + c, iconSize: new L.Point(40, 40) });
            };
        """

        marker_cluster = MarkerCluster(
            name='Cluster',
            control=False,  # Do not add this cluster layer to the layer control
            overlay=True,   # Add this cluster layer to the map
            icon_create_function=icon_create_function,
            options={
                #'maxClusterRadius': 4,  # Maximum radius of the cluster in pixels
                'disableClusteringAtZoom': 17  # Disable clustering at this zoom level and lower
            }).add_to(map)

        def style_function(feature):
            value = feature['properties']['_nettutveksling_vintereffekt']  # Assuming the column name is 'value'
            if (value * 1000) < 10 :
                return {'color': 'green'}
            elif (value * 1000) < 100:
                return {'color': 'orange'}
            else:
                return {'color': 'red'}

        # Add GeoJSON layer to the map and apply the style function
        folium.GeoJson(gdf, name='geojson', marker=folium.CircleMarker(radius = 5), style_function=style_function).add_to(marker_cluster)


        #folium.GeoJson(gdf, name='geojson', marker=folium.CircleMarker(color = "red")).add_to(marker_cluster)

    #    if st.checkbox("Tegne?"):
    #        draw = Draw()
    #        draw.add_to(map)
        checked = st.checkbox("Vis statistikk")
        if checked:
            returned_objects = None
        else:
            returned_objects = []
        
        st_map = st_folium(
            map,
            returned_objects=returned_objects,
            use_container_width=True,
            height=450,
            )

        
        
    with c2:
        if checked:
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

    
