from pydantic import BaseModel,validator
from datetime import datetime 
from typing import Optional, List, Type, Any, Dict
from settings import Settings
from shapely import wkb
from geojson_pydantic import Feature, FeatureCollection, Point
import geojson
import enum
import re


"""
Validators set here to be reused across models
"""

#Geom must be a WKB hex geometry
#It should be checked too that the SRS is WGS84 for the_geom
#or Spherical Mercator for the_geom_web_merctor
def valWkbGeom(cls,geom):
    try:
        shapelyGeom = wkb.loads(geom,hex=True)
        return geom
    except Exception as e:
        raise ValueError("Value {0} is not a valid geom".format(str(geom)))

#Geom must be a GeoJSON geometry
def valGeoJSONGeom(cls,geom):
    try:
         if geom == None: return None
         geojson.loads(geom)
         return geom
    except Exception as e:
        raise ValueError("Geojson {0} is not a valid geom".format(str(geom)))

#Date must be in format YYYY-mm-dd
def valDate(cls,date):
    try:
        dateStr = datetime.strptime(date,"%Y-%m-%d")
        return dateStr
    except Exception as e:
        raise ValueError("Date {0} is not a valid YYYY-mm-dd date".format(str(date)))


#Validate postal code
def valPostalCode(cls,code):
    if code > 1000 and code < 53000: return code
    else:
        raise ValueError("Postal code value {0} is not valid".format(code))


#Validate gender
def valGender(cls,gender):
    try:
        if gender.upper() == 'M' or gender.upper == 'F': return gender
        raise ValueError("Gender value {0} is not valid".format(gender))
    except:
        raise ValueError("Gender value {0} is not valid".format(gender))

#Validate longitude
def valLongitude(cls,longitude):
    try:
        if longitude > 180 or longitude < -180:
            raise ValueError("Longitude {0} is not valid".format(longitude))
    except:
        raise ValueError("Longitude value {0} is not valid".format(longitude))

#Validate latitude
def valLatitude(cls,latitude):
    try:
        if latitude > 180 or latitude < -180:
            raise ValueError("Latitude {0} is not valid".format(latitude))
    except:
        raise ValueError("Longitude value {0} is not valid".format(latitude))

"""
Model for postal code
"""
class PostalCode(BaseModel):
    #fields
    id: int
    the_geom: Optional[str]
    code: int
    # validators
    _ensure_postal_code: classmethod = validator("code", allow_reuse=True)(valPostalCode)
    _ensure_geom: validator("the_geom",allow_reuse=True)(valWkbGeom)

"""
  GeoJSON postalCodes response
"""
class PostalCodesResponse(BaseModel):
    features: FeatureCollection
    

"""
Model for turnover request
"""
class TurnoverRequest(BaseModel):
    #fields
    fromDate: str
    toDate: str
    zipCode: int

    # validators
    _ensure_from_date: classmethod = validator("fromDate", allow_reuse=True)(valDate)
    _ensure_to_date: classmethod = validator("toDate", allow_reuse=True)(valDate)
    _ensure_postal_code: classmethod = validator("zipCode", allow_reuse=True)(valPostalCode)


"""
Model for turnover request
"""
class TurnoverGeomRequest(BaseModel):
    #fields
    fromDate: str
    toDate: str
    longitude: float
    latitude: float

    # validators
    _ensure_from_date: classmethod = validator("fromDate", allow_reuse=True)(valDate)
    _ensure_to_date: classmethod = validator("toDate", allow_reuse=True)(valDate)
    _ensure_longitude: classmethod = validator("longitude", allow_reuse=True)(valLongitude)
    _ensure_latitude: classmethod = validator("latitude", allow_reuse=True)(valLatitude)


"""
Model for turnover response
"""
class TurnoverResponse(BaseModel):
    #fields
    amount: float
    p_month: str
    p_age: str
    p_gender: str
    zipcode: str
    
"""
Model for turnovers response (list of turnoverResponse)
"""
class TurnoversResponse(BaseModel):
    #fields
    rows : List[TurnoverResponse]

"""
Model for total turnover response
"""
class TotalTurnoverResponse(BaseModel):
    #fields
    amount : float
    
"""
Authentication User
"""
class User(BaseModel):
    username: str
    password: str


"""
Auth settings
"""

class AuthSettings(BaseModel):
    #Secret key for generating tokens
    authjwt_secret_key: str 
    #Deny list for tokens enabled
    authjwt_denylist_enabled: Optional[bool]
    #Deny list 
    authjwt_denylist_token_checks: Optional[set] 
    