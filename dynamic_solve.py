import argparse
import random
import sys
import os
from datetime import datetime
import pandas as pd
import numpy as np
import code

from tools import read_solution, read_vrplib, write_solution
from acg import clean_data, generate_ptop_matrix, fetch_pickup_from_api

MASTER_LOCATION_FILE, MASTER_DISTANCE_FILE, MASTER_SOLUTION_FILE, PROCESSED_PICKUP_FILE = None, None, None, None

def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--pickup_instance")
    parser.add_argument("--delivery_instance")
    parser.add_argument("--delivery_vrptw_instance")
    parser.add_argument("--solution_instance")
    parser.add_argument("--pickup_folder")
    parser.add_argument("--delivery_cache", action="store_false")
    parser.add_argument("--pickup_cache", action="store_false")
    parser.add_argument("--hindsight", action="store_false")

    return parser.parse_args()

def folder_exists(folder):
    if not os.path.exists(folder):
        os.makedirs(folder)
        return False
    return True

def file_exists(file):
    if not os.path.isfile(file):
        return False
    return True


def read_master_instances(delivery_instance, delivery_vrptw_instance, solution_instance):
    """
    Read the delivery instance and solution
    """
    global MASTER_LOCATION_FILE, MASTER_DISTANCE_FILE, MASTER_SOLUTION_FILE
    MASTER_DISTANCE_FILE = f"data/inter_iit_data/master_{delivery_instance}.xlsx"
    solution_instance_name = solution_instance.split("/")[-1].split(".")[0]
    MASTER_SOLUTION_FILE = f"data/inter_iit_data/master_solution_{solution_instance_name}.json"
    MASTER_LOCATION_FILE = f"data/inter_iit_data/clean_data_master_{delivery_instance}.xlsx"

    instance = read_vrplib(delivery_vrptw_instance)
    bag_capacity = instance["capacity"]

    if not file_exists(MASTER_LOCATION_FILE):
        print(f"Creating master location file {MASTER_LOCATION_FILE}")
        delivery_data = pd.read_excel(f"data/inter_iit_data/clean_data_{delivery_instance}.xlsx")
        delivery_data.to_excel(MASTER_LOCATION_FILE)
    else:
        print(f"Reading master location file {MASTER_LOCATION_FILE}")
        delivery_data = pd.read_excel(MASTER_LOCATION_FILE, index_col=0)

    if not file_exists(f"{MASTER_DISTANCE_FILE}"):
        print(f"Creating master location file {MASTER_DISTANCE_FILE}")
        distance_matrix = instance["duration_matrix"]
        distance_matrix = pd.DataFrame(distance_matrix)
        distance_matrix.to_excel(MASTER_DISTANCE_FILE)
        # distance_matrix = distance_matrix.to_numpy()
    else:
        print(f"Reading master location file {MASTER_DISTANCE_FILE}")
        distance_matrix = pd.read_excel(MASTER_DISTANCE_FILE, index_col=0)
        # distance_matrix = distance_matrix.to_numpy()
    
    if not file_exists(MASTER_SOLUTION_FILE):
        print(f"Creating master solution file {MASTER_SOLUTION_FILE}")
        cost, solution, number_of_riders = read_solution(solution_instance)
        write_solution(MASTER_SOLUTION_FILE, cost, solution, number_of_riders)
    else:
        print(f"Reading master solution file {MASTER_SOLUTION_FILE}")
        cost, solution, number_of_riders = read_solution(MASTER_SOLUTION_FILE)
    
    return delivery_data, distance_matrix, int(cost), solution, int(number_of_riders), bag_capacity

def processed_pickup(pickup_folder, pickup_instance):
    """
    Check if the pickup instance has been processed
    """
    if not folder_exists(f"data/inter_iit_data/{pickup_folder}"):
        print(f"Creating pickup folder {pickup_folder}")

    global PROCESSED_PICKUP_FILE
    PROCESSED_PICKUP_FILE = f"data/inter_iit_data/{pickup_folder}/processed_pickups.txt"
    if not file_exists(PROCESSED_PICKUP_FILE):
        print(f"Creating processed pickup file {PROCESSED_PICKUP_FILE}")
        os.mknod(PROCESSED_PICKUP_FILE)
        return False
    else:
        print(f"Reading processed pickup file {PROCESSED_PICKUP_FILE}")
        with open(PROCESSED_PICKUP_FILE, "r") as f:
            lines = f.readlines()
            for line in lines:
                if line.strip() == pickup_instance:
                    return True

    return False

def add_matrices(A, B):
    m,k = B.shape
    n = A.shape[0]
    part1 = B.iloc[:,:n]
    part1 = part1.transpose()
    columns = [i for i in range(k)]
    A = pd.concat([A,part1],axis=1)
    A.columns = columns
    B.columns = columns
    A = pd.concat([A, B], axis=0).reset_index(drop=True)
    return A

def sync_route(routes, name_of_instance):
    '''
    this function is used to sync the routes with the database
    ''' 
    name_of_instance = (name_of_instance.split("_")[3]).split(".")[0]
    print(name_of_instance)
    cleaned_data = pd.read_excel(f"data/inter_iit_data/clean_data_master_{name_of_instance}.xlsx")
    print(cleaned_data)
    for route in routes:
        for i in range(len(route)):
            route[i] = (str(cleaned_data.iloc[int(route[i])].AWB),str(cleaned_data.iloc[int(route[i])].latitude),str(cleaned_data.iloc[int(route[i])].longitude))

    return routes


def get_demands(n):
    """
    Get the demands of each location
    """
    demands = [2 for i in range(n)]
    demands[0] = 0
    return demands

def get_route_demands(total_location, solution):
    """
    Get the demands of each route
    """
    demands = get_demands(total_location)
    route_demands = []
    for route in solution:
        print(route_demands)
        route_demand = [0]
        for location in route:
            route_demand.append(route_demand[-1] + demands[int(location)])
        route_demand.pop()
        route_demand = route_demand[::-1]
        route_demands.append(route_demand)
    
    return route_demands

def reset():
    # Delete all the master files and processed pickup files
    if os.path.exists(MASTER_SOLUTION_FILE):
        os.remove(MASTER_SOLUTION_FILE)
    if os.path.exists(MASTER_DISTANCE_FILE):
        os.remove(MASTER_DISTANCE_FILE)
    if os.path.exists(MASTER_LOCATION_FILE):
        os.remove(MASTER_LOCATION_FILE)
    # if os.path.exists(PROCESSED_PICKUP_FILE):
        # os.remove(PROCESSED_PICKUP_FILE)

def get_pickup_demands(pickup_data):
    """
    Get the demands of each pickup location
    """
    pickup_demands = [2 for i in range(pickup_data.shape[0])]
    
    return pickup_demands

def write_master_distance_matrix(distance_matrix):
    """
    Write the distance matrix to the master_distance file
    """
    distance_matrix.to_excel(MASTER_DISTANCE_FILE)

def write_processed_pickup(pickup_instance):
    """
    Write the name of the pickup instance to the processed_pickup file
    """
    with open(PROCESSED_PICKUP_FILE, "a") as f:
        f.write(f"{pickup_instance}")


def write_master_location(master_data, pickup_data):
    """
    Append the pickup data to the master data
    """
    master_data = master_data.append(pickup_data, ignore_index=True)
    master_data.to_excel(MASTER_LOCATION_FILE)
    
def update_route_demands(route_demands, min_route_index, min_index, pickup_demand):
    route_to_update = route_demands[min_route_index]
    value_to_add = route_to_update[min_index]
    change_part = route_to_update[min_index:]
    change_part = [i + pickup_demand for i in change_part]
    route_to_update = route_to_update[:min_index] + [value_to_add] + change_part
    route_demands[min_route_index] = route_to_update

    return route_demands

def run(args):
    """
    Read the initial delivery instance and solution from the master_location and master_solution file 
    As the pickups arrive in epochs, add the distance from each pickup location to the all locations in the master_location file
    For each pickup location, calculate the detour and available bag capacity for each route in the master_solution file
    Add the pickup location to the route with the minimum detour and suitable bag capacity
    Update the master_solution file
    Add the name of pickup file to the processed_pickup file
    """

    master_data, distance_matrix, current_cost, current_solution, number_of_riders, bag_capacity = read_master_instances(args.delivery_instance, args.delivery_vrptw_instance, args.solution_instance)

    total_locations = distance_matrix.shape[0]
    print(total_locations)

    # if processed_pickup(args.pickup_folder, args.pickup_instance):
    #     print(f"Pickup instance {args.pickup_instance} has already been processed")
    #     cost, solution, number_of_riders = read_solution(f"data/inter_iit_data/{args.pickup_folder}/{args.pickup_instance}_solution.txt")
    #     return cost, solution, number_of_riders

    pickup_instance = fetch_pickup_from_api(args.pickup_instance)
    pickup_instance = (pickup_instance.split('/')[2]).split('.')[0]
    print(pickup_instance)

    pickup_data = clean_data(pickup_instance, args.pickup_cache, add_hub=False)  
    print(pickup_data)

    pickup_distance_matrix = generate_ptop_matrix(args.pickup_instance, f"clean_data_master_{args.delivery_instance}", args.pickup_cache, harsh=False)
    pickup_distance_matrix = pd.DataFrame(pickup_distance_matrix)

    print(pickup_distance_matrix.shape)
    print(pickup_distance_matrix)    

    print(pickup_distance_matrix.shape, distance_matrix.shape)

    distance_matrix = add_matrices(distance_matrix, pickup_distance_matrix)
    
    # create demand for each route
    # TODO : Remove hardcoding
    # take all delivey and pickup demands as 2

    # print(pickup_data, "\n", pickup_distance_matrix, "\n", distance_matrix)
    # print("Shape of distance matrix", distance_matrix.shape[0])
    route_demands = get_route_demands(distance_matrix.shape[0], current_solution)
    pickup_demands = get_pickup_demands(pickup_data)
    # print(pickup_demands)
    unsucessful_pickup_locations = []

    # calculate detour for each pickup location for each route and pick the route with minimum detour

    for pickup_location in range(total_locations, distance_matrix.shape[0]):
        pickup_demand = pickup_demands[pickup_location-total_locations]

        for route in range(number_of_riders):
            min_detour = float("inf")
            min_index = None
            min_route_index = None
            route_demand = route_demands[route]

            for index in range(len(current_solution[route])-1):
                location1 = int(current_solution[route][index])
                location2 = int(current_solution[route][index+1])
                # code.interact(local=locals())
                # print(loca)
                # print(index, route_demand)
                if (route_demand[index] + pickup_demand) > bag_capacity:
                    continue

                detour = distance_matrix.iloc[pickup_location, location1] + distance_matrix.iloc[pickup_location, location2] - distance_matrix.iloc[location1, location2]
                if detour < min_detour:
                    min_detour = detour
                    min_index = index
                    min_route_index = route

        if min_index is None:
            print(f"Error: no route found for pickup location {pickup_location}")
            unsucessful_pickup_locations.append(pickup_location)
            continue
        # print(min_detour, min_index, min_route_index)
        # print(current_solution)
        current_solution[min_route_index].insert(min_index+1, pickup_location)
        # print("Before update")
        # print(route_demands, current_solution)
        route_demands = update_route_demands(route_demands, min_route_index, min_index, pickup_demand)
        # print(route_demands)
        current_cost += min_detour                

    print("New solution", current_solution)
    print("New cost", current_cost)

    # update all the master files
    # write_processed_pickup(args.pickup_instance)
    write_solution(MASTER_SOLUTION_FILE, int(current_cost), current_solution, number_of_riders)
    write_solution(f"data/inter_iit_data/{args.pickup_folder}/{args.pickup_instance}_solution.txt", int(current_cost), current_solution, number_of_riders)
    write_master_distance_matrix(distance_matrix)
    write_master_location(master_data, pickup_data)

    current_solution = sync_route(current_solution, name_of_instance=args.delivery_vrptw_instance)

    print("Current solution", current_solution)
    print("Current cost", current_cost)
    print("Number of riders", number_of_riders)

    return current_cost, current_solution, number_of_riders


def oml_local_search(instance_dict):
    '''
    this function is used to solve the problem using the oml endpoint
    convert a dictionary to a args namespace and then call the run function and return the costs and solution
    '''
    args = argparse.Namespace()
    args.pickup_instance = instance_dict['pickup_instance']
    args.delivery_instance = instance_dict['delivery_instance']
    args.delivery_vrptw_instance = instance_dict['delivery_vrptw_instance']
    args.solution_instance = instance_dict['solution_instance']
    args.pickup_folder = instance_dict['pickup_folder']
    args.delivery_cache = instance_dict['delivery_cache']
    args.pickup_cache = instance_dict['pickup_cache']
    args.hindsight = instance_dict['hindsight']

    print(args)

    costs, solution, number_of_riders = run(args)
    reset()
    return costs, solution, number_of_riders

def lazy_pickup():
    pass

data = {
    "pickup_instance": "bangalore_pickups",
    "delivery_instance": "bangalore dispatch address",
    "delivery_vrptw_instance": "instances/instance_time_18000_bangalore dispatch address.txt",
    "solution_instance": "sols/instance_time_18000_bangalore dispatch address-11-05-50-05.json",
    "pickup_folder": "pickup",
    "delivery_cache": True,
    "pickup_cache": False,
    "hindsight": False, 
    "method": "local_search"
}

# print(oml_local_search(data))


# def main():
#     args = parse_args()
#     print(args)
#     print("HERE")
#     run(args)

# if __name__ == "__main__":
#     main()
