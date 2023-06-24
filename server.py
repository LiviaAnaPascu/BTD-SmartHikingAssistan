import requests
import socket
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
    responseUV = requests.get("https://api.openweathermap.org/data/3.0/onecall?lat="+str(lat)+"&lon="+str(lon)+"&exclude=minutely,hourly,daily,alerts&appid="+APIKEY)
    dataUV = responseUV.json()
    current=dataUV["current"]
    uv=current["uvi"]
    return uv

def getUVIndexBasedOnIP(ipAddress):
    lat, lon= getLocation(ipAddress)
    return getUVIndex(lat, lon)