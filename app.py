import os
from flask import Flask, render_template, request, redirect
from werkzeug.utils import secure_filename
import speech_recognition as sr
import simpleaudio as sa

app = Flask(__name__)

app.config["FILE_UPLOADS"] = "/Users/Micha/documents/github/podprod/uploads"
app.config["ALLOWED_EXTENSIONS"] = ["WAV"]
app.config["MAX_FILESIZE"] = 86400000

def allowed_file(filename):

	if not "." in filename:
		return False

	ext = filename.rsplit(".", 1)[1]

	if ext.upper() in app.config["ALLOWED_EXTENSIONS"]:
		return True
	else:
		return False

def allowed_filesize(filesize):

	if int(filesize) <= app.config["MAX_FILESIZE"]:
		return True
	else:
		return False

GOOGLE_SPEECH_API_KEY = None

@app.route("/")
def index():
	return render_template("index.html")


@app.route("/upload2", methods=["GET", "POST"])
def upload_file():

	if request.method == "GET":
		return render_template('upload.html')

	if request.method == "POST":

		if request.files:

			if not allowed_filesize(request.cookies.get("filesize")):
				print("File exceeded maximum size")
				return redirect(request.url)

			file = request.files["file"]

			if file.filename == "":
				print("File must have a filename")
				return redirect(request.url)

			if not allowed_file(file.filename):
				print("Your file doesn't have the right format")
				return redirect(request.url)

			else:
				filename = secure_filename(file.filename)
				file.save(os.path.join(app.config["FILE_UPLOADS"], filename))

				# Speech Recognition stuff.
				recognizer = sr.Recognizer()
				audio_file = sr.AudioFile(file)
				with audio_file as source:
					audio_data = recognizer.record(source)
				text = recognizer.recognize_google(audio_data, key=GOOGLE_SPEECH_API_KEY, language="en-EN")
				print(text)

			print("file saved")

			return redirect(request.url)

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

		return render_template('upload.html', extra_line=extra_line)

if __name__ == "__main__":
	app.run()


