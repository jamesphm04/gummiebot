from flask import Flask, jsonify

main_app = Flask(__name__)

@main_app.route('/main_app/gumtree/confirm_update/<int:item_id>', methods=['GET'])
def gumtree_confirm_update(item_id):
    message = f'Item {item_id} was updated please update it in the database'
    print(message)
    response = {
        'message': message
    }
    return jsonify(response), 200

@main_app.route('/main_app/gumtree/confirm_delete/<int:item_id>', methods=['GET'])
def gumtree_confirm_delete(item_id):
    message = f'Item {item_id} was deleted please update it in the database'
    print(message)
    response = {
        'message': message
    }
    return jsonify(response), 200

@main_app.route('/main_app/gumtree/confirm_create/<int:item_id>', methods=['GET'])
def gumtree_confirm_create(item_id):
    message = f'Item {item_id} was created please update it in the database'
    print(message)
    response = {
        'message': message
    }
    return jsonify(response), 200

if __name__ == '__main__':
    main_app.run(port=5000)
