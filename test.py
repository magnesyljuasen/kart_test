import folium
import geopandas as gpd

# Sample GeoDataFrame (replace this with your actual GeoDataFrame)
gdf = gpd.read_file("path/to/your/geojson/file.geojson")

# Create a map
m = folium.Map(location=[gdf.geometry.centroid.y.mean(), gdf.geometry.centroid.x.mean()], zoom_start=12)

# Define a style function to set marker color based on the 'value' column in the GeoDataFrame
def style_function(feature):
    value = feature['properties']['value']  # Assuming the column name is 'value'
    if value < 10:
        return {'fillColor': 'green', 'color': 'green'}
    elif value < 20:
        return {'fillColor': 'orange', 'color': 'orange'}
    else:
        return {'fillColor': 'red', 'color': 'red'}

# Add GeoJSON layer to the map and apply the style function
folium.GeoJson(gdf, name='geojson', style_function=style_function, tooltip=folium.GeoJsonTooltip(fields=['value'])).add_to(m)

# Add the map to the MarkerCluster
marker_cluster = folium.MarkerCluster().add_to(m)

# Add individual markers to the MarkerCluster
for idx, row in gdf.iterrows():
    folium.Marker(location=[row.geometry.centroid.y, row.geometry.centroid.x],
                  popup=f"Value: {row['value']}").add_to(marker_cluster)

# Save the map to an HTML file
m.save('map.html')