This is my final project for the CS50 2020 course. 
PodProd is an automated Podcast Post Production Software

As a user you have to first register with a username and a password to see the functions of the web-app.

When you are logged in you have different functions you can use. 

1. Overview
In the overview you can see all your uploaded files that are on the server. You will just be shown your files, which is an output of the database where each uploaded file is stored in. If you want, you can also delete the files, which will delete the file and all linked files (images, wave files, etc.)

2. Upload a file
The upload function is pretty straight forward. You can upload a file using the form. It must be a soundfile with the formats .wav, .mp3 and .m4a. The file can't be larger than 86400000 bits. After you have uploaded the file, it will be stored on the server in the /uploads folder. When a .mp3 or a .m4a file is being uploaded, they will be converted to a .wav file using pydub, so they can the used by the Google Speech-to-text API. 

3. Transcribe your uploaded files
The file transcription uses the Google Speech-to-text API. If you click on the button "transcribe" the transcribe function will be run and the output will be stored in the database to the related uploaded file. After you have uploaded the file, the page will be reloaded and as there is already a transcription within the database, the button to transcribe is disabled so the file can't be transcribed again.

4. Remove silences
This is the key part of the web-app. Removing silenced like pauses are a great tool for podcast post production to make it sound better and save time for the listener. This will give the podcast a professional sound. 
In the overview you can see your uploaded files and the related soundwaves, that are created during the upload using the matplotlib library. When you click on the button, the remove-silence function is run. The function uses the pydub library to split the soundfile in chunks whenever there is a silence part with a "silence_thresh" of -50 dbfs (line 228 in app.py) and "min_silence_len" of 500 miliseconds (line 226 in app.py). 
After the file is split in chunks, the pauses will be removed and all soundfiles will be merged again and saved as an override of the original soundfile using the same name. Afterwards all sound chunks are being deleted again. 
Lastly the new soundfile is being analysed by matplotlib again to cerate an image file of the soundwaved next to the original one. 
When the function is done, the page is being reloaded and the button will change to download, so the user can download the new file as an .wav file and can't use the "remove silence" function again. 

5. Logout
Of course you can also logout, when you don't want to use the software any more. 
