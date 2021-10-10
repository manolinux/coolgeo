from pydantic.errors import DataclassTypeError
import streamlit as st
from streamlit_folium import folium_static
from settings import Settings
from datetime import datetime,date
import requests
import leafmap.leafmap as leafmap
import pandas as pd
import json
import sys
from shapely import wkb
import requests
import jinja2

##Recreate a text in container
def stContainerText(container,text):
    container.empty()
    with container:
        st.text(text)

st.set_page_config(layout="wide")

#Custom html for keeping some things
s1 = """<input type="hidden" id="lon"/>"""
s2 = """<input type="hidden" id="lat"/>"""
s3 = """<input type="hidden" id="zipcode"/>"""
 
h1 = st.markdown(s1,unsafe_allow_html=True)
h2 = st.markdown(s2,unsafe_allow_html=True)
h3 = st.markdown(s3,unsafe_allow_html=True)


col1, col2,col3 = st.columns((2,3,1))
with col1:
    with st.form("Form 1"): 
        d1 = st.date_input ("Start date" , value=datetime.strptime('2015-01-01','%Y-%M-%d') , min_value=datetime.strptime('2015-01-01','%Y-%M-%d'), 
                max_value=datetime.strptime('2025-12-31','%Y-%M-%d') , key=None )
        d2 = st.date_input ("End date" , value=datetime.strptime('2017-12-31','%Y-%M-%d') , min_value=datetime.strptime('2015-01-01','%Y-%M-%d'), 
                max_value=datetime.strptime('2025-12-31','%Y-%M-%d') , key=None )

        cp = st.text_input("Selected zip code",value="28028")
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
    style = {
        "stroke": True,
        "color": "#0000ff",
        "weight": 2,
        "opacity": 1,
        "fill": True,
        "fillColor": "#0000ff",
        "fillOpacity": 0.1,
    }

    hover_style = {"fillOpacity": 0.7}
    m = leafmap.Map(center=[40, -3], zoom=10,
        draw_control=False, measure_control=False, fullscreen_control=True, attribution_control=True)
    m.add_geojson('http://localhost:8000/postalCodes',layer_name="Postal codes",
            style=style,hover_style=hover_style)
    m.to_streamlit(width=700, height=500)
    
with col3:
    c1 = st.bar_chart(data=None, width=200, height=200, use_container_width=True)
    c2 = st.bar_chart(data=None, width=200, height=200, use_container_width=True)
