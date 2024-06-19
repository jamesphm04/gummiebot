from tasks import flask_app, update_price
from celery.result import AsyncResult#-Line 2
from flask import request,jsonify 

@flask_app.route('/facebook_gummtree/', methods=['POST'])
def update():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    if data["isSold"] == 'False':
        price = data["price"]
        id = data["productId"]
              
        # Queue the task with Celery
        
        update_price.apply_async(args=[id, price], queue='update_price')
    
    # Return a response immediately
    response = {
        'message': 'Updating price in the background',
        'data': data
    }
    
    return jsonify(response), 200

if __name__ == '__main__':
    flask_app.run(port=5000)

