from flask import Flask, jsonify, request, session, redirect, url_for, render_template, flash, g
from setup import *
import os, bcrypt, uuid, datetime, boto, mimetypes, requests
from boto.s3.key import Key
from bson.objectid import ObjectId
import twilio.twiml
from twilio.rest import TwilioRestClient
import speech_recognition as sr

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

@app.route('/call', methods=['POST', 'GET'])
def call_view():
  resp = twilio.twiml.Response()
  resp.say("Say a command")
  resp.record(maxLength="5", action=url_for('handle_call_view', _external=True))
  return str(resp)

@app.route('/handle_call', methods=['POST', 'GET'])
def handle_call_view():
  filename = '/tmp/{}'.format(str(uuid.uuid4()))
  recording_url = request.values.get("RecordingUrl", None)
  with open(filename, 'wb') as handle:
    response = requests.get(recording_url, stream=True)
    for block in response.iter_content(1024):
      if block:
        handle.write(block)
      else:
        break
  r = sr.Recognizer()
  with sr.WavFile(filename) as source:
    audio = r.record(source)
  resp = twilio.twiml.Response()
  try:
    command = r.recognize(audio)
    from_number = request.values.get('From', '')[2:]
    user = users.find_one({'number': from_number})
    if not from_number or not user:
      resp.say("I couldn't find {} in our database!".format(from_number))
    else:
      pending_commands.insert({'key': user['key'], 'message': command, 'datetime': datetime.datetime.utcnow()})
      resp.say("I will " + command)
  except:
    resp.say("I didn't catch that. Please try again.")
    resp.redirect(url_for('call_view', _external=True))
  return str(resp)

@app.route('/insert', methods=['POST', 'GET'])
def insert_view():
  resp = twilio.twiml.Response()
  from_number = request.values.get('From', '')[2:]
  user = users.find_one({'number': from_number})
  if not from_number or not user:
    resp.message("We couldn't find {} in our database!".format(from_number))
  else:
    pending_commands.insert({'key': user['key'], 'message': request.values.get('Body'), 'datetime': datetime.datetime.utcnow()})
  return str(resp)

@app.route('/send', methods=['POST', 'GET'])
def send_view():
  client = TwilioRestClient(account=os.getenv('TWILIO_ACCOUNT_SID'), token=os.getenv('TWILIO_AUTH_TOKEN'))
  user = users.find_one({'key': uuid.UUID(request.values.get('key'))})
  if request.values.get('media_url'):
    message = client.messages.create(to="+1"+user['number'], from_="+1"+os.getenv('TWILIO_NUMBER'), media_url=[request.values.get('media_url')])
  else:
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
  pending_commands.remove({'_id': ObjectId(object_id), 'key': uuid.UUID(request.values.get('key'))})
  return jsonify({'status': 'ok'})

@app.route('/upload', methods=['POST'])
def upload_view():
  f = request.files['file']
  conn = boto.connect_s3()
  bucket = conn.get_bucket('ym-remote-control')
  k = Key(bucket)
  k.key = str(uuid.uuid4()) + '.' + f.filename.split('.')[-1]
  k.content_type = mimetypes.guess_type(f.filename)[0]
  k.set_contents_from_file(f, headers={'Content-Type': k.content_type}, policy='public-read')
  return jsonify({'url': k.generate_url(300)})

if __name__ == '__main__':
  if os.environ.get('PORT'):
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT')), debug=os.getenv('DEV') == 'true')
  else:
    app.run(host='0.0.0.0', port=5000, debug=True)
