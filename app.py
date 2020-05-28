import os
from flask import Flask, render_template, request, redirect
from werkzeug.utils import secure_filename
import speech_recognition as sr
import simpleaudio as sa
from pydub import AudioSegment
from pydub.playback import play
from pydub.silence import split_on_silence


app = Flask(__name__)

app.config["FILE_UPLOADS"] = "/Users/Micha/documents/github/podprod/uploads"
app.config["ALLOWED_EXTENSIONS"] = ["WAV"]
app.config["MAX_FILESIZE"] = 86400000

# Function check for right file extension
def allowed_file(filename):

	# Check if file has an extension
	if not "." in filename:
		return False

	# Check if File has allowed extension
	ext = filename.rsplit(".", 1)[1]

	if ext.upper() in app.config["ALLOWED_EXTENSIONS"]:
		return True
	else:
		return False

# Function check of allowed file size
def allowed_filesize(filesize):

	if int(filesize) <= app.config["MAX_FILESIZE"]:
		return True
	else:
		return False

# Google Speech API Key
GOOGLE_SPEECH_API_KEY = None

# Flask route to homepage
@app.route("/")
def index():
	return render_template("index.html")

@app.route("/upload", methods=["GET", "POST"])
def upload():
	extra_line = ''

	if request.method == "GET":
		return render_template('upload.html')

	if request.method == "POST":

		# Check if the post request has the file part.
		if "file" not in request.files:
			flash("No file part")
			return redirect(request.url)

		file = request.files["file"]

		# If user does not select file, browser also submit an empty part without filename.
		if file.filename == "":
			flash("No selected file")
			return redirect(request.url)

		if not allowed_file(file.filename):
			print("Your file doesn't have the right format")
			return redirect(request.url)

		if file:
			# Speech Recognition stuff.
			recognizer = sr.Recognizer()
			audio_file = sr.AudioFile(file)
			with audio_file as source:
				audio_data = recognizer.record(source)
				text = recognizer.recognize_google(audio_data, key=GOOGLE_SPEECH_API_KEY, language="de-DE")
			extra_line = f'Your text: "{text}"'

			# Saving the file.
			filename = secure_filename(file.filename)
			filepath = os.path.join(app.config["FILE_UPLOADS"], filename)
			file.save(filepath)

			# Play the sound
			sound = AudioSegment.from_file(file, format="wav")
			play(sound)

		return render_template('upload.html', extra_line=extra_line)

@app.route("/split", methods=["GET", "POST"])
def split():

	entries = []
		
	# Open a file
	path = app.config["FILE_UPLOADS"]
	
	with os.scandir(path) as dirs:
		for entry in dirs:
			entries.append(entry.name)

		

	if request.method == "POST":
		split_file = request.form['split_file']
		print(split_file)

		return render_template('split.html', entries=entries)

	else:
		return render_template('split.html', entries=entries)
	


if __name__ == "__main__":
	app.run()


