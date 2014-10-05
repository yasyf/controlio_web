chmod a+x /app/.heroku/python/lib/python2.7/site-packages/speech_recognition/flac-linux-i386
if [ "$DEV" = "true" ]
then
  python app.py
else
  gunicorn -b "0.0.0.0:$PORT" app:app
fi
