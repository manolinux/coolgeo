#Configuration class, all values are static


class Settings:

    
    #Endpoints
    baseUrl = "http://localhost:8000"
    loginUrl = "{0}/login".format(baseUrl)
    logoutUrl = "{0}/logout".format(baseUrl)
    postalCodesUrl ='{0}/postalCodes'.format(baseUrl)
    
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
