import random as rnd

import torch
import numpy as np
import soundfile as sf

from pocket_tts import TTSModel
from kokoro import KPipeline


def synth_podcast(podcast, audio_path):
    return synth_podcast_kokoro(podcast, audio_path)

def synth_podcast_kokoro(podcast, audio_path):
    print("Initializing Kokoro pipeline...")
    pipeline = KPipeline(lang_code='a')

    # Mapping speakers to Kokoro en-us voices
    # af_sarah is American Female, am_adam is American Male
    audio_segments = []
    sample_rate = 2400

    for turn in podcast.get("turns", []):
        speaker = turn.get("speaker", "Paul")
        speaker_lower = speaker.lower()
        voice_name = "af_aoede" if "anna" in speaker_lower else "am_puck"
        text = turn.get("text", "")
        if not text:
            continue

        generator = pipeline(text, voice=voice_name)
        turn_audios = []
        for _, _, audio in generator:
            if audio is not None:
                turn_audios.append(audio)

        if turn_audios:
            turn_audio = np.concatenate(turn_audios)
            audio_segments.append(turn_audio)

            # Add a 0.5s pause of silence between turns
            silence_samples = int(rnd.randrange(1, 3) * sample_rate)
            silence = np.zeros(silence_samples, dtype=turn_audio.dtype)
            audio_segments.append(silence)

    if audio_segments:
        merged_audio = np.concatenate(audio_segments)
        sf.write(audio_path, merged_audio, sample_rate)
    else:
        print("No dialogue turns found to generate audio.")

    return True


def synth_podcast_pocket_tss(podcast, audio_path):
    model = TTSModel.load_model()
    voice_states = {
        "anna": model.get_state_for_audio_prompt("anna"),
        "paul": model.get_state_for_audio_prompt("paul"),
    }

    audio_segments = []
    for turn in podcast.get("turns", []):
        speaker = turn.get("speaker", "Paul")
        speaker_lower = speaker.lower()
        voice_name = "anna" if "anna" in speaker_lower else "paul"
        voice_state = voice_states[voice_name]

        audio = model.generate_audio(voice_state, turn.get("text", ""))
        audio_segments.append(audio)
        silence_samples = int(0.5 * model.sample_rate)
        silence = torch.zeros(silence_samples, dtype=audio.dtype)
        audio_segments.append(silence)

    if audio_segments:
        merged_audio = torch.cat(audio_segments)
        sf.write(audio_path, merged_audio.numpy(), model.sample_rate)
    else:
        print("No dialogue turns found to generate audio.")

    return True


def synth_podcast(podcast, audio_path, method="kokoro"):
    if method == "pocket_tts":
        return synth_podcast_pocket_tss(podcast, audio_path)
    else:
        return synth_podcast_kokoro(podcast, audio_path)