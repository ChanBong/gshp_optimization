import requests
import pandas as pd

bangalore_latitude = 12.9716
bangalore_longitude = 77.5946

def read_file(filename):
    data = pd.read_excel(filename)
    return data

def get_geokeo_geocoding(address):
  
  url = 'https://geokeo.com/geocode/v1/search.php?q='+address+'g&api=f2f301246e829748673b208f2275bd49'
  resp = requests.get(url=url)
  data = resp.json()

  if 'status' in data:
      if data['status']=='ok':
          clean_address = data['results'][0]['formatted_address']
          latitude = data['results'][0]['geometry']['location']['lat']
          longitude = data['results'][0]['geometry']['location']['lng']
          return True, latitude, longitude

  return False, 0., 0.

def get_mapquest_geocoding(address):
  
  url = 'http://www.mapquestapi.com/geocoding/v1/address?key=RN9M347iPDHHeNHDVX8PM8W2yxqBucn3&location='+address

  resp = requests.get(url=url)
  data = resp.json()
  if 'info' in data:
      if 'statuscode' in data['info']:
          if data['info']['statuscode'] == 0:
              latitude = data['results'][0]['locations'][0]['latLng']['lat']
              longitude = data['results'][0]['locations'][0]['latLng']['lng'] 
              return True, latitude, longitude
  return False, 0., 0.

def clean_data(filename):

    data = read_file(filename)
    clean_data = data
    Latitude = []
    Longitude = []

    for index, address in enumerate(data['address']):

        status, latitude, longitude = get_geokeo_geocoding(address)
        if status and abs(float(latitude)-bangalore_latitude)<1. and abs(float(longitude)-bangalore_longitude)<1. :
            Latitude.append(latitude)
            Longitude.append(longitude)
            continue
        
        status, latitude, longitude = get_mapquest_geocoding(address)
        if status and abs(float(latitude)-bangalore_latitude)<1. and abs(float(longitude)-bangalore_longitude)<1. :
            Latitude.append(latitude)
            Longitude.append(longitude)
            continue

        clean_data = clean_data.drop(index=index)

    clean_data['latitude'] = Latitude
    clean_data['longitude'] = Longitude

    return clean_data


print(clean_data('data/inter_iit_data/bangalore_dispatch_address_finals.xlsx'))