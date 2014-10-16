from setup import *
import bcrypt, uuid

def create_user(number, password):
  key = uuid.uuid4()
  password = bcrypt.hashpw(str(password), bcrypt.gensalt())
  return users.insert({'number': number, 'password': password, 'key': key})

def check_password(password, user):
  return bcrypt.hashpw(str(password), str(user['password'])) == str(user['password'])
