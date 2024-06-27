from tasks import flask_app, update_item
from flask import request,jsonify 

@flask_app.route('/facebook_gummtree/', methods=['POST'])
def update():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    ids = []
    for item in data:
        ids.append(item["Id"])
        update_item.apply_async(args=[item], queue='update_item')
    # Return a response immediately
    response = {
        'message': 'Updating in the background',
        'itemIds': ids 
    }
    
    return jsonify(response), 200

if __name__ == '__main__':
    flask_app.run(port=5000)

