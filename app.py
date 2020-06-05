import os
from flask import Flask, render_template, request, redirect
from werkzeug.utils import secure_filename
import speech_recognition as sr
import simpleaudio as sa
from pydub import AudioSegment
from pydub.playback import play
from pydub.silence import split_on_silence
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import wave
import sys

app = Flask(__name__)

app.config["FILE_UPLOADS"] = "/Users/Micha/documents/github/podprod/uploads"
app.config["IMG_UPLOADS"] = "/Users/Micha/documents/github/podprod/static/img"
app.config["ALLOWED_EXTENSIONS"] = ["WAV", "M4A"]
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
			filename = secure_filename(file.filename)
			filepath = os.path.join(app.config["FILE_UPLOADS"], filename)

			# Saving the file.
			filename = secure_filename(file.filename)
			filepath = os.path.join(app.config["FILE_UPLOADS"], filename)
			file.save(filepath)
			filename_clean = filename [:-4]

			# Converting the file to wav, if it's not the case
			filename_wav = "uploads/" + filename_clean + ".wav"
			ext = filename.rsplit(".", 1)[1]
			if not ext.upper() == "WAV":
				song = AudioSegment.from_file(filepath)
				song.export(filename_wav, format="wav")

			# Delete the non Wav File
			os.remove(filepath)

			# Giving the filepath the wav filepath
			filepath = filename_wav
			
			# Create Soundwave PNG
			spf = wave.open(filepath, "r")

			# Extract Raw Audio from Wav File
			signal = spf.readframes(-1)
			signal = np.fromstring(signal, "Int16")
			fs = spf.getframerate()

			# If Stereo
			if spf.getnchannels() == 2:
				print("Just mono files")
				sys.exit(0)

			Time = np.linspace(0, len(signal) / fs, num=len(signal))
			plt.figure(figsize=(6,2.5))
			plt.style.use('seaborn')
			plt.plot(Time, signal)
			img_path = os.path.join(app.config["IMG_UPLOADS"], filename_clean)
			plt.savefig(img_path)

		return render_template('upload.html')

@app.route("/remove-silence", methods=["GET", "POST"])
def remove_silence():
	entries = []
		
	# Open a file
	path = app.config["FILE_UPLOADS"]
	
	with os.scandir(path) as dirs:
		for entry in dirs:
			entries.append(entry.name)
		

	if request.method == "POST":

		filename = request.form['filename']
		filepath = "uploads/" + filename

		sound = AudioSegment.from_file(filepath)
		chunks = split_on_silence(sound, 
		    # must be silent for at least half a second
		    min_silence_len=500,

		    # consider it silent if quieter than -50 dBFS
		    silence_thresh=-50

		)

		arr = []

		for i, chunk in enumerate(chunks):
		    chunk.export("uploads/temp/chunk{0}.wav".format(i), format="wav")
		    arr.append(i)

		print(len(arr))

		temp = AudioSegment.from_file("uploads/temp/chunk0.wav")

		for j in arr:
		    if j == 0:
		        print("Combining Chunks")
		    else: 
		        sound = AudioSegment.from_file("uploads/temp/chunk{}.wav".format(j))
		        temp = temp + sound

		temp.export(filepath, format="wav")

		for j in arr:
		    os.remove("uploads/temp/chunk{}.wav".format(j))

		print("chunks deleted")	

		# Create Soundwave PNG
		spf = wave.open(filepath, "r")

		# Extract Raw Audio from Wav File
		signal = spf.readframes(-1)
		signal = np.fromstring(signal, "Int16")
		fs = spf.getframerate()

		# If Stereo
		if spf.getnchannels() == 2:
			print("Just mono files")
			sys.exit(0)

		Time = np.linspace(0, len(signal) / fs, num=len(signal))
		plt.style.use('seaborn')
		plt.figure(figsize=(6,2.5))
		plt.plot(Time, signal)
		filename_clean = filename [:-4] + "_new"
		img_path = os.path.join(app.config["IMG_UPLOADS"], filename_clean)
		plt.savefig(img_path)	

		return render_template('remove-silence.html', entries=entries)

	else:
		return render_template('remove-silence.html', entries=entries)


@app.route("/transcribe", methods=["GET", "POST"])
def transcribe():

	text = ''

	entries = []
		
	# Open a file
	path = app.config["FILE_UPLOADS"]
	
	with os.scandir(path) as dirs:
		for entry in dirs:
			entries.append(entry.name)
		
	if request.method == "POST":

		filename = request.form['play_file']
		filepath = os.path.join(app.config["FILE_UPLOADS"], filename)

		# Speech Recognition stuff.
		recognizer = sr.Recognizer()
		audio_file = sr.AudioFile(filepath)
		with audio_file as source:
			audio_data = recognizer.record(source)
			text = recognizer.recognize_google(audio_data, key=GOOGLE_SPEECH_API_KEY, language="de-DE")

		return render_template('transcribe.html', entries=entries, text=text)

	else:
		return render_template('transcribe.html', entries=entries, text=text)
	

if __name__ == "__main__":
	app.run(debug=True)
