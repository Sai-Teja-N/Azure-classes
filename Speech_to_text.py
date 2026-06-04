import azure.cognitiveservices.speech as speechsdk  
  
def recognize_from_microphone():  
    # Replace with your own subscription key and service region  
    speech_config = speechsdk.SpeechConfig(subscription="", region="eastus")  
    speech_config.speech_recognition_language="en-US"  
  
    # Set up the audio configuration to use the default microphone  
    audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)  
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)  
  
    print("Speak into your microphone.")  
    speech_recognition_result = speech_recognizer.recognize_once_async().get()  
  
    if speech_recognition_result.reason == speechsdk.ResultReason.RecognizedSpeech:  
        print(f"Recognized: {speech_recognition_result.text}")  
    elif speech_recognition_result.reason == speechsdk.ResultReason.NoMatch:  
        print(f"No speech could be recognized: {speech_recognition_result.no_match_details}")  
    elif speech_recognition_result.reason == speechsdk.ResultReason.Canceled:  
        cancellation_details = speech_recognition_result.cancellation_details  
        print(f"Speech Recognition canceled: {cancellation_details.reason}")  
        if cancellation_details.reason == speechsdk.CancellationReason.Error:  
            print(f"Error details: {cancellation_details.error_details}")  
  
if __name__ == "__main__":  
    recognize_from_microphone()
