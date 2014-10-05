chmod a+x /app/.heroku/python/lib/python2.7/site-packages/speech_recognition/flac-linux-i386
if [[ "$DEV" -eq "true" ]]
then
  gunicorn -b "0.0.0.0:$PORT" app:app
else
  python app.py
fi
