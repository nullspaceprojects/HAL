import os
import time
import urllib.request
import threading
#import psutil

# === CHAT GPT ===
# https://platform.openai.com/examples
# https://platform.openai.com/docs/guides/images/usage
import openai

# === SPEECH TO TEXT ===
import speech_recognition as sr

for index, name in enumerate(sr.Microphone.list_microphone_names()):
    print("Microphone with name \"{1}\" found for `Microphone(device_index={0})`".format(index, name))

# === TEXT TO SPEECH ===
# https://gtts.readthedocs.io/en/latest/module.html#examples
import pygame
from gtts import gTTS
from io import BytesIO

import base64
from PIL import Image

IS_RASPPI = True #False
if IS_RASPPI:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BOARD)

HAL_PIN_LED = 12 #gpio12
HAL_PIN_FREQ = 500  # Hz

if IS_RASPPI:
    MIC_DEVICE_INDEX = 2
else:
    MIC_DEVICE_INDEX = None

REC_PAUSE_TH = 0.3 # seconds of non-speaking audio before a phrase is considered complete
REC_NON_SPEAKING_DURATION = 0.2 # seconds of non-speaking audio to keep on both sides of the recording
REC_PHRASE_TH = 0.3 # minimum seconds of speaking audio before we consider the speaking audio a phrase - values below this are ignored (for filtering out clicks and pops)
REC_ENERGY_TH = 60  # minimum audio energy to consider for recording

class HALEYE:
    def __init__(self, channel, freq):
        GPIO.setup(channel, GPIO.OUT)
        self.haleye = GPIO.PWM(channel, freq)  # channel=12 frequency=50Hz
        self.haleye.start(0)  # duty cycle from 0 to 100
        self.Stop = False
        self.hal_eye_pulse = 0.3  # in sec

    def run(self, p1, p2):
        try:
            while not self.Stop:
                for dc in range(0, 101, 5):
                    self.haleye.ChangeDutyCycle(dc)
                    time.sleep(self.hal_eye_pulse)
                for dc in range(100, -1, -5):
                    self.haleye.ChangeDutyCycle(dc)
                    time.sleep(self.hal_eye_pulse)
                time.sleep(0.2)
        except Exception as ex:
            print(ex)
        self.haleye.stop()


class S2T:
    def __init__(self, mic_dev_index=None):
        self.rec = sr.Recognizer()
        self.mic = None
        if mic_dev_index is None:
            self.mic = sr.Microphone()
        else:
            self.mic = sr.Microphone(device_index=mic_dev_index)
        self.rec.pause_threshold = REC_PAUSE_TH #0.3  # seconds of non-speaking audio before a phrase is considered complete
        self.rec.non_speaking_duration = REC_NON_SPEAKING_DURATION  # seconds of non-speaking audio to keep on both sides of the recording
        self.rec.phrase_threshold = REC_PHRASE_TH  # minimum seconds of speaking audio before we consider the speaking audio a phrase - values below this are ignored (for filtering out clicks and pops)
        # print("A moment of silence, please...")
        # with self.mic as source: self.rec.adjust_for_ambient_noise(source)
        self.rec.dynamic_energy_threshold = False
        self.rec.energy_threshold = REC_ENERGY_TH  # minimum audio energy to consider for recording
        print("Set minimum energy threshold to {}".format(self.rec.energy_threshold))

    def listen(self, lookforname=True):
        while True:
            with self.mic as source:
                print("Say something!")
                audio = self.rec.listen(source)
            speech = None
            try:
                # for testing purposes, we're just using the default API key
                # to use another API key, use `r.recognize_google(audio, key="GOOGLE_SPEECH_RECOGNITION_API_KEY")`
                # instead of `r.recognize_google(audio)`
                # list of languages: https://stackoverflow.com/questions/14257598/what-are-language-codes-in-chromes-implementation-of-the-html5-speech-recogniti
                speech = self.rec.recognize_google(audio, language='it-IT')
                #print("Google Speech Recognition thinks you said " + speech)
            except sr.UnknownValueError:
                print("Google Speech Recognition could not understand audio")
            except sr.RequestError as e:
                print("Could not request results from Google Speech Recognition service; {0}".format(e))
            if lookforname:
                if speech is not None:
                    if 'Ciao al' in speech or 'Ciao hal' in speech:
                        print("Ciao, Dimmi Tutto")
                        return None
                    else:
                        print("non mi hai interpellato")
                        continue
            else:
                if speech is not None:
                    return speech


class HAL:
    def __init__(self):
        openai.api_key = "your_api_key"
        self.start_sequence = "\nAI:"
        self.start_sequence_no_newline = self.start_sequence.replace("\n", "")
        self.start_sequence_no_newline_len = len(self.start_sequence_no_newline)
        self.restart_sequence = "\nHuman:"
        self.chat_history = "Questa è una conversazione con un assistente AI. " \
                            "L'assistente è collaborativo, creativo, intelligente, e molto amichevole.\n"
        '''
        self.chat_history = "Questa è una conversazione con un assistente AI. " \
                            "L'assistente è cinico e non amichevole.\n"
        '''
        self.stop_seq = [self.restart_sequence.replace("\n", " "), self.start_sequence.replace("\n", " ")]
        print(self.stop_seq)

    def update_chat_history(self, text, is_human):
        if is_human:
            self.chat_history += self.restart_sequence + text
        else:
            self.chat_history += self.start_sequence + text
        #print(self.chat_history)

    def run_chat(self, human_text, temperature=0.8, max_tokens=1000, top_p=1):
        self.update_chat_history(text=human_text, is_human=True)
        response = None
        try:
            response = openai.Completion.create(
                model="text-davinci-003",
                prompt=self.chat_history,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                frequency_penalty=0,
                presence_penalty=0,
                stop=self.stop_seq  # stop=["\n"] # stop=[" Human:", " AI:"]
            )
        except openai.error.OpenAIError as e:
            print(e.http_status)
            print(e.error)
        if response is not None:
            print(response)
            res = response.choices[0].text
            start_index = res.find(self.start_sequence_no_newline)
            if start_index >= 0:
                res = res[start_index+self.start_sequence_no_newline_len:]  # AI: => 3 chars
            res = res.replace("AI Assistant:", "")
            self.update_chat_history(text=res, is_human=False)
            # print(res)
            return res
        else:
            return None

    def run_completion(self, prompt, temperature=0, max_tokens=100, top_p=1, stop=None):
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            frequency_penalty=0,
            presence_penalty=0,
            stop=stop  # stop=["\n"] # stop=[" Human:", " AI:"]
        )
        # print(response)
        res = response.choices[0].text
        # print(res)
        return res

    def run_generate_image(self, prompt, n=1, size="1024x1024", response_format="url"):
        try:
            response = openai.Image.create(
                prompt=prompt,
                n=n,
                size=size,
                response_format=response_format # "b64_json"
            )
            image = None
            if response_format == "url":
                image = response['data'][0]['url']
                self.url_to_png(image_url=image)
            elif response_format == "b64_json":
                image = response['data'][0]['b64_json']
                self.b64_json_to_png(b64_json_image=image)
            return image
        except Exception as ex:
            print(ex)
            return None

    def url_to_png(self, image_url):
        # Download the image from the URL
        try:
            with urllib.request.urlopen(image_url) as url:
                image_data = url.read()
            image = Image.open(BytesIO(image_data))
            image.show()
        except Exception as ex:
            print(ex)

    def b64_json_to_png(self, b64_json_image):
        try:
            #close any previous image show
            '''
            for proc in psutil.process_iter():
                print(proc.name())
                if proc.name() == "display":
                    #proc.kill()
                    pass
            '''
            # Decode the base64-encoded JSON image data
            bimage = base64.b64decode(b64_json_image)
            # Load the image binary data into a PIL Image object
            image = Image.open(BytesIO(bimage))
            image.show()
            # Save the PIL Image object as a PNG file
            #image.save("output.png", "PNG")
        except Exception as ex:
            print(ex)



class T2S:
  def __init__(self):
    pygame.init()
    pygame.mixer.init()

  def speak(self, text, lang='it'):
    try:
        tts = gTTS(text=text, lang=lang)
        fp = BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        #pygame.mixer.init()
        pygame.mixer.music.load(fp)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
    except Exception as ex:
        print(ex)

if __name__ == "__main__":

    if IS_RASPPI:
        iHALEYE = HALEYE(channel=HAL_PIN_LED, freq=HAL_PIN_FREQ)
        thHALEYE = threading.Thread(name=f"thread-HAL-EYE", target=iHALEYE.run, args=(0, 1,), daemon=True)
        thHALEYE.start()

    # speech to text
    i_s2t = S2T(mic_dev_index=MIC_DEVICE_INDEX)
    # text to speech
    i_t2s = T2S()

    # HAL core
    i_HAL = HAL()

    #i_s2t.listen(lookforname=True)
    #i_t2s.speak(text="Dimmi tutto Fratè!")

    while True:
        try:
            #hal eye slow pulse
            if IS_RASPPI:
                iHALEYE.hal_eye_pulse = 0.3

            speech = i_s2t.listen(lookforname=False)

            lowerspeech = speech.lower()
            if "disegnami" in lowerspeech or "disegna" in lowerspeech:
                lowerspeech = lowerspeech.replace("disegnami", "")
                lowerspeech = lowerspeech.replace("disegna", "")
                lowerspeech = lowerspeech.strip()
                #print(lowerspeech)
                # hal eye high pulse
                if IS_RASPPI:
                    iHALEYE.hal_eye_pulse = 0.05
                i_t2s.speak(text="aspè.., sto dipingendo")
                img = i_HAL.run_generate_image(prompt=lowerspeech, size="1024x1024", #"256x256"
                                               response_format="b64_json")
                if img is None:
                    i_t2s.speak(text="Ho fatto una cagata di disegno, non te lo faccio vedere. Chiedimi altro")
                    continue
            else:
                # hal eye high pulse
                if IS_RASPPI:
                    iHALEYE.hal_eye_pulse = 0.05

                # answer = i_HAL.run_completion(prompt=speech)
                answer = i_HAL.run_chat(human_text=speech)
                if answer is None:
                    continue
                #print(answer)
                i_t2s.speak(text=answer)
        except Exception as ex:
            print(ex)

    if IS_RASPPI:
        GPIO.cleanup()
