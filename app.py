from flask import Flask, request, jsonify
app = Flask(__name__)

users = {
  "user1": "password1",
  "user2": "password2",
  "user3": "password3"
}

@app.route('/verify')
def verify():
  data = request.get_json()
  if not data or 'username' not in data or 'password' not in data:
    return jsonify({"status": "error", "message": "Invalid data format"}), 400

  username = data['username']
  password = data['password']

  if username in users and users[username] == password:
    return jsonify({"status": "GRANTED"}), 200
  else:
    return jsonify({"status": "error", "message": "Invalid username"}), 400

if __name__ == '__main__':
    app.run(debug=True)