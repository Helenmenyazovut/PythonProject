import pyaudio
import numpy as np
import threading

class AudioAnalyzer:
    def __init__(self):
        self.CHUNK = 4096
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 44100
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.running = False
        self.thread = None
        self.current_frequency = 0.0
        self.lock = threading.Lock()

        self.standard_tuning = {
            1: 82.41,
            2: 110.00,
            3: 146.83,
            4: 196.00,
            5: 246.94,
            6: 329.63,
        }

        self.note_names = {
            1: "E2",
            2: "A2",
            3: "D3",
            4: "G3",
            5: "B3",
            6: "E4",
        }

    def start(self):
        if self.running:
            return
        self.stream = self.p.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK
        )
        self.running = True
        self.thread = threading.Thread(target=self._read_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None

    def _read_loop(self):
        freq_buffer = []
        while self.running:
            try:
                data = self.stream.read(self.CHUNK, exception_on_overflow=False)
                audio_data = np.frombuffer(data, dtype=np.int16)
                if np.max(np.abs(audio_data)) < 300:
                    with self.lock:
                        self.current_frequency = 0.0
                        freq_buffer = []
                    continue
                windowed = audio_data * np.hanning(len(audio_data))
                fft = np.fft.fft(windowed)
                freqs = np.fft.fftfreq(len(fft), 1.0 / self.RATE)
                half = len(fft) // 2
                magnitudes = np.abs(fft[:half])
                freqs = freqs[:half]
                min_freq = 70
                max_freq = 400
                mask = (freqs >= min_freq) & (freqs <= max_freq)
                if not np.any(mask):
                    continue
                filtered_magnitudes = magnitudes[mask]
                filtered_freqs = freqs[mask]
                peak_index = np.argmax(filtered_magnitudes)
                peak_freq = filtered_freqs[peak_index]
                freq_buffer.append(peak_freq)
                if len(freq_buffer) > 10:
                    freq_buffer.pop(0)
                
                if len(freq_buffer) >= 5:
                    avg_freq = sum(freq_buffer) / len(freq_buffer)
                    with self.lock:
                        self.current_frequency = avg_freq
                    
            except Exception:
                with self.lock:
                    self.current_frequency = 0.0
                    freq_buffer = []

    def get_frequency(self):
        with self.lock:
            return self.current_frequency

    def find_closest_string(self, freq):
        if freq <= 0:
            return None, None, 0.0
        
        best_string = None
        best_diff = float('inf')
        
        for string_num, standard_freq in self.standard_tuning.items():
            diff = abs(freq - standard_freq)
            if diff < best_diff:
                best_diff = diff
                best_string = string_num
        
        if best_string is None:
            return None, None, 0.0
        
        standard_freq = self.standard_tuning[best_string]
        deviation = (freq - standard_freq) / (standard_freq * 0.05)
        deviation = max(-1.0, min(1.0, deviation))

        if abs(deviation) < 0.02:
            deviation = 0.0
        return best_string, self.note_names[best_string], deviation