from flask import Flask, request, jsonify
from flask import abort
from flask import make_response, url_for
import json
from time import gmtime, strftime
import sqlite3
import pdb
app = Flask(__name__)

dbName = 'cnp_db.db'

#List all users.
def list_users():
    conn = sqlite3.connect(dbName)
    print ("Opened database successfully");
    api_list=[]
    cursor = conn.execute("SELECT username, fullname, emailid, password, id from users")
    for row in cursor:
        a_dict = {}
        a_dict['username'] = row[0]
        a_dict['fullname'] = row[1]
        a_dict['email'] = row[2]
        a_dict['password'] = row[3]
        a_dict['id'] = row[4]
        api_list.append(a_dict)

    conn.close()
    return jsonify({'user_list': api_list})

def list_matchedUsers(matchStr):
    conn = sqlite3.connect(dbName)
    print ("Opened database successfully")
    api_list=[]
    cursor=conn.cursor()
    querystr = "%" + matchStr + "%"
    cursor.execute("select * from users where fullname like ?",(querystr,))
    data = cursor.fetchall()
    print (data)
    if len(data) == 0:
        abort(404)
    else:
        for eachUser in data:
            user = {}
            user['username'] = eachUser[0]
            user['name'] = eachUser[4]
            user['email'] = eachUser[1]
            user['password'] = eachUser[2]
            user['id'] = eachUser[3]
            api_list.append(user)

    conn.close()
    #Interesting security issue face here. See the following:
    #https://github.com/pallets/flask/issues/673
    #Can't JSONIFY an array.
    return jsonify(results=api_list)

def list_userID(user_id):
    conn = sqlite3.connect(dbName)
    print ("Opened database successfully");
    cursor=conn.cursor()
    cursor.execute("SELECT * from users where id=?",(user_id,))
    data = cursor.fetchall()

    if len(data) == 0:
        abort(404)
    else:
        #pdb.set_trace()
        user = {}
        user['username'] = data[0][0]
        user['email'] = data[0][1]
        user['password'] = data[0][2]
        user['id'] = data[0][3]
        user['fullname'] = data[0][4]

    conn.close()
    return jsonify(user)

def add_user(new_user):
    conn = sqlite3.connect(dbName)
    print ("Opened database successfully");
    cursor=conn.cursor()
    cursor.execute("SELECT * from users where username=? or email=?",(new_user['username'],new_user['email']))
    data = cursor.fetchall()
    if len(data) != 0:
        abort(409)
    else:
       cursor.execute("insert into users (username, email, password, full_name) values(?,?,?,?)",(new_user['username'],new_user['email'], new_user['password'], new_user['name']))
       conn.commit()
       return "Success"
    conn.close()
    return jsonify(new_user)


def del_user(del_user):
    conn = sqlite3.connect(dbName)
    print ("Opened database successfully");
    cursor=conn.cursor()
    cursor.execute("SELECT * from users where username=? ",(del_user,))
    data = cursor.fetchall()
    print ("Data" ,data)
    if len(data) == 0:
        abort(404)
    else:
       cursor.execute("delete from users where username==?",(del_user,))
       conn.commit()
       return "Success"

def upd_user(user):
    conn = sqlite3.connect(dbName)
    print ("Opened database successfully");
    cursor=conn.cursor()
    cursor.execute("SELECT * from users where id=? ",(user['id'],))
    data = cursor.fetchall()
    print (data)
    if len(data) == 0:
        abort(404)
    else:
        key_list=user.keys()
        for i in key_list:
            if i != "id":
                print (user, i)
                # cursor.execute("UPDATE users set {0}=? where id=? ", (i, user[i], user['id']))
                cursor.execute("""UPDATE users SET {0} = ? WHERE id = ?""".format(i), (user[i], user['id']))
                conn.commit()
    return "Success"

#Url decorators

#Retrieve information on the API version.
@app.route("/api/v1/info")
def home_index():
    conn = sqlite3.connect(dbName)
    print ("Opened database successfully");
    api_list=[]
    cursor = conn.execute("SELECT buildtime, version, methods, links from apirelease")
    for row in cursor:
        api = {}
        api['version'] = row[0]
        api['buildtime'] = row[1]
        api['methods'] = row[2]
        api['links'] = row[3]
        api_list.append(api)
    conn.close()
    return jsonify({'api_version': api_list}), 200

#Retrieve info on all users in the DB
@app.route('/api/v1/users', methods=['GET'])
def get_users():
    return list_users()

#Match a string query on user names.
@app.route('/api/v1/users/namematch/<string:matchStr>', methods=['GET'])
def get_user(matchStr):
    return list_matchedUsers(matchStr)

#Retrieve a user by user ID
@app.route('/api/v1/users/<int:user_id>', methods=['GET'])
def get_userID(user_id):
    return list_userID(user_id)

@app.route('/api/v1/users', methods=['POST'])
def create_user():
    if not request.json or not 'username' in request.json or not 'email' in request.json or not 'password' in request.json:
        abort(400)
    user = {
        'username': request.json['username'],
        'email': request.json['email'],
        'name': request.json.get('name',""),
        'password': request.json['password']
    }
    return jsonify({'status': add_user(user)}), 201

@app.route('/api/v1/users', methods=['DELETE'])
def delete_user():
    if not request.json or not 'username' in request.json:
        abort(400)
    user=request.json['username']
    return jsonify({'status': del_user(user)}), 200


@app.route('/api/v1/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    user = {}
    # if not request.json:
    #     abort(400)
    user['id']=user_id
    key_list = request.json.keys()
    for i in key_list:
        user[i] = request.json[i]
    print (user)

    return jsonify({'status': upd_user(user)}), 200

#Error handlers

@app.errorhandler(404)
def resource_not_found(error):
    return make_response(jsonify({'error 404': 'Resource not found!'}), 404)

@app.errorhandler(409)
def user_found(error):
    return make_response(jsonify({'error 409': 'Conflict! Record exist'}), 409)

@app.errorhandler(400)
def invalid_request(error):
    return make_response(jsonify({'error 400': 'Bad Request'}), 400)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

