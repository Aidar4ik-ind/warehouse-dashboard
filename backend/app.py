from flask import Flask, request, jsonify, render_template
from optimizer import solve_optimization

app = Flask(__name__, static_folder='../static', template_folder='../templates')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/optimize', methods=['POST'])
def optimize():
    data = request.get_json()
    result = solve_optimization(data)
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
