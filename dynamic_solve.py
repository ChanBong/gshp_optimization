import argparse
import random
import sys
import os
from datetime import datetime
import pandas as pd
import numpy as np

from tools import read_solution, add_depot_to_solution, read_vrplib
from acg import clean_data, generate_pickup_matrix, generate_distance_matrix


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


def run(args):

    delivery_instance = read_vrplib(args.delivery_vrptw_instance)
    initial_cost, initial_solution = read_solution(args.solution_instance)
    initial_routes = add_depot_to_solution(initial_solution, depot_index=0) # TODO : Don't hardcode depot index

    if not os.path.exists(args.pickup_folder):
        os.makedirs(args.pickup_folder)
    
    if not os.path.exists(f"{args.pickup_folder}/master.xlsx"):
        distance_matrix = delivery_instance["duration_matrix"]
        master = pd.DataFrame(distance_matrix)
        master.to_excel(f"{args.pickup_folder}/master.xlsx", header=False, index=False)

    distance_matrix = pd.read_excel(f"{args.pickup_folder}/master.xlsx", header=None)

    delivery_demands = delivery_instance["demands"]
    bag_capacity = delivery_instance["capacity"]
    total_delivery_locations = len(distance_matrix)

    print(delivery_demands)
    print("Total delivery locations", total_delivery_locations)

    pickup_data = clean_data(args.pickup_instance, args.pickup_cache)
    pickup_distance_matrix = generate_pickup_matrix(args.pickup_instance, args.delivery_instance, args.pickup_cache)
    pickup_distance_matrix  = pd.DataFrame(pickup_distance_matrix)
    pickup_data["demands"] = [2 for i in range(len(pickup_data))]

    # assign each pickup location an index from total_delivery_locations to total_delivery_locations + len(pickup_data), make pickup location index a dictionary
    pickup_location_index = {}
    for i in range(len(pickup_data)):
        pickup_location_index[i] = i+total_delivery_locations

    distance_matrix = add_matrices(distance_matrix, pickup_distance_matrix)
    print(distance_matrix)

    # write the distance matrix to the master excel file
    # distance_matrix.to_excel(f"{args.pickup_folder}/master.xlsx", header=False, index=False)

    unsucessful_pickup_locations = []

    delivery_demands_prefix = []
    for route in initial_routes:
        route_demand = [0]*(len(route)+1)
        for location in range(2, len(route)+1):
            route_demand[location] = route_demand[location-1] + delivery_demands[location-1]
        if route_demand[-1] > bag_capacity:
            print("Error: route demand exceeds bag capacity")
            sys.exit(1)
        print(route_demand)

    print(delivery_demands_prefix)
    print("Total rotes", len(initial_routes))
    for pickup_location in range(len(pickup_data)):
        print(pickup_location)
        pickup_location_idx = pickup_location_index[pickup_location]
        # print("HERE", pickup_data.iloc[pickup_location])
        min_detour = float("inf")
        min_route = None
        min_index = None
        min_route_index = None
        for route_index in range(len(initial_routes)):
            route = initial_routes[route_index]
            # for each adjacent location in the route, calculate the distance if the pickup location is added between them, use distance matrix
            for i in range(len(route)-1):
                # if the demand exceeds the bag capacity, skip this route
                if (delivery_demands_prefix[route_index][i] + pickup_data.iloc[pickup_location]["demands"] > bag_capacity):
                    continue
                detour = distance_matrix.iloc[route[i]][pickup_location_idx] + distance_matrix.iloc[pickup_location_idx][route[i+1]] - distance_matrix.iloc[route[i]][route[i+1]]
                print("detour:", detour, 
                      "route[i]:", route[i],
                        "pickup_location_idx:", pickup_location_idx,
                        "route[i+1]:", route[i+1],
                        "distance_matrix.iloc[route[i]][pickup_location_idx]:", distance_matrix.iloc[route[i]][pickup_location_idx],
                        "distance_matrix.iloc[pickup_location_idx][route[i+1]]:", distance_matrix.iloc[pickup_location_idx][route[i+1]],
                        "distance_matrix.iloc[route[i]][route[i+1]]:", distance_matrix.iloc[route[i]][route[i+1]],
                        "min_detour:", min_detour)
                if detour < min_detour:
                    min_detour = detour
                    min_route = route
                    min_route_index = route_index
                    min_index = i
        print(min_detour, min_route, min_index, min_route_index)
        if (min_detour == float("inf") or min_route == None or min_index == None or min_route_index == None):
            print(f"Error: no route found for pickup location {pickup_location}")
            unsucessful_pickup_locations.append(pickup_location)
            continue
        # add the pickup location to the route
        min_route.insert(min_index+1, pickup_location_idx)
        # update the demand prefix array
        print(delivery_demands)
        print(delivery_demands_prefix)
        for i in range(min_index+1, len(min_route)):
            temp = pickup_data.iloc[pickup_location]["demands"]
            try:
                delivery_demands_prefix[min_route_index][i] += temp
            except:
                print(i,delivery_demands_prefix[min_route_index])
                exit(0)
        # update the initial cost
        initial_cost += min_detour

    with open(f"solutions/{args.pickup_instance}-{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt", "w") as f:
        f.write(f"Costs: {initial_cost}\n")
        f.write(f"Solution: {initial_routes}\n")
    print(f"Costs: {initial_cost}\n")
    print(f"Solution: {initial_routes}\n")
    
    return initial_cost, initial_routes     


# def generate_dynamic_instance(distance_matrix, filename, use_cache=False):
#     # distance_matrix = generate_distance_matrix(filename,use_cache)

#     instance_file = open("instances/instance_"+filename+".txt", "w")

#     instance_file.write(f"NAME : {filename.upper()}\n")
#     instance_file.write(f"COMMENT : INTER_IIT\n")
#     instance_file.write(f"TYPE : CVRP\n")
#     instance_file.write(f"DIMENSION : {distance_matrix.shape[0]}\n")
#     instance_file.write(f"VEHICLES : {read_num_vehicles()}\n")
#     instance_file.write(f"EDGE_WEIGHT_TYPE : EXPLICIT\n")
#     instance_file.write(f"EDGE_WEIGHT_FORMAT : FULL_MATRIX\n")
#     instance_file.write(f"CAPACITY : {read_vehicle_capacity()}\n")

#     instance_file.write(f"EDGE_WEIGHT_SECTION\n")
#     for row in distance_matrix:
#         for item in row:
#             instance_file.write(f"{item.astype(int)} ")
#         instance_file.write(f"\n")

#     instance_file.write(f"NODE_COORD_SECTION\n")
#     for index, coordinates in enumerate(get_coordinates()):
#         instance_file.write(f"{index+1} {(coordinates[0]*10000).astype(int)} {(coordinates[1]*10000).astype(int)}\n")

#     instance_file.write(f"DEMAND_SECTION\n")
#     for index, demand in enumerate(get_demands()):
#         instance_file.write(f"{index+1} {demand}\n")
    
#     instance_file.write(f"DEPOT_SECTION\n{read_depot_index()+1}\n-1\n")
#     instance_file.write(f"SERVICE_TIME_SECTION\n")
#     for index in range(distance_matrix.shape[0]):
#         instance_file.write(f"{index+1} 0\n")
#     instance_file.write(f"TIME_WINDOW_SECTION\n")
#     for index in range(distance_matrix.shape[0]):
#         instance_file.write(f"{index+1} 0 100000\n")
#     instance_file.write(f"EOF\n")
    
#     instance_file.close()


# def lazy_solve(args):

#     # combine all the xlxs in pickup folder to one xlsx
#     # creat a file to store all the pickup locations
#     all_pickup_locations = []
#     for file in os.listdir(args.pickup_folder):
#         if file.endswith(".xlsx"):
#             pickup_locations = clean_data(file, args.pickup_cache)
#             all_pickup_locations.append(pickup_locations)
#     with open(f"{args.pickup_folder}/all_pickup_locations.txt", "w") as f:
#         f.write(all_pickup_locations)

#     # pickup matrix is m*m matrix, m is the number of pcikup locations
#     pickup_matrix = generate_distance_matrix(args.pickup_instance, args.pickup_cache)
#     pickup_distance_matrix = generate_pickup_matrix(args.pickup_instance, args.pickup_cache)
#     delivery_distance_matrix = generate_distance_matrix(args.delivery_instance, args.delivery_cache)
#     clean_data = clean_data(args.pickup_instance, args.pickup_cache)
#     initial_cost, initial_solution = read_solution(args.solution_instance)
    
#     # find the end delivery locations. append depot at the beginning of end delivery locations
#     end_delivery_locations = [args.depot]
#     for route in initial_solution:
#         end_delivery_locations.append(route[-1])

#     # slice the delivery distance matrix to get another matrix, which is the distance from end delivery locations to end delivery locations
#     end_delivery_distance_matrix = []
#     for i in range(len(end_delivery_locations)):
#         row = []
#         for j in range(len(end_delivery_locations)):
#             row.append(delivery_distance_matrix[end_delivery_locations[i]][end_delivery_locations[j]])
#         end_delivery_distance_matrix.append(row)
    
#     # for each row in end delivery distance matrix, append the distance from end delivery location to all pickup locations
#     for i in range(len(end_delivery_distance_matrix)):
#         for j in range(len(clean_data)):
#             end_delivery_distance_matrix[i].append(pickup_distance_matrix[j][end_delivery_locations[i]])
    
#     # add more rows to the end delivery distance matrix, each row is the distance from a pickup location to all end delivery locations and then to other pickup locations
#     for i in range(len(clean_data)):
#         row = []
#         for j in range(len(end_delivery_locations)):
#             row.append(pickup_distance_matrix[i][end_delivery_locations[j]])
#         for j in range(len(clean_data)):
#             row.append(pickup_matrix[i][j])
#         end_delivery_distance_matrix.append(row)
    
#     # creat a latitudes and longitudes list for all the locations


def oml_dynamic_solver(instance_dict):
    '''
    this function is used to solve the problem using the oml endpoint
    convert a dictionary to a args namespace and then call the run function and return the costs and solution
    '''
    args = argparse.Namespace()
    args.instance = instance_dict['instance_name']
    args.instance_seed = instance_dict['instance_seed']
    args.solver_seed = instance_dict['solver_seed']
    args.epoch_tlim = instance_dict['epoch_tlim']
    args.config_loc = instance_dict['config_loc']
    args.profile = instance_dict['profile']
    args.static = instance_dict['static']
    args.hindsight = instance_dict['hindsight']

    costs, solution = run(args)
    return costs, solution

def main():
    args = parse_args()
    print(args)
    print("HERE")
    run(args)

if __name__ == "__main__":
    main()
