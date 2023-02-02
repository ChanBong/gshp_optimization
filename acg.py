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

sdk = TravelTimeSdk('457cb73e', '423d700709835c86c392e5134aee4a11')

ids=[]
addresses = []
latitudes = []
longitudes = []
demand_ids = []

def read_xlsx(filename):
    data = pd.read_excel('data/inter_iit_data/'+filename+'.xlsx')
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

def clean_data(filename, use_cache=False):

    if use_cache:
        clean_data = read_xlsx('cleaned_data_'+filename)
        return clean_data

    data = read_xlsx(filename)
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

    new_file = pd.ExcelWriter('data/inter_iit_data/cleaned_data_'+filename+'.xlsx')
    clean_data.to_excel(new_file)
    new_file.save()

    return clean_data

def reset():
    ids=[]
    addresses = []
    latitudes = []
    longitudes = []
    demand_ids = []

def read_coordinates(clean_data):

    for ind in clean_data.index:
        ids.append(str(len(ids)))
        addresses.append(clean_data['address'][ind])
        longitudes.append(clean_data['longitude'][ind])
        latitudes.append(clean_data['latitude'][ind])
        demand_ids.append(clean_data['product_id'][ind])

def normalize(matrix):
    return (matrix+matrix.T)

def generate_distance_matrix(filename, use_cache=False):

    reset()
    read_coordinates(clean_data(filename, use_cache))

    if use_cache:
        return read_xlsx('distance_matrix_'+filename).to_numpy()

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
    
    distance_matrix = normalize(distance_matrix)

    df = pd.DataFrame(distance_matrix)
    df.to_excel('data/inter_iit_data/distance_matrix_'+filename+'.xlsx', index=False)

    return distance_matrix

def generate_instance(filename, use_cache=False):

    distance_matrix = generate_distance_matrix(filename,use_cache)

    instance_file = open("instances/instance_"+filename+".txt", "w")

    instance_file.write(f"NAME : {filename.upper()}\n")
    instance_file.write(f"COMMENT : INTER_IIT\n")
    instance_file.write(f"TYPE : CVRP\n")
    instance_file.write(f"DIMENSION : {distance_matrix.shape[0]}\n")
    instance_file.write(f"VEHICLES : {read_num_vehicles()}\n")
    instance_file.write(f"EDGE_WEIGHT_TYPE : EXPLICIT\n")
    instance_file.write(f"EDGE_WEIGHT_FORMAT : FULL_MATRIX\n")
    instance_file.write(f"CAPACITY : {read_vehicle_capacity()}\n")

    instance_file.write(f"EDGE_WEIGHT_SECTION\n")
    for row in distance_matrix:
        for item in row:
            instance_file.write(f"{item.astype(int)} ")
        instance_file.write(f"\n")

    instance_file.write(f"NODE_COORD_SECTION\n")
    for index, coordinates in enumerate(get_coordinates()):
        instance_file.write(f"{index+1} {(coordinates[0]*10000).astype(int)} {(coordinates[1]*10000).astype(int)}\n")

    instance_file.write(f"DEMAND_SECTION\n")
    for index, demand in enumerate(get_demands()):
        instance_file.write(f"{index+1} {demand}\n")
    
    instance_file.write(f"DEPOT_SECTION\n{read_depot_index()+1}\n-1\n")
    instance_file.write(f"SERVICE_TIME_SECTION\n")
    for index in range(distance_matrix.shape[0]):
        instance_file.write(f"{index+1} 0\n")
    instance_file.write(f"TIME_WINDOW_SECTION\n")
    for index in range(distance_matrix.shape[0]):
        instance_file.write(f"{index+1} 0 100000\n")
    instance_file.write(f"EOF\n")
    
    instance_file.close()

def generate_pickup_matrix(filename_pickup, filename_delivery, use_cache=False):

    reset()
    read_coordinates(clean_data(filename_pickup, use_cache=True))
    M = len(addresses)
    read_coordinates(clean_data(filename_delivery, use_cache=True))
    N = len(addresses)-M

    if use_cache:
        return read_xlsx('distance_matrix_pickup_to_delivery_'+filename).to_numpy()

    distance_matrix = np.zeros((M,N))

    locations = []

    for ind in range(M+N):
        locations.append(Location(id=str(ind),coords=Coordinates(lat=latitudes[ind], lng=longitudes[ind])))

    for ind in range(M):
      
        departure_search = DepartureSearch(
            id='INTER_IIT',
            arrival_location_ids=ids[M:],
            departure_location_id=ids[ind],
            departure_time=datetime.now(),
            travel_time=14400,
            transportation=Driving(),
            properties=[Property.TRAVEL_TIME, Property.DISTANCE],
        )

        response = sdk.time_filter(locations, [departure_search], [])
        for location in response.results[0].locations:
            distance_matrix[ind,int(location.id)-M] = location.properties[0].distance
    
    df = pd.DataFrame(distance_matrix)
    df.to_excel('data/inter_iit_data/distance_matrix_pickup_to_delivery_'+filename_delivery+'.xlsx', index=False)

    return distance_matrix

print(generate_pickup_matrix('bangalore_pickups','bangalore_dispatch_address_finals'))