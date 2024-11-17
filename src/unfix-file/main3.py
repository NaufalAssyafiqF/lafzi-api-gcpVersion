
import io
import re
import os
from flask import Flask, request, jsonify
from pydub import AudioSegment
from google.cloud import speech


# Initialize Flask app
app = Flask(__name__)


def transcribe_file(local_file_path):
    """Transcribe the audio file using Google Cloud Speech-to-Text API."""
    try:
        # Preprocess the audio file
        

        # Use recommended service account authentication
        client = speech.SpeechClient.from_service_account_file(
            "lafzi-key.json"  # Replace with your service account key file path
        )

        with io.open(local_file_path, "rb") as audio_file:
            content = audio_file.read()

        audio = speech.RecognitionAudio(content=content)

        hijaiyah_phrases = [
            "اليف", "با", "باء", "تا", "تاء", "ثا", "ثاء", "جا","جيم", "جاء", "حا", "حاء", "خا", "خاء", "دا", "دال", "ذا", "ذال",
            "را", "راء", "زا", "زا", "سا", "ساء","سين", "شاء", "شين", "صاء", "صاد", "ضاء", "ضاد", "طاء", "ظاء", "عاء", "عين", "غاء", "غين", "فاء", "قاء", "قاف", "شا", "صا", "ضا", "طا", "ظا", "عا",
            "غا", "فا", "قا", "كا", "كاء", "كاف", "لا", "لام", "ما", "ماء", "ميم", "نا", "ناء", "نون", "ها", "هاء", "وا", "واو", "ياء", "يا"
        ]


        speech_context = speech.SpeechContext(
            phrases=hijaiyah_phrases,
            boost=15.0  # Tingkatkan prioritas pengenalan frasa ini
        )

        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=44100,  # Updated sample rate
            audio_channel_count=2,    # Updated channel count
            language_code="ar-EG",
            speech_contexts=[speech_context],    # General Arabic
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
        return jsonify({"error": "Failed to transcribe audio. Please try again."}), 500

    except Exception:
        print(f"An error occurred")
        return jsonify({"error": "an error occurred (transcribe_file fungsction), please try again"}), 500

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
    try:
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
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "an error occurred in route, please try again"}), 500
    


if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    app.run(debug=True)