import requests
import numpy as np
import pandas as pd

from datetime import datetime
from traveltimepy.dto import Location, Coordinates
from traveltimepy.dto.requests import FullRange, Property
from traveltimepy.dto.requests.time_filter import DepartureSearch, ArrivalSearch
from traveltimepy.transportation import Driving
from traveltimepy.sdk import TravelTimeSdk

bangalore_latitude = 12.9716
bangalore_longitude = 77.5946

sdk = TravelTimeSdk('35c415e7', '58f656d94a27fee4533f3e2ba90d0d8c')

ids=[]
addresses = []
latitudes = []
longitudes = []
demand_ids = []

def read_file(filename):
    data = pd.read_excel(filename)
    return data

def read_num_vehicles():
    return 5 # chosen arbitrarily

def read_vehicle_capacity():
    return 20 # chosen arbitrarily

def read_depot_index():
    return 0 # chosen arbitrarily

def get_coordinates():
    coordinates = []
    for latitude, longitude in zip(latitudes, longitudes):
        coordinates.append((latitude,longitude))
    return coordinates

def get_demands():
    demands = []
    for demand_id in demand_ids:
        # demands.append(get_volume_from_id(demand_id))
        demands.append(2) # chosen arbitrarily
    return demands

def get_geocoding(address):
    url = 'https://api.distancematrix.ai/maps/api/geocode/json?region=in&address='+address+'&key=sPIe2SlBdFdJTI0sO269iEW1rPkV9'
    resp = requests.get(url=url)
    data = resp.json()

    if 'status' in data:
        if data['status']=='OK':
            latitude = data['result'][0]['geometry']['location']['lat']
            longitude = data['result'][0]['geometry']['location']['lng']
            return True, latitude, longitude

    return False, 0., 0.

def get_geokeo_geocoding(address):
  
    url = 'https://geokeo.com/geocode/v1/search.php?q='+address+'g&country=in&api=f2f301246e829748673b208f2275bd49'
    resp = requests.get(url=url)
    data = resp.json()

    if 'status' in data:
        if data['status']=='ok':
            clean_address = data['results'][0]['formatted_address']
            latitude = data['results'][0]['geometry']['location']['lat']
            longitude = data['results'][0]['geometry']['location']['lng']
            return True, latitude, longitude

    return False, 0., 0.

def clean_address(address):

    address = address.lower()
    address = address.replace('#',"")
    address = address.replace('&',"")
    address = address.replace('/',"")
    address = address.replace('?',"")
    address = address.replace("st","")
    address = address.replace("nd","")
    address = address.replace("th","")
    address = address.replace("floor","")
    return address

def clean_data(filename):

    data = read_file(filename)
    clean_data = data
    Latitude = []
    Longitude = []

    for index, address in enumerate(data['address']):

        status, latitude, longitude = get_geocoding(address)
        if status and (abs(float(latitude)-bangalore_latitude)<1.) and (abs(float(longitude)-bangalore_longitude)<1.) :
            Latitude.append(latitude)
            Longitude.append(longitude)
            continue
        
        original_address = address
        address = clean_address(address)
        status, latitude, longitude = get_geocoding(address)
        if status and (abs(float(latitude)-bangalore_latitude)<1.) and (abs(float(longitude)-bangalore_longitude)<1.) :
            Latitude.append(latitude)
            Longitude.append(longitude)
            continue
        
        address = original_address
        status, latitude, longitude = get_geokeo_geocoding(address)
        if status and (abs(float(latitude)-bangalore_latitude)<1.) and (abs(float(longitude)-bangalore_longitude)<1.) :
            Latitude.append(latitude)
            Longitude.append(longitude)
            continue
        
        clean_data = clean_data.drop(index=index)

    clean_data['latitude'] = Latitude
    clean_data['longitude'] = Longitude

    return clean_data

def read_coordinates(clean_data):

    for ind in clean_data.index:
        ids.append(str(ind))
        addresses.append(clean_data['address'][ind])
        longitudes.append(clean_data['longitude'][ind])
        latitudes.append(clean_data['latitude'][ind])
        demand_ids.append(clean_data['product_id'][ind])

def generate_distance_matrix(filename):

    read_coordinates(clean_data(filename))

    N = len(addresses)
    distance_matrix = np.zeros((N,N))

    locations = []

    for ind in range(N):
        locations.append(Location(id=str(ind),coords=Coordinates(lat=latitudes[ind], lng=longitudes[ind])))

    for ind in range(N):
      
        departure_search = DepartureSearch(
            id='INTER_IIT',
            arrival_location_ids=ids,
            departure_location_id=ids[ind],
            departure_time=datetime.now(),
            travel_time=14400,
            transportation=Driving(),
            properties=[Property.TRAVEL_TIME, Property.DISTANCE],
        )

        response = sdk.time_filter(locations, [departure_search], [])
        for location in response.results[0].locations:
            distance_matrix[ind,int(location.id)] = location.properties[0].distance

    return distance_matrix

print(generate_distance_matrix('data/inter_iit_data/bangalore_pickups.xlsx'))