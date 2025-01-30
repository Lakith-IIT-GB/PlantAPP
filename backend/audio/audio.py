import os
from pydub import AudioSegment
from pydub.silence import detect_nonsilent
import noisereduce as nr
import librosa
import soundfile as sf

def convert_to_wav(input_path, output_path="processed_audio.wav"):
    """
    Converts any audio format to WAV with 16kHz sample rate and mono.
    """
    audio = AudioSegment.from_file(input_path)
    audio = audio.set_frame_rate(16000).set_channels(1)  # Convert to 16kHz mono
    audio.export(output_path, format="wav")
    return output_path

def remove_silence(audio_path, output_path="trimmed_audio.wav", silence_thresh=-40, min_silence_len=500):
    """
    Removes silence from the audio file.
    silence_thresh: Threshold (dB) below which sound is considered silence.
    min_silence_len: Minimum silence duration (ms) to be removed.
    """
    audio = AudioSegment.from_file(audio_path)
    nonsilent_ranges = detect_nonsilent(audio, min_silence_len=min_silence_len, silence_thresh=silence_thresh)

    if nonsilent_ranges:
        start_trim, end_trim = nonsilent_ranges[0][0], nonsilent_ranges[-1][1]
        trimmed_audio = audio[start_trim:end_trim]
        trimmed_audio.export(output_path, format="wav")
        return output_path
    return audio_path  # Return original if no silence detected

def convert_to_mono(audio_path, output_path="mono_audio.wav"):
    """
    Ensures the audio is in mono.
    """
    audio = AudioSegment.from_file(audio_path)
    mono_audio = audio.set_channels(1)
    mono_audio.export(output_path, format="wav")
    return output_path

def reduce_noise(audio_path, output_path="denoised_audio.wav"):
    """
    Applies noise reduction using noisereduce.
    """
    audio, sr = librosa.load(audio_path, sr=None)  # Load audio with original sample rate
    reduced_audio = nr.reduce_noise(y=audio, sr=sr)
    sf.write(output_path, reduced_audio, sr)  # Save the denoised audio
    return output_path

def preprocess_audio(input_audio):
    """
    Full pipeline to preprocess the audio.
    1. Convert to WAV (16kHz, mono)
    2. Remove silence
    3. Convert to mono (ensures single channel)
    4. Apply noise reduction
    """
    print("Converting to WAV...")
    wav_audio = convert_to_wav(input_audio)

    print("Removing silence...")
    trimmed_audio = remove_silence(wav_audio)

    print("Ensuring mono audio...")
    mono_audio = convert_to_mono(trimmed_audio)

    print("Applying noise reduction...")
    denoised_audio = reduce_noise(mono_audio)

    print(f"Preprocessing complete! Final file: {denoised_audio}")
    return denoised_audio

# Example usage
if __name__ == "__main__":
    input_audio = "sample_audio.mp3"  # Change this to your file
    final_audio = preprocess_audio(input_audio)