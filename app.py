from tasks import flask_app, update_item, create_item, delete_item
from flask import request,jsonify 

@flask_app.route('/gummtree_bot/update', methods=['POST'])
def update():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    ids = []
    for item in data:
        ids.append(item["Id"])
        update_item.apply_async(args=[item], queue='task_queue')
    # Return a response immediately
    response = {
        'message': 'Updating in the background',
        'itemIds': ids 
    }
    
    return jsonify(response), 200

@flask_app.route('/gummtree_bot/delete', methods=['POST'])
def delete():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    ids = []
    for item in data:
        ids.append(item["Id"])
        delete_item.apply_async(args=[item], queue='task_queue')
    # Return a response immediately
    response = {
        'message': 'Deleting in the background',
        'itemIds': ids 
    }
    
    return jsonify(response), 200

@flask_app.route('/gummtree_bot/create', methods=['POST'])
def create():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    titles = []
    for item in data:
        titles.append(item["Title"])
        create_item.apply_async(args=[item], queue='task_queue')
    # Return a response immediately
    response = {
        'message': 'Creating in the background',
        'itemTitles': titles 
    }
    
    return jsonify(response), 200


if __name__ == '__main__':
    flask_app.run(port=5001)

