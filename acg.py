import requests, re
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
time_windows = []

def read_xlsx(filename):
    data = pd.read_excel('data/inter_iit_data/'+filename+'.xlsx')
    return data

def read_num_vehicles():
    return int(len(addresses)/20) # chosen arbitrarily

def read_vehicle_capacity():
    return 25 # chosen arbitrarily

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
        demands.append(1) # chosen arbitrarily
    demands[0] = 0
    return demands

def get_distmat_geocoding(address):
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
    address = address.replace("st","")
    address = address.replace("nd","")
    address = address.replace("th","")
    address = address.replace("floor","")
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

def clean_data(filename, use_cache=False, add_hub = True):

    if use_cache:
        clean_data = read_xlsx('clean_data_'+filename)
        return clean_data

    data = read_xlsx(filename)
    if add_hub :
        hub = pd.DataFrame({'address':'1075-I, 5th Cross Rd, North, Appareddipalya, Indiranagar, Bengaluru, Karnataka 560008', 'AWB':'00000000000', 'names':'GrowSimplee', 'product_id':'0', 'EDD':'13-02-2023'}, index=[0])
        data = pd.concat([hub,data.loc[:]]).reset_index(drop=True)
    clean_data = data
    Latitude = []
    Longitude = []

    for index, address in enumerate(data['address']):
        print(index)
        status, latitude, longitude = get_distmat_geocoding(address)
        if status and (abs(float(latitude)-bangalore_latitude)<1.) and (abs(float(longitude)-bangalore_longitude)<1.) :
            Latitude.append(latitude)
            Longitude.append(longitude)
            continue
        
        original_address = address
        address = clean_address(address)
        status, latitude, longitude = get_distmat_geocoding(address)
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

    new_file = pd.ExcelWriter('data/inter_iit_data/clean_data_'+filename+'.xlsx')
    clean_data.to_excel(new_file)
    new_file.save()

    return clean_data

def reset():
    ids=[]
    addresses = []
    latitudes = []
    longitudes = []
    demand_ids = []
    time_windows = []

def read_coordinates(clean_data):

    for ind in clean_data.index:
        ids.append(str(len(ids)))
        addresses.append(clean_data['address'][ind])
        longitudes.append(clean_data['longitude'][ind])
        latitudes.append(clean_data['latitude'][ind])
        demand_ids.append(clean_data['product_id'][ind])
        time_windows.append(int(clean_data['EDD'][ind].split('-')[0]))
    
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

def generate_instance(filename, use_cache=False, edge_weight = "time", one_day_time = 45000, pickups = False):

    if pickups == True :
        matrix = generate_pickup_matrix(filename,use_cache)
    else :
        matrix = generate_matrix(filename,use_cache)

    instance_file = open("instances/instance_"+edge_weight+"_"+str(one_day_time)+"_"+filename+".txt", "w")

    instance_file.write(f"NAME : {filename.upper()}\n")
    instance_file.write(f"COMMENT : INTER_IIT\n")
    instance_file.write(f"TYPE : CVRP\n")
    instance_file.write(f"DIMENSION : {matrix.shape[0]}\n")
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
    for index, demand in enumerate(get_demands()):
        instance_file.write(f"{index+1} {demand}\n")
    
    instance_file.write(f"DEPOT_SECTION\n{read_depot_index()+1}\n-1\n")
    instance_file.write(f"SERVICE_TIME_SECTION\n")
    for index in range(matrix.shape[0]):
        instance_file.write(f"{index+1} 0\n")
    instance_file.write(f"TIME_WINDOWS_SECTION\n")
    for index in range(matrix.shape[0]):
        instance_file.write(f"{index+1} 0 {(time_windows[index]+1)*one_day_time}\n")
    instance_file.write(f"EOF\n")
    
    instance_file.close()



generate_instance('bangalore dispatch address', use_cache = True)


