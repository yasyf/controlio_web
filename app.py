from flask import Flask, jsonify, request, session, redirect, url_for, render_template, flash, g
from setup import *
import os, bcrypt, uuid, datetime
from bson.objectid import ObjectId
import twilio.twiml
from twilio.rest import TwilioRestClient

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
  from_number = request.values.get('From')
  user = users.find_one({'number': from_number[2:]})
  if not from_number or not user:
    resp.message("We couldn't find that number in our database!")
  else:
    pending_commands.insert({'key': user['key'], 'message': request.values.get('Body'), 'datetime': datetime.datetime.utcnow()})
  return str(resp)

@app.route('/send', methods=['POST', 'GET'])
def send_view():
  client = TwilioRestClient(account=os.getenv('TWILIO_ACCOUNT_SID'), token=os.getenv('TWILIO_AUTH_TOKEN'))
  user = users.find_one({'key': uuid.UUID(request.values.get('key'))})
  message = client.messages.create(to="+1"+user['number'], from_="+1"+os.getenv('TWILIO_NUMBER'), body=request.values.get('message'))
  return str(message)

@app.route('/poll', methods=['POST', 'GET'])
def poll_view():
  commands = list(pending_commands.find({'key': uuid.UUID(request.values.get('key'))}))
  for command in commands:
    command['_id'] = str(command['_id'])
  return jsonify({'commands': commands})

@app.route('/destroy/<object_id>', methods=['POST', 'GET'])
def destroy_view(object_id):
  response = pending_commands.remove({'_id': ObjectId(object_id), 'key': uuid.UUID(request.values.get('key'))})
  return jsonify({'response': response})

if __name__ == '__main__':
  if os.environ.get('PORT'):
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT')), debug=False)
  else:
    app.run(host='0.0.0.0', port=5000, debug=True)
