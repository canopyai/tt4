
import io
from flask import Flask, Response, request, jsonify
from scipy.io.wavfile import write
import numpy as np
import ljinference
import msinference
import torch
from flask_cors import CORS


def genHeader(sampleRate, bitsPerSample, channels):
    datasize = 2000 * 10**6
    o = bytes("RIFF", "ascii")
    o += (datasize + 36).to_bytes(4, "little")
    o += bytes("WAVE", "ascii")
    o += bytes("fmt ", "ascii")
    o += (16).to_bytes(4, "little")
    o += (1).to_bytes(2, "little")
    o += (channels).to_bytes(2, "little")
    o += (sampleRate).to_bytes(4, "little")
    o += (sampleRate * channels * bitsPerSample // 8).to_bytes(4, "little")
    o += (channels * bitsPerSample // 8).to_bytes(2, "little")
    o += (bitsPerSample).to_bytes(2, "little")
    o += bytes("data", "ascii")
    o += (datasize).to_bytes(4, "little")
    return o

voicelist = ['f-us-1', 'f-us-2', 'f-us-3', 'f-us-4', 'm-us-1', 'm-us-2', 'm-us-3', 'm-us-4']
voices = {}
import phonemizer
global_phonemizer = phonemizer.backend.EspeakBackend(language='en-us', preserve_punctuation=True,  with_stress=True)
print("Computing voices")
for v in voicelist:
    voices[v] = msinference.compute_style(f'voices/{v}.wav')
print("Starting Flask app")

app = Flask(__name__)
cors = CORS(app)



def synthesize(text, voice):
    v = voice.lower()
    return msinference.inference(text, voices[v], alpha=0.3, beta=0.7, diffusion_steps=10, embedding_scale=1)

@app.route("/ping", methods=['GET'])
def ping():
    return "Pong"

@app.route("/api/v1/static", methods=['POST'])
def serve_wav():
    if 'text' not in request.form or 'voice' not in request.form:
        error_response = {'error': 'Missing required fields. Please include "text" and "voice" in your request.'}
        return jsonify(error_response), 400
    text = request.form['text'].strip()
    voice = request.form['voice'].strip().lower()
    if not voice in voices:
        error_response = {'error': 'Invalid voice selected'}
        return jsonify(error_response), 400
    v = voices[voice]
    print(f"texts are {text}")
    audios = []
    synth_audio = synthesize(text, voice)
    audios.append(synth_audio)
    output_buffer = io.BytesIO()
    write(output_buffer, 24000, np.concatenate(audios))
    response = Response(output_buffer.getvalue())
    response.headers["Content-Type"] = "audio/wav"
    return response
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)