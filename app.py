from flask import Flask
from flask import jsonify
from flask import request
import json
from models import HGS_Solver, OML_Solver

app = Flask(__name__)

@app.route('/hgs', methods=['POST'])
def hgs():
    """
    HGS Solver:
    uses the vanilla HGS solver to solve the CVRP
    """
    data = request.get_json()
    hgs_solver = HGS_Solver(data)
    result = hgs_solver.solve_cvrp()
    return jsonify(
    {
        "cost": str(int(result.cost)),
        "routes": result.routes
    })

@app.route('/optimise/static', methods=['POST'])
def static_oml():
    """
    OML Solver:
    uses the OML solution `solver.py` to solve static VRPTW  considering only deliveries
    """
    data = request.get_json()
    oml_solver = OML_Solver(data)
    cost, routes, number_of_riders = OML_Solver.solve(oml_solver)

    cost = str(cost)
    number_of_riders = str(number_of_riders)

    return jsonify(
    {
        "cost": cost,
        "number_of_riders": number_of_riders,
        "routes": routes
    })

@app.route('/optimise/dynamic', methods=['POST'])
def dynamic_oml():
    """
    OML Solver:
    uses the OML solution `solver.py` to solve dynamic VRPTW taking in a list of pickup locations
    """
    data = request.get_json()
    oml_solver = OML_Solver(data)
    cost, routes = OML_Solver.solve(oml_solver)
    cost = str(cost[0])
    routes = [route.tolist() for route in routes[0]]
    
    # sort routes by length in descending order and if length is same then sort by first element sort by first element putting the smaller first element first
    routes = sorted(routes, key=lambda x: (-len(x), x[0]))

    return jsonify(
    {
        "cost": cost,
        "routes": routes
    })


# defalut landing page
@app.route('/')
def index():
    return "Welcome to the HGS API" 


if __name__ == '__main__':    
    app.run(host='0.0.0.0', port=9876)

