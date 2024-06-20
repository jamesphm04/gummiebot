from tasks import flask_app, update_price
from flask import request,jsonify 
import redis

# Configure Redis client
redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)

def get_queue_length(queue_name):
    # Get the length of the specified Celery queue
    return redis_client.llen(f'celery_{queue_name}')

@flask_app.route('/facebook_gummtree/', methods=['POST'])
def update():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    if data["isSold"] == 'False':
        price = data["price"]
        id = data["productId"]
              
        # Queue the task with Celery
        queue_name = "update_price"
        queue_length = get_queue_length(queue_name)
        print(f"Queue Length for '{queue_name}': {queue_length}")

        if queue_length >= 5:
            return jsonify({'error': 'Queue is full, try again later'}), 429
        
        update_price.apply_async(args=[id, price], queue='update_price')
    
    # Return a response immediately
    response = {
        'message': 'Updating price in the background',
        'data': data
    }
    
    return jsonify(response), 200

if __name__ == '__main__':
    flask_app.run(port=5000)

