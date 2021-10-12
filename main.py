
from models import *
from settings import Settings
from typing import Optional, List, Type, Any
from fastapi import FastAPI, Depends, HTTPException, Request, Path, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime 
from shapely.geometry import mapping, shape
from fastapi_jwt_auth import AuthJWT
from fastapi_jwt_auth.exceptions import AuthJWTException
import json
import requests 
import logging
import asyncio
import asyncpg
import pyproj
from shapely.ops import transform

################## DATABASE STUFF ##################################

class Database():

    async def create_pool(self):
        self.pool = await asyncpg.create_pool(dsn=Settings.databaseUrl)
        return self.pool



##################### SOME UTILITY FUNCTIONS ##########################

"""
Obtain postalcode id in database (avoid joins)
"""
def getPostalCodeDBId(code: str):
    try:
        pcDict = getPostalCodesDict(app.postalCodes)
        return pcDict[code]['id']
    except Exception as e:
        #Not found
        return None

"""
Obtain ordered dict from postalCodes, easier to index
"""
def getPostalCodesDict(postalCodes: List):
    pcDict = {}
    for pc in postalCodes:
        pcDict[pc['code']]=pc
    return pcDict



def create_app():

    db = Database()
    app = FastAPI(debug = True)
    
    if Settings.corsAllowed:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=['*']
        )
    

    """
    JWT Initialization
    """
    @AuthJWT.load_config
    def getAuthConfig():
        return AuthSettings(**Settings.authSettings)
    

    @AuthJWT.token_in_denylist_loader
    def checkIfTokenInDenyList(decrypted_token):
        jti = decrypted_token['jti']
        return jti in app.denyTokenList

    @app.middleware("http")
    async def db_session_middleware(request: Request, call_next):
        request.state.pgpool = db.pool
        response = await call_next(request)
        return response


    @app.on_event('startup')
    async def startup():

        #Access to db for shutdown
        app.state.db = db

        #Connection pool
        pool = await db.create_pool()

        #Get logger
        app.logger = logging.getLogger(__name__)

        #Valid tokens list
        app.denyTokenList = []


        #Cache postal codes
        postalCodesQuery = "select ST_AsGeoJSON(the_geom) geom,code,id from postal_codes"
        async with pool.acquire() as connection:
            # Open a transaction.
                async with connection.transaction():
                    try:
                        # Run the query passing the request argument.
                        resultSet = await connection.fetch(postalCodesQuery, timeout=None, record_class=None)
                        postalCodes = []
                        for record in resultSet:
                            postalCodes.append(dict(record))
                    except Exception as e:
                        #Something wrong
                        pass
                    app.postalCodes = postalCodes

    @app.on_event("shutdown")
    async def shutdown():
        try:
            if not app.state.db:
                await app.state.db.close()
        except:
            pass
        app.logger.info(Settings.serverShutdownMsg)


    @app.exception_handler(AuthJWTException)
    def authjwt_exception_handler(request: Request, exc: AuthJWTException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message}
    ) 

    @app.post('/login')
    async def login(user: User, Authorize: AuthJWT = Depends()):
        if user.username != "test" or user.password != "test":
            raise HTTPException(status_code=401,detail=Settings.loggedInBadAuthentication)

        # Create the tokens and passing to set_access_cookies or set_refresh_cookies
        access_token = Authorize.create_access_token(subject=user.username)
   
        return {"msg": Settings.loggedInMsg,
            "access_token" : access_token}


    @app.get('/logout')
    async def logout(Authorize: AuthJWT = Depends()):
        """
        Mark token as unusable
        """
        jti = Authorize.get_raw_jwt()['jti']
        app.denyTokenList.append(jti)
        return {"msg": Settings.loggedOutMsg}


    """
    Example:
    turnovers/202170101/20171001/28028
    """
    @app.get("/turnovers/{fromDate}/{toDate}/{zipCode}")
    async def turnoversEndpoint(fromDate: str, 
                toDate: str,
                zipCode: int,
                request: Request,
                Authorize: AuthJWT = Depends()):
    
        try:
            #Authorization required/optional by settings
            if Settings.authEnabled:  Authorize.jwt_required()
            else: Authorize.jwt_optional()
    
            #Check params, if there is trouble validating params, exception will be raised
        
            turnoverRequest = TurnoverRequest(
                        fromDate = fromDate, toDate = toDate, zipCode = zipCode)
        

            fromDateTs = datetime.strptime(fromDate,'%Y-%m-%d')
            toDateTs = datetime.strptime(toDate,'%Y-%m-%d')
        
            #Build query
            postal_code_id = getPostalCodeDBId(zipCode)

            #Asked for existing data
            if postal_code_id:
                turnoverQuery = """ 
                    select sum(amount) amount,p_gender,p_month,p_age
                    from paystats 
                    where p_month >= '{0}' and p_month <= '{1}' and postal_code_id = {2} 
                    group by p_month,p_gender,p_age
                """.replace('\n',"").format(fromDate,toDate,postal_code_id)
        
                async with request.state.pgpool.acquire() as connection:
                # Open a transaction.
                    async with connection.transaction():
                        # Run the query passing the request argument.
                        turnovers = TurnoversResponse(rows=[])
                        resultSet = await connection.fetch(turnoverQuery, timeout=None, record_class=None)
                        for record in resultSet:
                            turnovers.rows.append(TurnoverResponse(
                                amount = record['amount'],
                                p_month = datetime.strftime(record['p_month'],"%Y-%m-%d"),
                                p_age = record['p_age'],
                                p_gender = record['p_gender'],
                                zipcode = zipCode
                            ))
                        return turnovers
           
        except Exception as e:
            raise HTTPException(status_code=422,detail=str(e))

        #Postal code not found
        raise HTTPException(status_code=422,detail=Settings.postalCodeNotFound.format(zipCode))    
    
    """
    Example:
    turnoversPoint/2015-01-01/2017-10-01/-3.703339/40.416729
    """
    @app.get("/turnoversPoint/{fromDate}/{toDate}/{longitude}/{latitude}")
    async def turnoversPointEndpoint(fromDate: str, 
                toDate: str,
                longitude: float,
                latitude: float,
                request: Request,
                Authorize: AuthJWT = Depends()):
    
        try:
            #Authorization required/optional by settings
            if Settings.authEnabled:  Authorize.jwt_required()
            else: Authorize.jwt_optional()
    
            #Check params, if there is trouble validating params, exception will be raised
        
            turnoverRequest = TurnoverGeomRequest(
                        fromDate = fromDate, toDate = toDate, 
                            longitude=longitude,latitude=latitude)
        

            fromDateTs = datetime.strptime(fromDate,'%Y-%m-%d')
            toDateTs = datetime.strptime(toDate,'%Y-%m-%d')
        
           
            turnoverQuery = """ 
                    select sum(amount) amount,p_gender,p_month,p_age,code
                    from paystats ps,postal_codes pc
                    where ps.p_month >= '{0}' and ps.p_month <= '{1}' and
                    ps.postal_code_id = pc.id and
                    ST_Intersects(pc.the_geom,ST_SetSRID( ST_Point({2},{3}), 4326)) 
                    group by ps.p_month,ps.p_gender,ps.p_age, code
            """.replace('\n',"").format(fromDate,toDate,longitude,latitude)
        
            async with request.state.pgpool.acquire() as connection:
                # Open a transaction.
                    async with connection.transaction():
                        # Run the query passing the request argument.
                        turnovers = TurnoversResponse(rows=[])
                        resultSet = await connection.fetch(turnoverQuery, timeout=None, record_class=None)
                        for record in resultSet:
                            turnovers.rows.append(TurnoverResponse(
                                amount = record['amount'],
                                p_month = datetime.strftime(record['p_month'],"%Y-%m%d"),
                                p_age = record['p_age'],
                                p_gender = record['p_gender'],
                                zipcode = record['code']
                            ))
                        return turnovers
           
        except Exception as e:
            raise HTTPException(status_code=422,detail=str(e))
    
    @app.get("/totalTurnovers/{fromDate}/{toDate}/{zipCode}",response_model = TotalTurnoverResponse)
    async def totalTurnoversEndpoint(fromDate: str, 
                toDate: str,
                zipCode: int,
                request: Request,
                Authorize: AuthJWT = Depends()):
        try:
            #Authorization required/optional by settings
            if Settings.authEnabled:  Authorize.jwt_required()
            else: Authorize.jwt_optional()
          
            #Check params, if there is trouble validating params, exception will be raised
        
            turnoverRequest = TurnoverRequest(
                fromDate = fromDate, toDate = toDate, zipCode = zipCode)
        

            fromDateTs = datetime.strptime(fromDate,'%Y-%m-%d')
            toDateTs = datetime.strptime(toDate,'%Y-%m-%d')
        
            #Build query
            postal_code_id = getPostalCodeDBId(zipCode)

            #Not found data for that postCode
            if postal_code_id is not None:
                turnoverQuery = """ 
                    select sum(amount) amount 
                    from paystats 
                    where p_month >= '{0}' and p_month <= '{1}' and postal_code_id = {2} 
                    """.replace('\n',"").format(fromDate,toDate,postal_code_id)
        
                async with request.state.pgpool.acquire() as connection:
                    # Open a transaction.
                        async with connection.transaction():
                            # Run the query passing the request argument.
                            resultSet = await connection.fetch(turnoverQuery, timeout=None, record_class=None)
                            if len(resultSet) == 1:
                                return TotalTurnoverResponse(amount=resultSet[0]['amount'])
                            else:
                                return TotalTurnoverResponse(amount=None)
                    #Sth went wrong
        except Exception as e:
                raise HTTPException(status_code=422,detail=str(e))

        #Postal code not found
        raise HTTPException(status_code=422,detail=Settings.postalCodeNotFound.format(zipCode))
                           
    """
    postalCodes to be printed in a map
    """

    @app.get("/postalCodes/{crs}")
    async def postalCodesEndpoint(
        crs : Optional[int] = 3587,
        Authorize: AuthJWT = Depends()):
        

        #Authorization required/optional by settings
        if Settings.authEnabled:  Authorize.jwt_required()
        else: Authorize.jwt_optional()

        features = []
        
        for pc in app.postalCodes:
            geometry = shape(json.loads(pc.get('geom')))
            reprojection = pyproj.Transformer.from_proj(
                    pyproj.Proj(init='epsg:4326'), # source coordinate system
                    pyproj.Proj(init='epsg:{0}'.format(str(crs)))) # destination coordinate system

            #Needed reproj?
            if crs != 4326:
                geometry = transform(reprojection.transform, geometry)  # apply projection
            bbox = geometry.bounds
            feature = Feature(
                geometry = geometry,
                properties={'id': pc.get('id'), 'code': pc.get('code')},
                id=pc.get('id'),bbox=bbox)
            features.append(feature)

        fc = FeatureCollection(features=features)
        return fc


    #end create_app
    return app


################# Launch API ######################
app = create_app()


