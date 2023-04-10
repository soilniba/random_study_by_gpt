import azure.cognitiveservices.speech as speechsdk
from config import *
# Creates an instance of a speech config with specified subscription key and service region.


speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
# Note: the voice setting will not overwrite the voice element in input SSML.
speech_config.speech_synthesis_voice_name = "zh-CN-sichuan-YunxiNeural"
speech_config.set_speech_synthesis_output_format(speechsdk.SpeechSynthesisOutputFormat['Audio48Khz192KBitRateMonoMp3'])

text = "你好，很高兴认识你"

# Set the output file path
output_file_path = 'output.mp3'

# Set the audio configuration to output to a file
audio_config = speechsdk.audio.AudioOutputConfig(filename=output_file_path)

# Use the speech synthesizer to synthesize the text to an audio file
speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
# speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)
result = speech_synthesizer.speak_text_async(text).get()

# Check result
if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
    print(
        f"Speech synthesized for text [{text}]. Audio output written to [{output_file_path}]"
    )
elif result.reason == speechsdk.ResultReason.Canceled:
    cancellation_details = result.cancellation_details
    print(f"Speech synthesis canceled: {cancellation_details.reason}")
    if cancellation_details.reason == speechsdk.CancellationReason.Error:
        print(f"Error details: {cancellation_details.error_details}")
