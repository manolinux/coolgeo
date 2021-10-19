from pydantic.errors import DataclassTypeError
import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime,date
import requests
import leafmap.kepler as leafmap
import pandas as pd
import json
import sys
from shapely.geometry import mapping, shape
import requests
from geojson_pydantic import Feature, FeatureCollection
from fastapi.encoders import jsonable_encoder
import tempfile
import geojson
from settings import Settings
from communication import communication


##Session state
def setSessionState(key,value):
        st.session_state[key] = value

##Recreate a text in container
def stContainerText(container,text):
    container.empty()
    with container:
        st.text(text)

##Recreate a text input in container
def stContainerTextInput(container,label,value):
    container.empty()
    with container:
         return st.text_input(label=label,value=value)

#process turnovers into groups by age and male/female
def processTurnovers(tdata,postalCode):
    combinedTurnovers = Settings.COMBINED_GROUPS_DICT
    for index  in tdata.properties:
        age = tdata.properties[index]["p_age"]
        gender = tdata.properties[index]["p_gender"]
        amount = tdata.properties[index]["amount"]
        combinedTurnovers[age+"-"+gender] += amount
    return combinedTurnovers


#get Geometry for postalCode
def getGeometryFromPropertyAndValue(geojson,prop,val):
    fc = geojson
    features = fc['features']
    try:
        for ft in features:
            if ft['properties'][prop] == int(val):
                return ft['geometry']
    #Non exisitng prop
    except Exception as e:
        st.error(str(prop)+str(val))
    return None

#get Geometry centroid
def getGeometryCentroid(geom):
    return shape(geom).centroid

#def changed postal code
def changedPostalCode(args):
    st.write("postal code = " + args)

#Page config wide
st.set_page_config(layout="wide")

#Custom html for keeping some things
#postalCodes in advance
postalCodesData = requests.get('http://localhost:8000/postalCodes/4326').json()
if 'postalCodes' not in st.session_state:
    st.session_state['postalCodes'] = postalCodesData
if 'lon' not in st.session_state:
    st.session_state['lon'] = -3.703889
if 'lat' not in st.session_state:
    st.session_state['lat'] = 40.416667
if 'startDate' not in st.session_state:
    st.session_state['startDate'] = datetime.strptime('2015-01-01','%Y-%M-%d')
if 'endDate' not in st.session_state:
    st.session_state['endDate'] = datetime.strptime('2017-12-31','%Y-%M-%d')
if 'zipcode' not in st.session_state:
    st.session_state['zipcode'] = '28013'
if 'turnovers' not in st.session_state:
    st.session_state['turnovers'] = None
if 'turnoversByAgeAndGener' not in st.session_state:
    st.session_state['turnoversByAgeAndGender'] = None

col1, col2,col3 = st.columns((1,2,1))
with col1:
    sCode = communication()
    with st.form("Form 1"): 
      
        d1 = st.date_input ("Start date" , max_value=datetime.strptime('2017-12-31','%Y-%M-%d'), 
                min_value=datetime.strptime('2015-01-01','%Y-%M-%d'), 
                value=st.session_state["startDate"])
        d2 = st.date_input("End date", min_value=datetime.strptime('2015-01-01','%Y-%M-%d'), 
                max_value=datetime.strptime('2025-12-31','%Y-%M-%d'),
                value=st.session_state["endDate"])
                
        cpContainer = st.empty()
        cp = stContainerTextInput(cpContainer,label="Selected zip code",value=st.session_state["zipcode"])
        b1 = st.form_submit_button("Go!")
        acumHeader = st.subheader('Acummulated')
        periodContainer = st.empty()
        valueContainer = st.empty()
        stContainerText(periodContainer,'Period: N/A')
        stContainerText(valueContainer,'Value: N/A')
    
        if sCode:
            st.session_state["zipcode"] = sCode["value"]
            del cp
            cp = stContainerTextInput(cpContainer,label="Selected zip code",value=st.session_state["zipcode"])

        if d1 or d2:
            stContainerText(periodContainer,'Period: ' + datetime.strftime(d1,'%Y/%m/%d') + " - " + 
                        datetime.strftime(d2,'%Y/%m/%d'))
            stContainerText(valueContainer,'Value: N/A')
            setSessionState("startDate", d1)
            setSessionState("endDate", d2)
        
            
           
        #Button clicked?
        if b1:
            try:
                totalTurnoversUrl = 'http://localhost:8000/totalTurnovers/{0}/{1}/{2}'.format(
                    datetime.strftime(d1,"%Y-%m-%d"),datetime.strftime(d2,"%Y-%m-%d"),cp)
                response = requests.get(totalTurnoversUrl)
                totalTurnovers = json.loads(response.text)
                if response.status_code == 200:
                    stContainerText(valueContainer,'Value: ' + str(totalTurnovers['amount']))
                    st.success("Got total turnovers data!")
                else:
                    stContainerText(valueContainer,'Value: N/A')
                    st.error(response.text) 

            except Exception as e:
                stContainerText(valueContainer,'Value: N/A')
                exc_type, exc_value, exc_traceback = sys.exc_info()
                st.error(exc_value)

with col2:
    #showing the map
    style_1 = {
        "stroke": True,
        "color": "#0000ff",
        "weight": 2,
        "opacity": 1,
        "fill": True,
        "fillColor": "#0000ff",
        "fillOpacity": 0.1,
    }

    hover_style = {"fillOpacity": 0.7}


    style_2 = {
        "stroke": True,
        "color": "#00ff00",
        "weight": 2,
        "opacity": 1,
        "fill": True,
        "fillColor": "#00ff00",
        "fillOpacity": 0.1,
    }
    
    if cp:

        DEFAULT_MAP_SPECS = dict(height=450, width=600) 
        map_specs = DEFAULT_MAP_SPECS

        #We obtain turnovers data for current postalCode
        turnoversUrl = 'http://localhost:8000/turnovers/{0}/{1}/{2}'.format(
            datetime.strftime(st.session_state["startDate"],'%Y-%m-%d'),
            datetime.strftime(st.session_state["endDate"],'%Y-%m-%d'),cp)
            
        turnoversData = requests.get(turnoversUrl).json()
    
        #And obtain geometry from cached geometries
        turnoversGeometry = getGeometryFromPropertyAndValue(postalCodesData,
                            "code", st.session_state["zipcode"])
        centroid = getGeometryCentroid(turnoversGeometry)
        #Now we mix turnoversData with geometry into a Feature, so that it can be added as Geojson layer
        turnoversFeature = geojson.Feature(geometry=turnoversGeometry,
                        properties= {id(x): x for x in turnoversData["rows"]})
   
        
        #Lets write turnovers by age and gender in a file, so that
        #it can be included in a layer

        turnoversByAgeAndGender = Feature(geometry=turnoversGeometry,
                              properties = processTurnovers(turnoversFeature,
                              st.session_state['zipcode']))
        
        (file,fileName)=tempfile.mkstemp(prefix='tmp')
        with open(fileName,'w',encoding="utf-8") as file:
            file.write(turnoversByAgeAndGender.json())

        #Lets keep data for timeseries in session
        st.session_state['turnovers'] = turnoversFeature
        st.session_state['turnoversByAgeAndGender'] = turnoversByAgeAndGender

        #center on centroid of selected postcode
        centroid = getGeometryCentroid(turnoversGeometry)
        st.session_state["lat"] = centroid.y
        st.session_state["lon"] = centroid.x

        #Create map
        m = leafmap.Map(center=[st.session_state["lat"], st.session_state["lon"]], zoom=13,
                    height=map_specs['height'],
                    width=map_specs['width'])
        
        #Add turnovers layer for selected postal code
        m.add_geojson(fileName,layer_name="Turnovers by age and gender ({0})".format(st.session_state["zipcode"]),
            style=style_2,hover_style=hover_style)
        #Add postal codes layer
        m.add_geojson(postalCodesData,layer_name="Postal codes",
            style=style_1,hover_style=hover_style)
                            
    aditionalJavascript = """
        <script>
            Streamlit = top.Streamlit;
            var __assign = (this && this.__assign) || function () {
                __assign = Object.assign || function(t) {
                    for (var s, i = 1, n = arguments.length; i < n; i++) {
                        s = arguments[i];
                        for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p))
                            t[p] = s[p];
                    }
                return t;
                };
                return __assign.apply(this, arguments);
            };
          
            window.store.subscribe(function() {
                var map = window.store.getState().keplerGl.map;
                if (typeof map.visState.clicked != 'undefined') {
                    var object = map.visState.clicked.object;
                    if (typeof object != 'undefined' && typeof object.properties != 'undefined') 
                    {
                           Streamlit.sendBackMsg("streamlit:setComponentValue", {
                                value: { value: map.visState.clicked.object.properties.code},
                                dataType: "json"
                            });
                        
                    }
                
                }
            });
        </script>
    """
    
    html = m.to_html()
    html = html.replace("Object(n.createStore)","window.store=Object(n.createStore)",1)
    closeBodyPos = html.find("</body>")
    
    #Insert aditional javascript before closing </body>
    components.html(
        f"{html[:closeBodyPos]}{aditionalJavascript}{html[closeBodyPos:]}",
        width=map_specs['width'],
        height=map_specs['height'],
        scrolling=False)

    
    #m.to_streamlit()
    
    
with col3:
    
    st.write("Turnovers by age and gender",allow_unsafe_html=True)
    valuesForChart1 = st.session_state['turnoversByAgeAndGender'].properties
    pdf1 = pd.DataFrame([k for k in valuesForChart1.values()],
            index=[k[0]+"-"+k[1] for k in Settings.COMBINED_GROUPS_FIELDS])
    ch1 = st.bar_chart(pdf1,use_container_width=True,width=500,height=200)
    
