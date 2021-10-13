#Configuration class, all values are static
import itertools

class Settings:

    
    #Endpoints
    baseUrl = "http://localhost:8000"
    loginUrl = "{0}/login".format(baseUrl)
    logoutUrl = "{0}/logout".format(baseUrl)
    postalCodesUrl ='{0}/postalCodes'.format(baseUrl)

    #Constants
    GENDERS = ['M','F']
    AGE_GROUPS = ["<=24","25-34","35-44","45-54","55-64",">=65"]

    COMBINED_GROUPS_FIELDS = list(itertools.product(AGE_GROUPS,GENDERS))
    COMBINED_GROUPS_DICT = dict.fromkeys([(x[0] + "-" + x[1]) 
                    for x in COMBINED_GROUPS_FIELDS],0)
   

    
    #Database
    databaseUrl = "postgresql://adm:adm9999@localhost:5432/coolgeo"

    #Errors and msgs
    postalCodeNotFound ='Postal code {0} not found in database'
    loggedOutMsg = 'Successfully logged out'
    loggedInMsg = 'Successfully logged in'
    loggedInBadAuthentication = 'Bad username or password'
    serverShutdownMsg = 'Server Shutdown'

    #Auth and security
    corsAllowed = True
    authEnabled = False
    authSettings = {
        "authjwt_secret_key" : "secret",
        "authjwt_denylist_enabled"  : True,
        "authjwt_denylist_token_checks" : {"access"}
    }
