import requests, re
import numpy as np
import pandas as pd
import json
import os
import tools, geojson

from datetime import datetime
from traveltimepy.dto import Location, Coordinates
from traveltimepy.dto.requests import FullRange, Property
from traveltimepy.dto.requests.time_filter import DepartureSearch, ArrivalSearch
from traveltimepy.transportation import Driving
from traveltimepy.sdk import TravelTimeSdk

bangalore_latitude = 12.9709411	
bangalore_longitude = 77.6385078

sdk = TravelTimeSdk('457cb73e', '423d700709835c86c392e5134aee4a11')

address_cache = pd.DataFrame()
ids=[]
addresses = []
latitudes = []
longitudes = []
demand_ids = []
demands = []
time_windows = []

def fetch_delivery_from_api(filename = 'delivery'):
    url = "https://interiit.msqu4re.me/delivery"
    headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
    response = requests.get(url, headers=headers)

    with open(filename+'.json', 'w') as f:
        json.dump(response.json(), f)

    with open(filename+'.json', 'r') as f:
        json_data = json.loads(f.read())

    data_from_api = pd.json_normalize(json_data, record_path=['deliveries']) 
    columns = ['id', 'type', 'address', 'AWB', 'names', 'product_id', 'EDD']
    data_from_api.columns = columns   
    deliveries_file = 'data/inter_iit_data/' + filename + '.xlsx'
    data_from_api.to_excel(deliveries_file, index=False)

    os.remove(filename+'.json')
    return deliveries_file

def fetch_pickup_from_api(filename = 'pickup'):
    url = "https://interiit.msqu4re.me/pickup"
    headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
    response = requests.get(url, headers=headers)

    with open(filename+'.json', 'w') as f:
        json.dump(response.json(), f)

    with open(filename+'.json', 'r') as f:
        json_data = json.loads(f.read())

    data_from_api = pd.json_normalize(json_data, record_path=['pickups']) 
    print(data_from_api)
    columns = ['id', 'address', 'AWB', 'names', 'product_id', 'EDD', 'type', 'completed', 'itemID', 'routeId']
    data_from_api.columns = columns   
    pickups_file = 'data/inter_iit_data/' + filename + '.xlsx'
    data_from_api.to_excel(pickups_file, index=False)

    os.remove(filename+'.json')
    return pickups_file

def read_xlsx(filename):
    data = pd.read_excel('data/inter_iit_data/'+filename+'.xlsx')
    return data

def read_cache():
    global address_cache
    address_cache = read_xlsx('address_cache')

def read_num_vehicles():
    return int(len(addresses)/20) # chosen arbitrarily

def read_vehicle_capacity():
    return 30

def read_depot_index():
    return 0 

def get_coordinates():
    coordinates = []
    for latitude, longitude in zip(latitudes, longitudes):
        coordinates.append((latitude,longitude))
    return coordinates

def get_avg_speed(filename):

    distance = read_xlsx('distance_matrix_'+filename)
    time = read_xlsx('time_matrix_'+filename)

    return distance.sum().sum()/time.sum().sum()

def get_distmat_geocoding(address):
    print("## Address", address)
    url = 'https://api.distancematrix.ai/maps/api/geocode/json?region=in&address='+address+'&key=xtT8ArMnjkIXCLqiSDRsNraE6u2ap'
    resp = requests.get(url=url)
    data = resp.json()

    if 'status' in data:
        if data['status']=='OK':
            latitude = data['result'][0]['geometry']['location']['lat']
            longitude = data['result'][0]['geometry']['location']['lng']
            return True, latitude, longitude
    print(data['status'])
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
    print(data['status'])
    return False, 0., 0.

def clean_address(address):

    address = address.lower()
    address = address.replace('#',"")
    address = address.replace('&',"")
    address = address.replace('/',"")
    address = address.replace('?',"")
    address = address.replace("st "," ")
    address = address.replace("nd "," ")
    address = address.replace("th "," ")
    address = address.replace("floor "," ")
    return address

def clean_address_complete(address):

    address = address.lower()
    # address = address.replace(',',' ')
    address = address.replace('bangalore',' ')

    stop_words = ['#','&','/','?','floor ','behind ','adjacent to ','opposite to ','in front of ','in front ','next to ','next ','above ','off ']
    locality = ['jp nagar','hsr','indiranagar','mth','marathahalli','kr puram']
    for word in stop_words:
        address = address.replace(word," ")

    for word in locality:
        res = address.find(word)
        if res == -1:
            continue
        address = address.replace(word,"")
        address = address + " " + word
        

    address = address + ', bangalore'
    address = re.sub(',(,| )+',', ', address)

    return address

def get_geocoding_api(address):
    read_cache()
    return get_geocoding(address)

def get_geocoding(address):
    global address_cache

    original_address = address
    if(address in set(address_cache['address'])):
        latitude = list(address_cache['latitude'].loc[address_cache['address']==address])[0]
        longitude = list(address_cache['longitude'].loc[address_cache['address']==address])[0]
        return latitude, longitude

    status, latitude, longitude = get_distmat_geocoding(address)
    if status and (abs(float(latitude)-bangalore_latitude)<1.) and (abs(float(longitude)-bangalore_longitude)<1.) :
        address_cache.loc[len(address_cache.index)] = [original_address, latitude, longitude] 
        return latitude, longitude
    
    address = clean_address(address)
    status, latitude, longitude = get_distmat_geocoding(address)
    if status and (abs(float(latitude)-bangalore_latitude)<1.) and (abs(float(longitude)-bangalore_longitude)<1.) :
        address_cache.loc[len(address_cache.index)] = [original_address, latitude, longitude] 
        return latitude, longitude
    
    address = original_address
    status, latitude, longitude = get_geokeo_geocoding(address)
    if status and (abs(float(latitude)-bangalore_latitude)<1.) and (abs(float(longitude)-bangalore_longitude)<1.) :
        address_cache.loc[len(address_cache.index)] = [original_address, latitude, longitude]
        return latitude, longitude

    return 0, 0

def clean_data(filename, use_cache=False, add_hub = True):

    print(filename)
    if use_cache:
        return read_xlsx('clean_data_'+filename)

    global address_cache
    read_cache()
    data = read_xlsx(filename)
    print(data)
    if add_hub :
        hub = pd.DataFrame({'address':'1075-I, 5th Cross Rd, North, Appareddipalya, Indiranagar, Bengaluru, Karnataka 560008', 'AWB':'00000000000', 'names':'GrowSimplee', 'product_id':'0', 'EDD':'13-02-2023'}, index=[0])
        data = pd.concat([hub,data.loc[:]]).reset_index(drop=True)
    clean_data = data
    print(data)
    Latitude = []
    Longitude = []

    for index, address in enumerate(data['address']):
        print(index)
        latitude, longitude = get_geocoding(address)
        if latitude == 0 and longitude == 0:
            clean_data = clean_data.drop(index=index)
        else :
            Latitude.append(latitude)
            Longitude.append(longitude)

    clean_data['latitude'] = Latitude
    clean_data['longitude'] = Longitude
    address_cache = address_cache.drop_duplicates()
    address_cache.to_excel('data/inter_iit_data/address_cache.xlsx', index=False)
    new_file = pd.ExcelWriter('data/inter_iit_data/clean_data_'+filename+'.xlsx')
    clean_data.to_excel(new_file)
    new_file.save()

    return clean_data

def add_to_cache(filename):

    data = read_xlsx('clean_data_'+filename)[['address','latitude','longitude']]
    original_data = read_xlsx('address_cache')

    data = pd.concat([original_data,data],ignore_index = True).drop_duplicates()
    data.to_excel('data/inter_iit_data/address_cache.xlsx', index=False)

def reset():
    global ids, addresses, latitudes, longitudes, demand_ids, demands, time_windows
    ids=[]
    addresses = []
    latitudes = []
    longitudes = []
    demand_ids = []
    demands = []
    time_windows = []

def read_coordinates(clean_data, endpoints = False, pickups = False):

    for ind in clean_data.index:
        ids.append(str(len(ids)))
        addresses.append(clean_data['address'][ind])
        longitudes.append(clean_data['longitude'][ind])
        latitudes.append(clean_data['latitude'][ind])
        demand_ids.append(clean_data['product_id'][ind])
        # demands.append(get_volume(demand_ids[ind]))
        if endpoints :
            demands.append(1000)
        else :
            demands.append(1)
        if not (pickups or endpoints) :
            time_windows.append(int(str(clean_data['EDD'][ind]).split('-')[0]))
    if not (pickups or endpoints) :
        minimum_time_window = min(time_windows)
        for index, _ in enumerate(time_windows):
            time_windows[index] = time_windows[index] - minimum_time_window
        time_windows[0] = max(time_windows[1:])

def normalize(matrix):
    return (matrix+matrix.T)/2

def generate_matrix(filename, use_cache=False, edge_weight = 'time'):

    reset()
    read_coordinates(clean_data(filename, use_cache))

    if use_cache:
        return read_xlsx(edge_weight+'_matrix_'+filename).to_numpy()

    N = len(addresses)
    distance_matrix = np.zeros((N,N))
    time_matrix = np.zeros((N,N))

    locations = []

    for ind in range(N):
        locations.append(Location(id=str(ind),coords=Coordinates(lat=latitudes[ind], lng=longitudes[ind])))

    for ind in range(N):
        print(ind)
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
            time_matrix[ind,int(location.id)] = location.properties[0].travel_time
    
    distance_matrix = normalize(distance_matrix)
    time_matrix = normalize(time_matrix)

    df = pd.DataFrame(distance_matrix)
    df.to_excel('data/inter_iit_data/distance_matrix_'+filename+'.xlsx', index=False)
    df = pd.DataFrame(time_matrix)
    df.to_excel('data/inter_iit_data/time_matrix_'+filename+'.xlsx', index=False)

    if edge_weight == 'distance' :
        return distance_matrix
    else :
        return time_matrix

def generate_pickup_matrix(filename_pickup, filename_endpoint, use_cache=False, edge_weight = 'time'):

    reset()
    read_coordinates(clean_data(filename_endpoint, use_cache), endpoints = True)
    read_coordinates(clean_data(filename_pickup, use_cache, add_hub = False), pickups = True)
    
    if use_cache:
        return read_xlsx(edge_weight+'_matrix_pickups_to_endpoint_'+filename_pickup).to_numpy()

    N = len(addresses)
    distance_matrix = np.zeros((N,N))
    time_matrix = np.zeros((N,N))

    locations = []

    for ind in range(N):
        locations.append(Location(id=str(ind),coords=Coordinates(lat=latitudes[ind], lng=longitudes[ind])))

    for ind in range(N):
        print(ind)
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
            time_matrix[ind,int(location.id)] = location.properties[0].travel_time
    
    distance_matrix = normalize(distance_matrix)
    time_matrix = normalize(time_matrix)

    df = pd.DataFrame(distance_matrix)
    df.to_excel('data/inter_iit_data/distance_matrix_'+filename_pickup+'.xlsx', index=False)
    df = pd.DataFrame(time_matrix)
    df.to_excel('data/inter_iit_data/time_matrix_'+filename_pickup+'.xlsx', index=False)

    if edge_weight == 'distance' :
        return distance_matrix
    else :
        return time_matrix

def generate_ptop_matrix(filename_pickup, filename_delivery, use_cache=False, edge_weight = 'time', harsh = True):

    reset()
    read_coordinates(clean_data(filename_delivery, use_cache, add_hub= harsh), endpoints = True)
    N = len(addresses)
    read_coordinates(clean_data(filename_pickup, use_cache, add_hub = False), pickups = True)
    M = len(addresses)-N
    
    print(N, M)

    if use_cache:
        return read_xlsx(edge_weight+'_matrix_pickups_to_delivery_'+filename_pickup).to_numpy()

    distance_matrix = np.zeros((M,N+M))
    time_matrix = np.zeros((M,N+M))

    locations = []

    for ind in range(M+N):
        locations.append(Location(id=str(ind),coords=Coordinates(lat=latitudes[ind], lng=longitudes[ind])))

    for ind in range(N,M+N):
        print(ind)
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
            distance_matrix[ind-N,int(location.id)] = location.properties[0].distance
            time_matrix[ind-N,int(location.id)] = location.properties[0].travel_time
    
    df = pd.DataFrame(distance_matrix)
    df.to_excel('data/inter_iit_data/distance_matrix_pickups_to_delivery_'+filename_pickup+'.xlsx', index=False)
    df = pd.DataFrame(time_matrix)
    df.to_excel('data/inter_iit_data/time_matrix_pickups_to_delivery_'+filename_pickup+'.xlsx', index=False)

    if edge_weight == 'distance' :
        return distance_matrix
    else :
        return time_matrix

def generate_instance(filename, use_cache = False, edge_weight = "time", one_day_time = 18000, pickups = False, pickup_filename = ""):

    if pickups == True :
        matrix = generate_pickup_matrix(pickup_filename, filename, use_cache)
    else :
        matrix = generate_matrix(filename,use_cache)

    instance_file = open("instances/instance_"+edge_weight+"_"+str(one_day_time)+"_"+filename+".txt", "w")

    instance_file.write(f"NAME : {filename.upper()}\n")
    instance_file.write(f"COMMENT : INTER_IIT\n")
    instance_file.write(f"TYPE : CVRP\n")
    instance_file.write(f"DIMENSION : {matrix.shape[0]}\n")
    if pickups :
        instance_file.write(f"VEHICLES : {read_xlsx(filename).shape[0]-1}\n")
    else :
        instance_file.write(f"VEHICLES : {read_num_vehicles()}\n")
    instance_file.write(f"EDGE_WEIGHT_TYPE : EXPLICIT\n")
    instance_file.write(f"EDGE_WEIGHT_FORMAT : FULL_MATRIX\n")
    instance_file.write(f"CAPACITY : {read_vehicle_capacity()}\n")

    instance_file.write(f"EDGE_WEIGHT_SECTION\n")
    for row in matrix:
        for item in row:
            instance_file.write(f"{item.astype(int)} ")
        instance_file.write(f"\n")

    instance_file.write(f"NODE_COORD_SECTION\n")
    for index, coordinates in enumerate(get_coordinates()):
        instance_file.write(f"{index+1} {(int)(coordinates[0]*10000)} {(int)(coordinates[1]*10000)}\n")

    instance_file.write(f"DEMAND_SECTION\n")
    demands[0] = 0
    for index, demand in enumerate(demands):
        instance_file.write(f"{index+1} {demand}\n")
    
    instance_file.write(f"DEPOT_SECTION\n{read_depot_index()+1}\n-1\n")
    instance_file.write(f"SERVICE_TIME_SECTION\n")
    for index in range(matrix.shape[0]):
        instance_file.write(f"{index+1} 0\n")
    instance_file.write(f"TIME_WINDOW_SECTION\n")

    if pickups :
        for index in range(matrix.shape[0]):
            instance_file.write(f"{index+1} 0 {one_day_time}\n")
    else :
        for index in range(matrix.shape[0]):
            instance_file.write(f"{index+1} 0 {(time_windows[index]+1)*one_day_time}\n")
    
    instance_file.write(f"EOF\n")
    
    instance_file.close()

    return instance_file.name

def get_endpoints(filename,solution_filename="solution_example"):

    cost, routes, no_of_riders = tools.read_solution('solutions/'+solution_filename)
    endpoints = []
    for route in routes:
        endpoints.append(route[-2])

    data = read_xlsx('clean_data_'+filename).iloc[endpoints]
    data.to_excel('data/inter_iit_data/'+filename+'_'+solution_filename+'.xlsx',index = False)

    return filename+'_'+solution_filename

# get_endpoints('bangalore dispatch address')
# generate_instance(filename = get_endpoints('bangalore dispatch address'), pickup_filename = 'bangalore_pickups', pickups = True)
# generate_instance('bangalore_pickups', pickups = True,pickup_filename ='bangalore dispatch address_solution_example')


def print_geojson(filename,solution_filename="solution_example"):

    cost, routes, no_of_riders = tools.read_solution('solutions/'+solution_filename)
    temp=[]
    for ind,route in enumerate(routes):
        data = read_xlsx('clean_data_'+filename).iloc[route]
        ls = []
        for ind,_ in enumerate(data):
            ls.append((data['longitude'].iloc[ind],data['latitude'].iloc[ind]))
        temp.append(ls)
    return geojson.MultiLineString(temp)

# print(print_geojson('bangalore dispatch address'))
# print_sol('bangalore dispatch address', solution_filename='instance_time_18000_bangalore dispatch address-2023-02-08T23:33:59.919980.json')

