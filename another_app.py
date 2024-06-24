from flask import Flask, request, jsonify
import sys

another_app = Flask(__name__)



@another_app.route('/successful/', methods=['GET'])
def update():
    data = request.get_json()
    print(data)
    response = {'message': 'OK, Goodjob!'}
    return jsonify(response), 200

if __name__ == '__main__':
    another_app.run(port=6000)

