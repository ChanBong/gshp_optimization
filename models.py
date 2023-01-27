import numpy as np 
import hygese as hgs 
from collections import OrderedDict
from tools import write_vrplib, read_vrplib
import json

class HGS_Solver():
    def __init__(self, data):
        self.input_data = data
        self.instance_name = data['instance_name']
        self.instance = read_vrplib(self.instance_name)
        # print(self.instance)

        hgs_data = OrderedDict()
        hgs_data['distance_matrix'] = self.instance['duration_matrix']
        hgs_data['num_vehicles'] = self.instance['vehicle_count']
        hgs_data['depot'] = 0
        hgs_data['demands'] = self.instance['demands']
        hgs_data['vehicle_capacity'] = self.instance['capacity']
        hgs_data['service_times'] = self.instance['service_times']
        
        self.data = hgs_data
        self.timeLimit = data['epoch_tlim']
        self.ap = hgs.AlgorithmParameters(timeLimit=self.timeLimit)
        self.hgs_solver = hgs.Solver(parameters=self.ap, verbose=True)

    def solve_cvrp(self, data):
        result = self.hgs_solver.solve_cvrp(self.data)
        return result