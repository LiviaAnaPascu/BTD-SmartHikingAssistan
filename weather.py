import requests
# Make a GET request to retrieve IP address
ipAddr = requests.get('https://api.ipify.org').content.decode('utf8')

def getLocation(ipAddress):
    # Make a GET request to retrieve location data from an API
    responseLocation = requests.get('https://api.geoiplookup.net/?query='+ipAddress+'&json=true')
    # Check if the request was successful (status code 200)
    if responseLocation.status_code == 200:
        # Extract the data from the response
        dataLocation = responseLocation.json()
        lat=dataLocation["latitude"]
        lon=dataLocation["longitude"]
        return lat,lon
    else:
        # Handle the error
        return responseLocation.status_code

def getUVIndex(lat, lon ):
    APIKEY="3dca95e4f3135362a5eb61f243216885"
    # Make a GET request to retrieve UV data from an API
    responseUV = requests.get("https://api.openweathermap.org/data/3.0/onecall?lat="+str(lat)+"&lon="+str(lon)+"&exclude=minutely,hourly,daily,alerts&appid="+APIKEY)
    # Check if the request was successful (status code 200)
    if responseUV.status_code == 200:
        dataUV = responseUV.json()
        current=dataUV["current"]
        uv=current["uvi"]
        return uv
    else:
        # Handle the error
        return responseUV.status_code

def getUVIndexBasedOnIP(ipAddress):
    lat, lon= getLocation(ipAddress)
    return getUVIndex(lat, lon)


def convertUVIndexToString(ipAddress):
    index= getUVIndexBasedOnIP(ipAddress)
    if(index <= 2):
        return "Low"
    if(index >= 3 or index <= 5):
        return "Moderate"
    if(index >=6 or index <= 7):
        return "High"
    if(index >=7 or index <= 10):
        return "Very High"

print(getUVIndexBasedOnIP(ipAddr))