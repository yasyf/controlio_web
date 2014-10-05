chmod a+x /app/.heroku/python/lib/python2.7/site-packages/speech_recognition/flac-linux-i386
gunicorn -b "0.0.0.0:$PORT" app:app
