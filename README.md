CARTODB TECHNICAL INTERVIEW TEST

* Tried to do as much as possible when initalizing the server. Thought, as postal codes seemed to be not many, they could be cached (memoized) for later access; there is a postalCodes webcall returning GeoJson (postal codes geoms & properties) that may be used for a map client software (Leaflet, Openlayers, Mapbox)

* Endpoints implemented

  - Endpoint1/ GET Endpoint for getting all postal codes (returns GeoJson)
  /postalCodes/
  Returs a GeoJson containing all the info in postal_codes table, in order to be represented by mapping software
  Geoms are considered to be represented in WGS84 lonlat format, aka EPSG:4326

  - Endpoint2/ GET Endpoint for getting summation of all turnovers in a postalCode during a period
  /totalTurnovers/{fromDate}/{toDate}/{zipCode}

  Example:
  /totalTurnovers/2015-01-01/2017-01-01/28028

  Expected fixed arguments date range, and postal code have been set up as path parameters.
  So, after receiving and cheking arguments (done by Pydantic), checking and dealing with authentication, the pseudocode for second endpoint is:

        * Get postal_code_id primary key in postal_codes table related to postal code,
          it is cached from initialization
        * Consult database, parametrized query:
          
                    select sum(amount) amount 
                    from paystats 
                    where p_month >= '{0}' and p_month <= '{1}' and postal_code_id = {2} 


        * Final results go to TotalTurnoverResponse (serialized into JSON) object (which in fact has only an amount field)
        * In case of validation errors, a 422 HTTP code (non-processed entity) is issued, resulting in a Json that has a field containing deatils of fail.

- Endpoint3/ Endpoint for getting details of all turnovers in a postalCode during a period, 
  grouping by group age, month, and gender
  /turnovers/{fromDate}/{toDate}/{zipCode}

  Example:
  /turnovers/2015-01-01/2017-01-01/28028

  This endpoint is expected to be used for timeseries widgets.
  Expected fixed arguments date range, and postal code have been set up as path parameters.
  So, after receiving and cheking arguments (done by Pydantic), checking and dealing with authentication, the pseudocode for third endpoint is:

        * Get postal_code_id primary key in postal_codes table related to postal code,
          it is cached from initialization
        * Consult database, parametrized query:
                    
                    select sum(amount) amount,p_gender,p_month,p_age
                    from paystats 
                    where p_month >= '{0}' and p_month <= '{1}' and postal_code_id = {2} 
                    group by p_month,p_gender,p_age
          

        * Final results go to TurnoverResponse (serialized into JSON) object (which in fact has 
        following fields: amount, p_month,p_age,p_gender,zipcode
        * In case of validation errors, a 422 HTTP code (non-processed entity) is issued, resulting in a Json that has a field containing deatils of fail.

- Endpoint4/ GET Endpoint for getting details of all turnovers in the postalcode which was 
  clicked  in the frontend (thus we have lat lon coordinates) during a period, grouping by group age, month, and gender
  /turnoversPoint/{fromDate}/{toDate}/{longitude}{latitude}

  Example:
  /turnoversPoint/2015-01-01/2017-10-01/-3.70256/40.4165

  This endpoint is expected to be used for showing details of postal codes clicked in frontend.
  Expected fixed arguments date range, longitude and latitude. They have been set up as path parameters.
  So, after receiving and cheking arguments (done by Pydantic), checking and dealing with authentication, the pseudocode for third endpoint is:

        
        * Consult database, parametrized query:

                    select sum(amount) amount,p_gender,p_month,p_age,code
                    from paystats ps,postal_codes pc
                    where ps.p_month >= '{0}' and ps.p_month <= '{1}' and
                    ps.postal_code_id = pc.id and
                    ST_Intersects(pc.the_geom,ST_SetSRID( ST_Point({2},{3}), 4326)) 
                    group by ps.p_month,ps.p_gender,ps.p_age, code

          In this case, we don't have a postal code to lookup, but a point that must intersect
          with geometries that are recovered (resulting in a database table join)
                    
        * Final results go to TurnoverResponse (serialized into JSON) object (which in fact has 
        following fields: amount, p_month,p_age,p_gender,zipcode
        * In case of validation errors, a 422 HTTP code (non-processed entity) is issued, resulting in a Json that has a field containing deatils of fail.


* About authentication

  FastAPI endpoints have been protected using a simple JWT Authentication Bearer schema.
  By default it is disabled. Can be enabled by Settings.authEnabled (settings.py file).

  Logout is implemented including token in a denylist; as it is not permanent by the moment, a server reload would imply that a denied token could be used again. Lists of tokens/users should be stored permanently in a database system. Redis could be a good alternative too. This simple system has not a mechanism of refreshing tokens, either, an expired token would force to ask the API for a new one. FastAPI JWT extension can deal with refresh tokens, and store them in cookies. The current way is via Authentication Bearer header in HTTP.

  User for this demo API is:  test / test

  The API should be protected with HTTPS too. No interchange of sensitive information should be carried out without encrypted support.
  Uvicorn (the web server in which FastAPI is executed) has easy support for HTTPS. Certificate could be obtained via Let's Encrypt / Certbot, for instance

  There are two endpoints for logging in and out:

  * POST endpoint /login, requiring username and password parameters in a JSON request
    Returns JSON object with access_token 
        
            {"msg": Settings.loggedInMsg,
            "access_token" : access_token}

  *  GET endpoint /logout
    _Marks acces token as unusable and returns JSON object telling the final status of the operation.
          
          return {"msg": Settings.loggedOutMsg}

* Deploy

  a/Vanilla Deploy
  * Build a virtualenv in downloaded folder
    $ virtualenv .

    * Activate environment:
    $ source bin/activate   (bash)
    $ . bin/activate (sh)

  * Install requirements
    $ pip3 install -r requirements.txt

  * Run api inside uvicorn
    $ uvicorn --reload --port 8000 main:app & disown
  
  * Run streamlit (not required)

    $ streamlit run streamlit_app.py & disown

    Disown is a BASH extension, so if not running bash, we could use nohup
    $ nohup uvicorn --reload --port 8000 main:app &
    $ nohup streamlit run streamlit_app.py &
   

b/Docker Deployment
  Deployment can be done in a Docker container, building it from scratch with the offered 
  Dockerfile.
  Image exposes two ports, 8000 for API, and 8001 for Streamlit.
 
 * Building :
   docker build . -t coolgeo

 * Running
   docker run  -d  -p 8000:8000 -p 8001:8001 coolgeo

* Streamlit visualization (Not finished due to some problems with maps)

  A minimal Streamlit application has been made for the sake of curiosity, and to be able to visualize easily results. Not fully functional app, tried to make a mock for endpoints, but folium under streamlit seems to be faulty and lacking interactivity. Should have been better to go ahead with a plain javascript mock, this is my fault. But i love Streamlit concept!

* Testing
  Unit tests, using for instance, Python unittest, have to be implemented.
  Tests can also be performed via the excellent ThunderClient replacement for Postman inside Visual Studio Code.

* List of technolgies used

  - Python 3.8, virtualenv or conda for environment separation
  - Postgresql 11 with Postgis 2.5 under Debian 10
  - Tried to import data into database with GDAL's ogr2ogr, but seems to not understand geometries
    in geojson format no matter what options I used or explanations I followed.
  - Anyway, you can import into database with excellent COPY command, with previous creation of
  tables, users, and all database stuff
  - Created two users in database, "usr" with just read access and "admin", which is the owner of relationships created and has full access to tables (read and write).
  - Uvicorn as web server, and FastAPI for (just knew Flask, and I wanted to learn more about FastAPI)
  - asyncpg for asyncio operations on database 
  - Pydantic, very nice for modelling requests and responses when working with APIs. 
  Using for seralizing, deserializing request and responses and performing checks.
  - Shapely for some vector data tweaking (geojson)
  - Visual Studio Code, the best IDE I know (at least for Python)
  - Thunder Client plugin for Visual Studio Code, as a replacement for Postman, great to check APIs
  - Streamlit for visualization. I really love Streamlit, it's possibilities are endless!
  - Docker for containerization and distribution

* To be done

  - Go HTTPS, uvicorn and fastapi have no problems with https (Certbot and Let's encrypt for certificates, for example)
  - Improve checks for models 
  - Improve error handling (there is very little there)
  - Add more endpoints
  - Improve authentication. The JWT Token Bearer authentication is very simple, tokens are in denylist in memory, when server reboots denylist is lost, which allows an invalid token to enter the app. Could implement another scheme, like OAuth2, etc, or improve JWT with refresh tokens support and session backend storage and retrieval (database, Redis).
  - Integrate maps in streamlit app with Folium or replacement

Manuel Cotallo
10/10/2021


Second commit:
* Kepler gl backend for maps
* Showing postal codes
* Showing turnovers when a postal code is selected in left box for postal code.
  Bidirectionality is not already working for leafmap.kepler. If you press in the map, you won't get that data transferred to left part of app.

* Getting turnovers for selected zip code in left panel (in fact there are two layers at kepler map, Postal Codes and Turnovers). Data for a given timeseries is there, but no way to show a customized popup to show the info as stated in mock picture of app). Leafmap will evolve, and i think I'll get it soon ...

* Postal codes endpoint has also a new param allowing recovery in distinct CRS (3857 instead of 43265, last path param of endpoint controls the srs numbered as EPSG code.)

Manuel Cotallo
10/12/2021

Third commit:
* Two layers in map: postal codes and turnovers per age and gender (calculated in the python
  Streamlit app from turnoversEndpoint by postalCode). Second layer is dynamic, map refreshes 
  when postalCode is changed
* Map centers on centroid of selected postal code.
* Each layer shows the fields it contains; "Turnovers per age and gender" has a field per 
  combined age/gender group.
* Should be fine to capture callback from clicking in the map and then refreshing calculations
  (investigating if it is possible or not)
* Bar/Timeseries widgets have not been added, soon to be.
* Should delete temporary geojson files for add_geojson()

Manuel Cotallo
10/13/2021

 Fourth commit:
 - Minimal bar char for turnovers by age and gender
 
 Manuel Cotallo
 10/14/2021

 Fifth commit:
 - Improvements in communication map/form, so that when a postal code is clicked, it's info
 is selected in form, and data reloaded
 10/19/2021