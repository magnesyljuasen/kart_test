import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster, Draw
from streamlit_folium import st_folium
import geopandas as gpd
from shapely.geometry import Point
import pyproj
import numpy as np
import os
from functools import reduce
import plotly.express as px
import plotly.graph_objects as go

def set_streamlit_settings():
    st.set_page_config(
    page_title="Østmarka",
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

def read_csv(folder_path = "output"):
    csv_file_list = []
    scenario_name_list = []
    filename_list = []
    for filename in os.listdir(folder_path):
        if filename.endswith("unfiltered.csv"):
            filename_list.append(filename)
            scenario_name_list.append(filename.split(sep = "_")[0])
            csv_file_list.append(filename)
    return csv_file_list, scenario_name_list

@st.cache_data
def import_df(filename):
    df = pd.read_csv(filename, low_memory=False).head(5000)
    return df

def df_to_gdf(df, selected):
    df['lat'] = df['SHAPE'].apply(return_lat)
    df['lng'] = df['SHAPE'].apply(return_lng)
    geometry = [Point(lon, lat) for lon, lat in zip(df['lng'], df['lat'])]
    gdf = gpd.GeoDataFrame(df, geometry=geometry, crs = "25832")
    gdf = gdf.loc[gdf['Byggutvalgsident'] == selected]
    return gdf

#'_nettutveksling_vintereffekt'
#'_nettutveksling_energi'
def plot_bar_chart(df, y_max, yaxis_title, y_field, chart_title, scaling_value, percentage_mode = False, fixed_mode = True):
    def reorder_dataframe(df):
        reference_row = df[df['scenario_navn'] == 'Referansesituasjon']
        other_rows = df[df['scenario_navn'] != 'Referansesituasjon']
        reordered_df = pd.concat([reference_row, other_rows])
        reordered_df.reset_index(drop=True, inplace=True)
        return reordered_df
    df[y_field] = df[y_field] * scaling_value
    df = df.groupby('scenario_navn')[y_field].sum().reset_index()
    df = reorder_dataframe(df)
    df["prosent"] = (df[y_field] / df.iloc[0][y_field]) * 100
    df["prosent"] = df["prosent"].round(0)
    if fixed_mode == True:
        y_max = None
    if percentage_mode == True:
        y_field = "prosent"
        y_max = 100
        yaxis_title = "Prosentandel (%)"
    colors = ["#1d3c34", '#48a23f', '#4a625c', '#341d3c', '#778a85', '#8e9d99', '#a4b1ad', '#bbc4c2', '#b7dc8f', '#FFC358']

    fig = px.bar(df, x='scenario_navn', y=df[y_field], title = f"{chart_title}", color = 'scenario_navn', color_discrete_sequence = colors)
    fig.update_layout(
        showlegend = False,
        margin=dict(l=0,r=0,b=0,t=50,pad=0),
        height=600,
        yaxis_title=yaxis_title,
        xaxis_title="",
        #plot_bgcolor="white",
        legend=dict(yanchor="top", y=0.98, xanchor="left", x=0.01, bgcolor="rgba(0,0,0,0)"),
        barmode="stack")

    fig.update_xaxes(
            ticks="outside",
            linecolor="black",
            gridcolor="lightgrey",
            tickangle=90
        )
    fig.update_yaxes(
        range=[0, y_max],
        tickformat=",",
        ticks="outside",
        linecolor="black",
        gridcolor="lightgrey",
    )
    if percentage_mode == True:
        fig.update_layout(separators="* .*")
        fig.update_traces(
        hovertemplate='%{y:.0f}%',  # Display percentage values with two decimal places in the tooltip
        )
    else:
        fig.update_layout(separators="* .*")
    
    st.plotly_chart(figure_or_data= fig, use_container_width=True, config = {
        'displayModeBar': False, 
        #'staticPlot': True
        })

def show_all():
    
    c1, c2 = st.columns([1, 1])
    
    with c1:
        selected = st.radio("Velg bygningsmasse", options = ["Eksisterende", "Alternativ 1", "Alternativ 2", "Alternativ 3"], horizontal = True)
        if selected == "Alternativ 3":
            selected = "P3"
        elif selected == "Alternativ 2":
            selected = "P2"
        elif selected == "Alternativ 1":
            selected = "P1"
        elif selected == "Eksisterende":
            selected = "E"
        #--
        csv_list, scenario_name_list = read_csv(folder_path = "output")
        df_list = []
        for i in range(0, len(csv_list)):
            filename = str(csv_list[i])
            df = import_df(filename = rf"output/{filename}")
            df['scenario_navn'] = f'{scenario_name_list[i]}'
            #columns_to_exclude = ['SHAPE', 'Byggutvalgsident']
            #df.columns = [str(col) + f'_{filename.split("_")[0]}' if col not in columns_to_exclude else col for col in df.columns]
            df_list.append(df)
        df = pd.concat(df_list, ignore_index=True)
        #--
        gdf = df_to_gdf(df, selected)
        map = folium.Map(location=[63.4525759196283, 10.447553721163194], zoom_start=13, scrollWheelZoom=True, tiles='CartoDB positron', max_zoom = 22)
    
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
        
        icon_create_function = """
        function (cluster) {
            var childCount = cluster.getChildCount();
            var c = ' marker-cluster-';
            c += 'medium';

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
                'disableClusteringAtZoom': 20  # Disable clustering at this zoom level and lower
            }).add_to(map)

        def style_function(feature):
            value = feature['properties']['_nettutveksling_vintereffekt']  # Assuming the column name is 'value'
            try:
                value = value * 1000
            except Exception:
                value = 0
            if (value) < 10 :
                return {'color': 'green'}
            elif (value) < 100:
                return {'color': 'orange'}
            else:
                return {'color': 'red'}
            
        def style_function(feature):
            value = feature['properties']['_nettutveksling_energi']  # Assuming the column name is 'value'
            try:
                value = value * 1000
            except Exception:
                value = 0
#            if (value) < 10 :
#                return {'color': 'green'}
#            elif (value) < 100:
#                return {'color': 'orange'}
#            else:
#                return {'color': 'red'}
            return {'color' : 'black'}

        gdf1 = gdf.loc[gdf['scenario_navn'] == "Referansesituasjon"]
        # Add GeoJSON layer to the map and apply the style function
        folium.GeoJson(gdf1, name='geojson', marker=folium.CircleMarker(radius = 5), style_function=style_function).add_to(marker_cluster)



        #folium.GeoJson(gdf, name='geojson', marker=folium.CircleMarker(color = "red")).add_to(marker_cluster)

    #    if st.checkbox("Tegne?"):
    #        draw = Draw()
    #        draw.add_to(map)

        st_map = st_folium(
            map,
            use_container_width=True,
            height=600,
            )
        st.info("Zoom inn og ut på kartet med scrollehjulet. Søylediagrammene på høyre side følger kartutsnittet.", icon = "ℹ️")
    with c2:
#        with st.expander("Returnert"):
#            st.write(st_map)
        if st_map["zoom"] > 24:
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
            #
           
            percentage_mode = st.toggle("Prosent", help = "Viser prosentvis reduksjon fra referansesituasjonen.")
            #fixed_mode = st.toggle("Fast y-akse", value = True)
            tab1, tab2, tab3, tab4, tab5 = st.tabs(["Effekt", "Energi", "Timedata", "Varighetskurve", "Overordnet"])
            with tab1:
                plot_bar_chart(df = filtered_gdf, y_max = 4500, yaxis_title = "Effekt [kW]", y_field = '_nettutveksling_vintereffekt', chart_title = "Maksimalt behov for tilført el-effekt fra el-nettet", scaling_value = 1000, percentage_mode = percentage_mode)
            with tab2:
                plot_bar_chart(df = filtered_gdf, y_max = 16000000, yaxis_title = "Energi [kWh]", y_field = '_nettutveksling_energi', chart_title = "Behov for tilført el-energi fra el-nettet", scaling_value = 1000 * 1000, percentage_mode = percentage_mode)
            with tab3:
                effekt = (round(int(np.sum(filtered_gdf["_nettutveksling_vintereffekt"])), 1))
                areal = round(int(np.sum(filtered_gdf['BRUKSAREAL_TOTALT'])), 1)
                energi = round(int(np.sum(filtered_gdf['_nettutveksling_energi'])), 1)
                st.metric(label = "Areal", value = f"{areal:,} m2".replace(",", " "))
                st.metric(label = "Effekt", value = f"{effekt:,} kW".replace(",", " "))
                st.metric(label = "Energi", value = f"{energi:,} kWh".replace(",", " "))
            with tab4:
                pass
            with tab5:
                st.write("Kostnader")
                st.write("Miljø") 
            # Print the filtered GeoDataFrame
            
    #st.write(filtered_gdf)

def merge_dataframes(left, right):
    return pd.merge(left, right, on='SHAPE', how='inner')  # Replace 'common_column' with your actual common column name

def main():
    set_streamlit_settings()
    st.title("Østmarka")
    #st.write(merged_df)
    show_all()

    st.info("Sjekk om det er lagt inn noen regler på de store byggene")
main()

    
