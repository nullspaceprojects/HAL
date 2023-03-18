#CREATE AN ACCOUNT FOR CHATGPT
https://auth0.openai.com/

#generatre API key
https://platform.openai.com/docs/quickstart/add-your-api-key

#install the pyton module
pip install --upgrade openai

#gTTS (Google Text-to-Speech)
pip install gTTS

#utils
pip install psutil

#Pillow
pip3 install Pillow
sudo apt-get install python3-pil.imagetk

#play the text
pip install pygame

#on RaspPi
sudo apt-get install alsa-utils
sudo apt-get install portaudio19-dev
sudo apt-get --no-install-recommends install jackd2 (to run the service: jackd -d alsa)
sudo apt-get install flac

#NOT NEEDED ANYMORE
sudo apt install espeak -y
pip install python-espeak

#then install
pip instal pyaudio
pip install SpeechRecognition

#on RaspPi
pip install RPi.GPIO

#on RaspPi
change all instances of Microphone() to Microphone(device_index=MICROPHONE_INDEX), 
where MICROPHONE_INDEX is the hardware-specific index of the microphone.
To figure out what the value of MICROPHONE_INDEX should be, run the following code:

import speech_recognition as sr
for index, name in enumerate(sr.Microphone.list_microphone_names()):
    print("Microphone with name \"{1}\" found for `Microphone(device_index={0})`".format(index, name))

#on RaspPi
Bug Audio on Bullseye.
change in /boot/config.txt
dtoverlay=vc4-kms-v3d
to
dtoverlay=vc4-fkms-v3d

#on RaspPi
#ALSA PCM ERRORS
You can try to clean up your ALSA configuration, for example,

ALSA lib pcm.c:2212:(snd_pcm_open_noupdate) Unknown PCM cards.pcm.rear
ALSA lib pcm.c:2212:(snd_pcm_open_noupdate) Unknown PCM cards.pcm.center_lfe
ALSA lib pcm.c:2212:(snd_pcm_open_noupdate) Unknown PCM cards.pcm.side
are caused by /usr/share/alsa/alsa.conf:

pcm.rear cards.pcm.rear
pcm.center_lfe cards.pcm.center_lfe
pcm.side cards.pcm.side
Once you comment out these lines, those error message will be gone



