
import io
import re
import os
from flask import Flask, request, jsonify
from pydub import AudioSegment
from google.cloud import speech


# Initialize Flask app
app = Flask(__name__)

def preprocess_audio(local_file_path):
    """Convert audio to single channel and 16000 Hz if necessary."""
    try:
        # Load the audio file
        audio = AudioSegment.from_file(local_file_path)

        # Convert to mono if stereo
        if audio.channels != 1:
            print("Converting stereo to mono...")
            audio = audio.set_channels(1)

        # Convert sample rate to 16000 Hz if needed
        if audio.frame_rate != 16000:
            print("Converting sample rate to 16000 Hz...")
            audio = audio.set_frame_rate(16000)

        # Save the processed audio
        processed_path = "processed_audio.wav"
        audio.export(processed_path, format="wav")
        return processed_path

    except Exception as e:
        print(f"Error during audio preprocessing: {e}")
        return None

def transcribe_file(local_file_path):
    """Transcribe the audio file using Google Cloud Speech-to-Text API."""
    try:
        # Preprocess the audio file
        processed_path = preprocess_audio(local_file_path)
        if not processed_path:
            
            return print("Audio preprocessing failed.")

        # Use recommended service account authentication
        client = speech.SpeechClient.from_service_account_file(
            "lafzi-key.json"  # Replace with your service account key file path
        )

        with io.open(processed_path, "rb") as audio_file:
            content = audio_file.read()

        audio = speech.RecognitionAudio(content=content)


        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,  # Updated sample rate
            audio_channel_count=1,    # Updated channel count
            language_code="ar-AR",    # General Arabic
            enable_automatic_punctuation=True,  # Improve punctuation (optional)
        )

        # Perform speech recognition
        response = client.recognize(config=config, audio=audio)
        # responses = client.streaming_recognize(config=config, audio=audio)

        # Extract and return the transcript
        for result in response.results:
            return result.alternatives[0].transcript

        # Handle no transcription case
        print("No transcription received.")
        return None

    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def search_hijaiyah(transkripsi, hijaiyah):
        # Cari kata 'جيم' dalam teks, case-insensitive
        if re.search(hijaiyah, transkripsi, re.IGNORECASE):
            return True
        else:
            return False

@app.route('/', methods=['GET'])
def index():
    return jsonify({'message': 'Anda berhasil terhubung dengan API'})

@app.route('/predict', methods=['POST'])
def predict():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"})

    if 'huruf' not in request.form:
        return jsonify({"error": "No huruf part"})
    

    file = request.files['file']
    huruf = request.form['huruf']

    if (huruf == ""):
        return jsonify({"error": "No huruf part"})

    if file:
        temp_path = os.path.join("uploads", file.filename)
        file.save(temp_path)

        transcript = transcribe_file(temp_path)

        if not transcript:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return jsonify({"error": "Failed to transcribe audio. Please try again."}), 500
        
        print(f"Transcript: {transcript}")

        hasil = search_hijaiyah(transcript, huruf)

        # Hapus file sementara jika sudah selesai
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        return jsonify({ "huruf": huruf, "transcript": transcript, "hasil": hasil })



if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    app.run(debug=True)