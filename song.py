import numpy as np
import sounddevice as sd

SAMPLE_RATE = 44100

# Semitone offsets from the root for each key type
SCALES = {
    "major": [0, 2, 4, 5, 7, 9, 11],
    "natural_minor": [0, 2, 3, 5, 7, 8, 10],
    "harmonic_minor": [0, 2, 3, 5, 7, 8, 11],
}

NOTE_TO_SEMITONE = {
    "C": 0,
    "C#": 1,
    "Db": 1,
    "D": 2,
    "D#": 3,
    "Eb": 3,
    "E": 4,
    "F": 5,
    "F#": 6,
    "Gb": 6,
    "G": 7,
    "G#": 8,
    "Ab": 8,
    "A": 9,
    "A#": 10,
    "Bb": 10,
    "B": 11,
}


def note_to_midi(note):  # "C4" -> 60, "A4" -> 69
    return 12 * (int(note[-1]) + 1) + NOTE_TO_SEMITONE[note[:-1]]


def degree_to_midi(degree, root_midi, scale):
    # 0-based: degree 0 = root. Degrees past the scale wrap into higher octaves.
    octave, index = divmod(degree, len(scale))
    return root_midi + scale[index] + 12 * octave


def midi_to_freq(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


def render_note(freq, duration=0.4, amp=0.3):
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    wave = amp * np.sin(2 * np.pi * freq * t)
    fade = int(0.01 * SAMPLE_RATE)  # 10ms fades to avoid clicks
    wave[:fade] *= np.linspace(0, 1, fade)
    wave[-fade:] *= np.linspace(1, 0, fade)
    return wave


def play_sequence(degrees, key="major", root="C4", note_duration=0.4):
    scale = SCALES[key]
    root_midi = note_to_midi(root)
    audio = np.concatenate(
        [
            render_note(
                midi_to_freq(degree_to_midi(d, root_midi, scale)), note_duration
            )
            for d in degrees
        ]
    )
    sd.play(audio, SAMPLE_RATE)
    sd.wait()
