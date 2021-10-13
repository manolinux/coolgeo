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

##Session state
def setSessionState(key,value):
        st.session_state[key] = value

##Recreate a text in container
def stContainerText(container,text):
    container.empty()
    with container:
        st.text(text)

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
        st.error(str(e))
    return None

#get Geometry centroid
def getGeometryCentroid(geom):
    return shape(geom).centroid

st.set_page_config(layout="wide")

#Custom html for keeping some things
#postalCodes in advance
postalCodesData = requests.get('http://localhost:8000/postalCodes/4326').json()
st.session_state['postalCodes'] = postalCodesData
st.session_state['lon'] = -3.703889
st.session_state['lat'] = 40.416667
st.session_state['startDate'] = datetime.strptime('2015-01-01','%Y-%M-%d')
st.session_state['endDate'] = datetime.strptime('2017-12-31','%Y-%M-%d')
st.session_state['zipcode'] = '28013'
st.session_state['turnovers'] = None
st.session_state['turnoversByAgeAndGender'] = None

col1, col2,col3 = st.columns((2,3,1))
with col1:
    with st.form("Form 1"): 
        d1 = st.date_input ("Start date" , max_value=datetime.strptime('2017-12-31','%Y-%M-%d'), 
                min_value=datetime.strptime('2015-01-01','%Y-%M-%d'), 
                value=st.session_state["startDate"])
        d2 = st.date_input("End date", min_value=datetime.strptime('2015-01-01','%Y-%M-%d'), 
                max_value=datetime.strptime('2025-12-31','%Y-%M-%d'),
                value=st.session_state["endDate"])
                

        cp = st.text_input("Selected zip code",value=st.session_state["zipcode"])
        b1 = st.form_submit_button("Go!")
        acumHeader = st.subheader('Acummulated')
        periodContainer = st.empty()
        valueContainer = st.empty()
        stContainerText(periodContainer,'Period: N/A')
        stContainerText(valueContainer,'Value: N/A')
    
        if d1 or d2:
            stContainerText(periodContainer,'Period: ' + datetime.strftime(d1,'%Y/%m/%d') + " - " + 
                        datetime.strftime(d2,'%Y/%m/%d'))
            stContainerText(valueContainer,'Value: N/A')
            setSessionState("startDate", d1)
            setSessionState("endDate", d2)
        if cp:
            setSessionState("zipcode",cp)
  
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
        st.write(centroid)
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


                            
    components.html(
        m.to_html(),
        width=map_specs['width'] * 2,
        height=map_specs['height'] * 1.5,
        scrolling=False)
    
    #m.to_streamlit()
    
    
with col3:
    c1 = st.bar_chart(data=None, width=200, height=200, use_container_width=True)
    c2 = st.bar_chart(data=None, width=200, height=200, use_container_width=True)
