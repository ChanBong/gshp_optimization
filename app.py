from flask import Flask
from flask import jsonify
from models import HGS_Solver
app = Flask(__name__)

# import data from data/toy_data.json
import json
with open('data/toy_data.json') as json_file:
    data = json.load(json_file)


@app.route('/')
def algorithm():

    # Solver initialization
    hgs_solver = HGS_Solver(data, timeLimit=3.2)

    # Solve
    result = hgs_solver.solve_cvrp(data)
    print(result.cost)
    print(result.routes)

    return jsonify(
    {
        "cost": result.cost,
        "routes": result.routes
    })

app.run(host='0.0.0.0', port=9876)