import argparse
import sys
import threading

import aria.sdk as aria
import numpy as np
import soundfile as sf

from common import quit_keypress, update_iptables

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--update_iptables",
        default=False,
        action="store_true",
        help="Update iptables to enable receiving the data stream, only for Linux.",
    )
    return parser.parse_args()

def max_signed_value_for_bytes(n):
    return (1 << (8 * n - 1)) - 1

def main():
    args = parse_args()
    if args.update_iptables and sys.platform.startswith("linux"):
        update_iptables()

    aria.set_log_level(aria.Level.Info)

    streaming_client = aria.StreamingClient()

    config = streaming_client.subscription_config
    config.subscriber_data_type = aria.StreamingDataType.Audio
    config.message_queue_size[aria.StreamingDataType.Audio] = 10

    options = aria.StreamingSecurityOptions()
    options.use_ephemeral_certs = True
    config.security_options = options
    streaming_client.subscription_config = config

    # Observer class to receive and store audio
    class StreamingClientObserver:
        def __init__(self):
            self.recording_buffer = []
            self.audio_lock = threading.Lock()
            self.audio_max_value_ = max_signed_value_for_bytes(4)
            self.timestamp_ns = None

        def on_audio_received(self, audio_data, timestamp_ns):
            self.timestamp_ns = timestamp_ns.capture_timestamps_ns
            timestamps_s = [ts / 1e9 for ts in self.timestamp_ns]

            audio_np = np.array(audio_data.data).astype(np.float64) / self.audio_max_value_

            # Reshape the audio to (256, 7) where 7 = number of channels
            try:
                audio_np = audio_np.reshape((-1, 7))  # Result: shape (256, 7)
            except ValueError as e:
                print(f"Error reshaping audio: {e}")
                return

            with self.audio_lock:
                self.recording_buffer.append(audio_np)
                print(f"Received chunk: shape={audio_np.shape}, mean={np.mean(audio_np):.4f}")
                print(f"Appended audio to buffer, new buffer size: {len(self.recording_buffer)}")


    observer = StreamingClientObserver()
    streaming_client.set_streaming_client_observer(observer)

    print("Start listening to audio data")
    streaming_client.subscribe()

    import time
    try:
        while not quit_keypress():
            time.sleep(1)
    finally:
        print("Stop listening to data")
        streaming_client.unsubscribe()

        # Save to WAV
        with observer.audio_lock:
            if observer.recording_buffer:
                all_audio = np.vstack(observer.recording_buffer)  # shape: (N_samples, 7)
                sf.write("recorded_audio.wav", all_audio, samplerate=48000)
                print("Saved recorded audio to recorded_audio.wav")
            else:
                print("No audio data recorded.")


if __name__ == "__main__":
    main()
