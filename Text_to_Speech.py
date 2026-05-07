import azure.cognitiveservices.speech as speechsdk  
  
def synthesize_to_speaker():  
    # Replace with your own subscription key and service region  
    speech_config = speechsdk.SpeechConfig(subscription="", region="eastus")  
      
    # Set the voice name (optional, defaults to an en-US voice)  
    speech_config.speech_synthesis_voice_name = "en-US-JennyNeural"  
  
    # Use the default speaker for audio output  
    audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)  
    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)  
  
    text = "Hello! Welcome to the Azure Speech Service tutorial."  
    print(f"Synthesizing text: '{text}'")  
      
    speech_synthesis_result = speech_synthesizer.speak_text_async(text).get()  
  
    if speech_synthesis_result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:  
        print("Speech synthesized to speaker for text.")  
    elif speech_synthesis_result.reason == speechsdk.ResultReason.Canceled:  
        cancellation_details = speech_synthesis_result.cancellation_details  
        print(f"Speech synthesis canceled: {cancellation_details.reason}")  
        if cancellation_details.reason == speechsdk.CancellationReason.Error:  
            print(f"Error details: {cancellation_details.error_details}")  
  
if __name__ == "__main__":  
    synthesize_to_speaker()
