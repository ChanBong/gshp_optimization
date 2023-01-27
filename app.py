from flask import Flask
from flask import jsonify
from flask import request
import json
from models import HGS_Solver
app = Flask(__name__)

@app.route('/hgs', methods=['POST'])
def hgs():
    """
    HGS Solver:
    uses the vanilla HGS solver to solve the CVRP
    """
    data = request.get_json()
    hgs_solver = HGS_Solver(data)
    result = hgs_solver.solve_cvrp(data)
    return jsonify(
    {
        "cost": result.cost,
        "routes": result.routes
    })

@app.route('/oml', methods=['POST'])
def oml():
    data = request.get_json()
    result = HGS_Solver.solve(data)
    return jsonify(result)

# defalut landing page
@app.route('/')
def index():
    return "Welcome to the HGS API" 


if __name__ == '__main__':    
    app.run(host='0.0.0.0', port=9876)

