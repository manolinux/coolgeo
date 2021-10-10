from pydantic.errors import DataclassTypeError
import streamlit as st
from streamlit_folium import folium_static
from settings import Settings
from datetime import datetime,date
import requests
import folium
import pandas as pd
import json
import sys
from shapely import wkb
import requests
import jinja2

#Override for popup
class MyLatLngPopup(folium.LatLngPopup):
    """
    When one clicks on a Map that contains a LatLngPopup,
    a popup is shown that displays the latitude and longitude of the pointer.

    """
    _template = jinja2.Template(u"""
            {% macro script(this, kwargs) %}
              
              function latLngPop(e) {
                    var startDate=querySelectorAllInIframes("input[id='startDate']");
                    var endDate=querySelectorAllInIframes("input[id='endDate']");
                    var lonInput = querySelectorAllInIframes("input[id='lon']");
                    var latInput = querySelectorAllInIframes("input[id='lat']");
                    lonInput.value = e.latlng.lng;
                    latInput.value = e.latlng.lat;
                    console.log(lonInput);
                    console.log(latInput);
                    {{this.get_name()}}
                        .setLatLng(e.latlng)
                        .setContent("Latitude: " + e.latlng.lat.toFixed(4) +
                                    "<br>Longitude: " + e.latlng.lng.toFixed(4))
                        //.openOn({{this._parent.get_name()}});
                    }
                {{this._parent.get_name()}}.on('click', latLngPop);
            {% endmacro %}
            """)  # noqa

    def __init__(self):
        super(MyLatLngPopup, self).__init__()
        self._name = 'MyLatLngPopup'

#Read in advance postal code layer data
postalCodesData = requests.get('http://localhost:8000/postalCodes').json()


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


col1, col2,col3 = st.columns((1,4,1))
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
    map = folium.Map(tiles="Stamen Terrain", 
            location=[40.416729, -3.703339], zoom_start=12)

    tooltip = folium.features.GeoJsonTooltip(
            fields=['code'],
            aliases=['Postal code:'],
    )   

    postalCodesLayer =  folium.GeoJson(
        data=postalCodesData,
        style_function=lambda x: {
            'fillColor': 'lightblue',
            'color': 'black',
            'weight': 1,
            'fillOpacity':0.7
        },
        highlight_function=lambda x: {
            'fillOpacity':1
        },
        tooltip=tooltip,
        name='Postal Codes').add_to(map) 
    
    popup1 = MyLatLngPopup()
    map.add_child(popup1)
    folium_static(map)
    

with col3:
    c1 = st.bar_chart(data=None, width=200, height=200, use_container_width=True)
    c2 = st.bar_chart(data=None, width=200, height=200, use_container_width=True)
