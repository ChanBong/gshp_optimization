# Find distance between two geocodes using geopy

from geopy.distance import distance
from geopy.geocoders import Nominatim
import pyproj
import numpy as np
import matplotlib.pyplot as plt

def get_duration_matrix(latitudes_longitudes):
    # get distance matrix from a list of longitudes and latitudes. Make the upper half of the matrix and copy it to the lower half to save time.
    n = len(latitudes_longitudes)
    duration_matrix = np.zeros((n, n), dtype=int)
    for i in range(n):
        for j in range(i+1, n):
            duration_matrix[i, j] = int(distance(latitudes_longitudes[i], latitudes_longitudes[j]).meters)
            duration_matrix[j, i] = duration_matrix[i, j]
    return duration_matrix

def lat_long_to_utm(latitudes_longitudes, zone=43):
    proj = pyproj.Proj(proj='utm', zone=zone, ellps='WGS84')
    utm = np.array([proj(lon, lat) for lat, lon in latitudes_longitudes], dtype=int)
    return utm

def UTM_to_lat_long(utm, zone=43):
    proj = pyproj.Proj(proj='utm', zone=zone, datum='WGS84')
    long_lat = np.array([proj(x, y, inverse=True) for x, y in utm])
    lat_long = np.array([[lat, lon] for lon, lat in long_lat])
    return lat_long

def get_lat_long_from_address(address):
    geolocator = Nominatim(user_agent="inter iit tech meet")
    location = geolocator.geocode(address)
    print(location.address)
    return location.latitude, location.longitude

def plot_map_from_lat_long(latitudes_longitudes, depot_index=0, title="Map"):
    depot = latitudes_longitudes[depot_index]
    latitudes_longitudes = np.delete(latitudes_longitudes, depot_index, axis=0)
    plt.scatter(latitudes_longitudes[:, 1], latitudes_longitudes[:, 0], label="Customers")
    plt.scatter(depot[1], depot[0], label="Depot")
    plt.title(title)
    plt.legend()
    plt.show()

def plot_solution(latitudes_longitudes, solution, depot_index=0, title="Solution"):
    # each route is a numpy array of customer indices. Add depot index in the start and end of each route.
    depot = latitudes_longitudes[depot_index]
    latitudes_longitudes = np.delete(latitudes_longitudes, depot_index, axis=0)
    plt.scatter(latitudes_longitudes[:, 1], latitudes_longitudes[:, 0], label="Customers")
    plt.scatter(depot[1], depot[0], label="Depot")
    # add depot in front of latitudes_longitudes
    latitudes_longitudes = np.insert(latitudes_longitudes, 0, depot, axis=0)
    route_number = 1
    for route in solution:
        route = np.insert(route, 0, depot_index)
        route = np.append(route, depot_index)
        print(f"Route {route_number}: {route}")
        route_lat_long = latitudes_longitudes[route]
        plt.plot(route_lat_long[:, 1], route_lat_long[:, 0], label=f"Route {route_number}")
        route_number += 1
    plt.title(title)
    plt.legend()
    plt.show()


