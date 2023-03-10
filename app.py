from flask import Flask
from flask import jsonify
from flask import request
from flask_cors import CORS
import json
from models import HGS_Solver, OML_Solver, Dynamic_Solver
import acg

app = Flask(__name__)
CORS(app)
@app.route('/coordinates', methods=['POST'])
def get_geocoding_api():
    data = request.get_json()
    address = data['address']
    acg.read_cache()
    return acg.get_geocoding(address)


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
    cost = cost/100
    cost = str(cost)
    number_of_riders = str(number_of_riders)
    on_time_deliveries = str(acg.get_on_time_delivery(data['instance_name']))
    return jsonify(
    {
        "cost": cost,
        "number_of_riders": number_of_riders,
        "routes": routes,
        "on_time_deliveries": on_time_deliveries
    })

@app.route('/optimise/dynamic', methods=['POST'])
def dynamic_oml():
    """
    OML Solver:
    uses the OML solution `solver.py` to solve dynamic VRPTW taking in a list of pickup locations
    """
    data = request.get_json()
    dynamic_solver = Dynamic_Solver(data)
    if (data['method'] == 'local_search'):
        cost, routes, number_of_riders = Dynamic_Solver.local_search_solve(dynamic_solver)
    else:
        # use lazy solveer
        pass

    cost = cost/100
    cost = str(cost)
    number_of_riders = str(number_of_riders)
    on_time_deliveries = str(100.0)

    return jsonify(
    {
        "cost": cost,
        "number_of_riders": number_of_riders,
        "routes": routes, 
        "on_time_deliveries": on_time_deliveries
    })


# defalut landing page
@app.route('/')
def index():
    return "Welcome to the HGS API" 


if __name__ == '__main__':    
    app.run(host='0.0.0.0', port=9876)

