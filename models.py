import numpy as np 
import hygese as hgs 

class HGS_Solver():
    def __init__(self, data, timeLimit=3.2):
        self.timeLimit = timeLimit
        self.ap = hgs.AlgorithmParameters(timeLimit=self.timeLimit)
        self.hgs_solver = hgs.Solver(parameters=self.ap, verbose=True)
        self.data = data

    def solve_cvrp(self, data):
        result = self.hgs_solver.solve_cvrp(self.data)
        return result