from flask import Flask, jsonify, request, session, redirect, url_for, render_template, flash, g
from setup import *
import os, bcrypt, uuid
from bson.objectid import ObjectId
import twilio.twiml

app = Flask(__name__)
app.secret_key = os.environ.get('SK')

@app.before_request
def preprocess_request():
  g.user = users.find_one({'_id': ObjectId(session.get('userid'))})

@app.route('/')
def index_view():
  if not g.user:
    session['userid'] = None
    return redirect(url_for('login_signup_view'))
  return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login_signup_view():
  if request.method == 'POST':
    user = users.find_one({'number': request.form['number'].lower()})
    if user:
      if bcrypt.hashpw(str(request.form['password']), str(user['password'])) == str(user['password']):
        session['userid'] = str(user['_id'])
        return redirect(url_for('index_view'))
      else:
        flash('Your credentials are incorrect!', 'danger')
    else:
      key = uuid.uuid4()
      password = bcrypt.hashpw(str(request.form['password']), bcrypt.gensalt())
      userid = users.insert({'number': request.form['number'].lower(), 'password': password, 'key': key})
      session['userid'] = str(userid)
      return redirect(url_for('index_view'))
  return render_template('login_signup.html')

@app.route('/insert', methods=['POST', 'GET'])
def insert_view():
  resp = twilio.twiml.Response()
  resp.message("It workd!")
  return str(resp)

if __name__ == '__main__':
  if os.environ.get('PORT'):
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT')), debug=False)
  else:
    app.run(host='0.0.0.0', port=5000, debug=True)
