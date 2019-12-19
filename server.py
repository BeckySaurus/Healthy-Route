from flask import Flask, escape, request, Response
import psycopg2
import os
import json
import requests
import shapely
import folium
from openrouteservice import client
from shapely.geometry import LineString, Polygon, mapping, shape
from shapely.ops import cascaded_union
import geopandas as gpd
from geojson import Point, Feature, FeatureCollection, dump
import numpy as np

app = Flask(__name__)

URL = "https://traffic.cit.api.here.com/traffic/6.2/flow.json?app_id=67Jad2HjPh8wXb3Eau3A&app_code=3hlMkBLEzMRbJp-Aondktw&bbox=55.824430445857764,12.119293212890625;55.552718667216595,12.712554931640625&responseattributes=sh"
r = requests.get(url = URL) 
data = r.json() 

dta = data['RWS']
#print(data)
@app.route('/')
def index():

    URL = "https://traffic.cit.api.here.com/traffic/6.2/flow.json?app_id=67Jad2HjPh8wXb3Eau3A&app_code=3hlMkBLEzMRbJp-Aondktw&bbox=55.824430445857764,12.119293212890625;55.552718667216595,12.712554931640625&responseattributes=sh"
    r = requests.get(url = URL) 
    data = r.json() 
    dta = data['RWS']
    #print(data)
    map = folium.Map([55.71459, 12.577], zoom_start=5, tiles='cartodbpositron')
    jam = []
    lat_point = []
    lon_point = []
    features = []
    for rws in data['RWS']:
        #print(rws)
        
        for rw in rws['RW']:
            #print(rw)
            
            for fis in rw['FIS']:
                #print(fis)
                
                for fi in fis['FI']:
                    #print(fi)
                    #########################   
                    #Getting the coordonates#
                    #########################
                    #for shp in fi['SHP']:
                        #print(shp)
                        #for key, value in shp.items():
                            #print(value)
                            
                    ##########################    
                    #Getting the current flow#
                    ##########################
                    for cf in fi['CF']:
                        #print(cf)
                        
                        for key, value in cf.items():
                            #print(key)
                            #print(value)
                            ####################################################################    
                            #Getting the JamFactor, SpeedUncut and FreeFlow in the current flow#
                            ####################################################################
                            if key=='SU':
                                speedUncut = value
                                #print("Speed Uncut: "+str(speedUncut))
                            if key=='JF':
                                jamFactor = value
                                #print("Jam Factor: "+str(jamFactor))
                                if jamFactor > 7.9:
                                    for shp in fi['SHP']:
                                        #print(jamFactor)
                                        
                                        for key, value in shp.items():
                                            #Fixing the parsing
                                            if key == 'value':
                                                #print(key)
                                                coordset = value
                                                #print (coordset)
                                                for line in coordset:
                                                    #print(line)
                                                    fields=line[0:-1].replace(' ', '],[').replace(',',', ')

                                                    ccc=('[['+fields+']]')
                                                    #print(ccc)

                                                    lines = LineString(json.loads(ccc))
                                                    #print (lines)

                                                    # add more features...
                                                    # features.append(...)
                                                    features.append(Feature(geometry=lines))
                                                    #Creates a FeatureCollection
                                                    feature_collection = FeatureCollection(features)
                            if key=='FF':
                                freeFlow = value
                                #print("Free Flow: "+str(freeFlow))
                                
                            #Getting SS values
                            if key == 'SSS':
                                #print(value)
                                ssValue = value
                                
                                for key, value in ssValue.items():
                                    #print(key)
                                    #print(value)
                                    ssValueList = value
                                   
                                    for value in ssValueList:
                                        #print(value)
                                        ssValueListDict = value
                                        
                                        #########################################################    
                                        #Getting Jam Factor, Free Flow and Speed Uncut inside SS#
                                        #########################################################
                                        for key, value in ssValueListDict.items():
                                            #print(key)
                                            #print(value)
                                            ssFinalValues = value
                                            if key == 'SU':                          
                                                ssSpeedUncut = ssFinalValues
                                                #print("SS Speed Uncut: "+str(ssSpeedUncut))
                                            if key == 'JF':
                                                
                                                ssJamFactor = ssFinalValues
                                                #print(ssJamFactor)
                                                #If the Jam Factor == 10 give me the coordonates
                                                if ssJamFactor > 8:
                                                    jammm = ssJamFactor
                                                    #print (jammm)
                                                    #print("SS Jam Factor: "+str(ssJamFactor))
                                                    for shp in fi['SHP']:
                                                        #print(shp)
                                                    
                                                        for key, value in shp.items():
                                                            #Fixing the parsing
                                                            if key == 'value':
                                                                #print(key)
                                                                coordset = value
                                                                #print (coordset)
                                                                for line in coordset:
                                                                    #print(line)
                                                                    fields=line[0:-1].replace(' ', '],[').replace(',',', ')

                                                                    ccc=('[['+fields+']]')
                                                                    #print(ccc)

                                                                    lines = LineString(json.loads(ccc))
                                                                    #print (lines)
                                                                    
                                                                    # add more features...
                                                                    # features.append(...)
                                                                    features.append(Feature(geometry=lines))
                                                                    #Creates a FeatureCollection
                                                                    feature_collection = FeatureCollection(features)
                                                                   

                                                       
                                                                    

                                                if key == 'FF':
                                                    ssFreeFlow = ssFinalValues
                                                    #print("SS Free Flow: "+str(ssFreeFlow))
    #with open('sss.geojson', 'w') as f:
        #dump(feature_collection, f)


    #Flipping the coordinates in the GeoJson Featured Collection
    def flip_geojson_coordinates(geo):
        if isinstance(geo, dict):
            for k, v in geo.items():
                if k == "coordinates":
                    z = np.asarray(geo[k])
                    f = z.flatten()
                    geo[k] = np.dstack((f[1::2], f[::2])).reshape(z.shape).tolist()
                else:
                    flip_geojson_coordinates(v)
        elif isinstance(geo, list):
            for k in geo:
                flip_geojson_coordinates(k)

    flip_coordinates = feature_collection

    #Stile the LineStrings
    flip_geojson_coordinates(flip_coordinates)
    style_function = lambda x: {
        'color' : 'red',
    }


    folium.GeoJson(feature_collection,style_function=style_function).add_to(map)

    #folium.PolyLine(jam, color="red", weight=2.5, opacity=1).add_to(map)

    map 


    # In[4]:


    URL = "https://traffic.cit.api.here.com/traffic/6.2/flow.json?app_id=67Jad2HjPh8wXb3Eau3A&app_code=3hlMkBLEzMRbJp-Aondktw&bbox=55.824430445857764,12.119293212890625;55.552718667216595,12.712554931640625&responseattributes=sh"
    r = requests.get(url = URL) 
    data = r.json() 
    dta = data['RWS']
    #print(data)

    api_key = '5b3ce3597851110001cf62480bce1c9f6f5041d0ae79d1a8847f8b98' #https://openrouteservice.org/sign-up
    clnt = client.Client(key=api_key)

    map = folium.Map(tiles='https://maps.heigit.org/openmapsurfer/tiles/roads/webmercator/{z}/{x}/{y}.png', 
                            attr='Map data (c) OpenStreetMap, Tiles (c) <a href="https://heigit.org">GIScience Heidelberg</a>', 
                            location=([55.71459, 12.577]), 
                            zoom_start=7) # Create map

    popup_route = "<h4>{0} route</h4><hr>"              "<strong>Duration: </strong>{1:.1f} mins<br>"              "<strong>Distance: </strong>{2:.3f} km" 

    # Request route
    coordinates = [[12.597, 55.71499], [12.507, 55.71409]]
    direction_params = {'coordinates': coordinates,
                        'profile': 'driving-car', 
                        'format_out': 'geojson',
                        'preference': 'shortest',
                        'geometry': 'true'}

    regular_route = clnt.directions(**direction_params) # Direction request

    # Build popup
    duration, distance = regular_route['features'][0]['properties']['summary'].values()
    popup = folium.map.Popup(popup_route.format('Regular', 
                                                     duration/60, 
                                                     distance/1000))

    gj= folium.GeoJson(regular_route,
                       name='Regular Route',
                      ) \
              .add_child(popup)\
              .add_to(map)
    folium.Marker(list(reversed(coordinates[0])), popup='Bundeskanzleramt').add_to(map)
    folium.Marker(list(reversed(coordinates[1])), popup='Deutsches Currywurst Museum').add_to(map)

    jam = []
    lat_point = []
    lon_point = []
    features = []
    for rws in data['RWS']:
        #print(rws)
        
        for rw in rws['RW']:
            #print(rw)
            
            for fis in rw['FIS']:
                #print(fis)
                
                for fi in fis['FI']:
                    #print(fi)
                    #########################   
                    #Getting the coordonates#
                    #########################
                    #for shp in fi['SHP']:
                        #print(shp)
                        #for key, value in shp.items():
                            #print(value)
                            
                    ##########################    
                    #Getting the current flow#
                    ##########################
                    for cf in fi['CF']:
                        #print(cf)
                        
                        for key, value in cf.items():
                            #print(key)
                            #print(value)
                            ####################################################################    
                            #Getting the JamFactor, SpeedUncut and FreeFlow in the current flow#
                            ####################################################################
                            if key=='SU':
                                speedUncut = value
                                #print("Speed Uncut: "+str(speedUncut))
                            if key=='JF':
                                jamFactor = value
                                #print("Jam Factor: "+str(jamFactor))
                                if jamFactor > 4:
                                    for shp in fi['SHP']:
                                        #print(jamFactor)
                                        
                                        for key, value in shp.items():
                                            #Fixing the parsing
                                            if key == 'value':
                                                #print(key)
                                                coordset = value
                                                #print (coordset)
                                                for line in coordset:
                                                    #print(line)
                                                    fields=line[0:-1].replace(' ', '],[').replace(',',', ')

                                                    ccc=('[['+fields+']]')
                                                    #print(ccc)

                                                    lines = LineString(json.loads(ccc))
                                                    #print (lines)

                                                    # add more features...
                                                    # features.append(...)
                                                    features.append(Feature(geometry=lines))
                                                    #Creates a FeatureCollection
                                                    feature_collection = FeatureCollection(features)
                            if key=='FF':
                                freeFlow = value
                                #print("Free Flow: "+str(freeFlow))
                                
                            #Getting SS values
                            if key == 'SSS':
                                #print(value)
                                ssValue = value
                                
                                for key, value in ssValue.items():
                                    #print(key)
                                    #print(value)
                                    ssValueList = value
                                   
                                    for value in ssValueList:
                                        #print(value)
                                        ssValueListDict = value
                                        
                                        #########################################################    
                                        #Getting Jam Factor, Free Flow and Speed Uncut inside SS#
                                        #########################################################
                                        for key, value in ssValueListDict.items():
                                            #print(key)
                                            #print(value)
                                            ssFinalValues = value
                                            if key == 'SU':                          
                                                ssSpeedUncut = ssFinalValues
                                                #print("SS Speed Uncut: "+str(ssSpeedUncut))
                                            if key == 'JF':
                                                
                                                ssJamFactor = ssFinalValues
                                                #print(ssJamFactor)
                                                #If the Jam Factor == 10 give me the coordonates
                                                if ssJamFactor > 4:
                                                    jammm = ssJamFactor
                                                    #print (jammm)
                                                    #print("SS Jam Factor: "+str(ssJamFactor))
                                                    for shp in fi['SHP']:
                                                        #print(shp)
                                                    
                                                        for key, value in shp.items():
                                                            #Fixing the parsing
                                                            if key == 'value':
                                                                #print(key)
                                                                coordset = value
                                                                #print (coordset)
                                                                for line in coordset:
                                                                    #print(line)
                                                                    fields=line[0:-1].replace(' ', '],[').replace(',',', ')

                                                                    ccc=('[['+fields+']]')
                                                                    #print(ccc)

                                                                    lines = LineString(json.loads(ccc))
                                                                    #Buffer around the lines
                                                                    buff = lines.buffer(0.0005)
                                                                    #print (lines)
                                                                    
                                                                    # add more features...
                                                                    # features.append(...)
                                                                    features.append(Feature(geometry=lines))
                                                                    
                                                                    #Creates a FeatureCollection
                                                                    feature_collection = FeatureCollection(features)
                                                                    #print(feature_collection)
                                                                   

                                                       
                                                                    

                                                if key == 'FF':
                                                    ssFreeFlow = ssFinalValues
                                                    #print("SS Free Flow: "+str(ssFreeFlow))
    #with open('sss.geojson', 'w') as f:
        #dump(feature_collection, f)


    #Flipping the coordinates in the GeoJson Featured Collection
    def flip_geojson_coordinates(geo):
        if isinstance(geo, dict):
            for k, v in geo.items():
                if k == "coordinates":
                    z = np.asarray(geo[k])
                    f = z.flatten()
                    geo[k] = np.dstack((f[1::2], f[::2])).reshape(z.shape).tolist()
                else:
                    flip_geojson_coordinates(v)
        elif isinstance(geo, list):
            for k in geo:
                flip_geojson_coordinates(k)

    flip_coordinates = feature_collection
    json_flip_coordinates = flip_coordinates
    
    #Stile the LineStrings
    flip_geojson_coordinates(flip_coordinates)
    style_function = lambda x: {
        'color' : 'blue',
    }
    # # map.on('click', newMarker)
    # # def newMarker(e):
    # #     #new_mark = L.marker().setLatLng(e.latlng).addTo(map);
    # #     #folium.Marker(list(reversed(coordinates[0])), popup='Bundeskanzleramt').add_to(map)
    # #     print(e.latlng)
    folium.GeoJson(feature_collection,style_function=style_function).add_to(map)

    #folium.PolyLine(jam, color="red", weight=2.5, opacity=1).add_to(map)
   

    #folium.TileLayer(tiles='https://tiles.traffic.api.here.com/traffic/6.0/tiles/{z}/{x}/{y}/256/png32?app_id=67Jad2HjPh8wXb3Eau3A&app_code=3hlMkBLEzMRbJp-Aondktw', attr='Here.com').add_to(map)
    #map.add_child(folium.ClickForMarker(popup='Waypoint'))

    # #map




    
    return map._repr_html_()





if __name__ == '__main__':
    app.run(debug=True)




@app.route('/json-example')
def json_data():
    return regular_route