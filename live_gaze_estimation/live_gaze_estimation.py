import argparse
import sys
import os
import torch

import aria.sdk as aria

import cv2
import numpy as np
from common import quit_keypress, update_iptables

from projectaria_tools.core.sensor_data import ImageDataRecord

from inference import infer

from projectaria_tools.core import data_provider
from projectaria_tools.core.mps import EyeGaze
from projectaria_tools.core.mps.utils import get_gaze_vector_reprojection
from projectaria_tools.core.stream_id import StreamId

provider = data_provider.create_vrs_data_provider("reference_vrs/Profile_18.vrs")
device_calibration = provider.get_device_calibration()
rgb_stream_id = StreamId("214-1")
rgb_stream_label = provider.get_label_from_stream_id(rgb_stream_id)
rgb_camera_calibration = device_calibration.get_camera_calib(rgb_stream_label)
got_rgb_image = False



def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--update_iptables",
        default=False,
        action="store_true",
        help="Update iptables to enable receiving the data stream, only for Linux.",
    )
    parser.add_argument(
        "--model_checkpoint_path",
        type=str,
        default=f"{os.path.dirname(__file__)}/inference/model/pretrained_weights/social_eyes_uncertainty_v1/weights.pth",
        help="location of the model weights",
    )
    parser.add_argument(
        "--model_config_path",
        type=str,
        default=f"{os.path.dirname(__file__)}/inference/model/pretrained_weights/social_eyes_uncertainty_v1/config.yaml",
        help="location of the model config",
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cpu",
        help="device to run inference on",
    )
    return parser.parse_args()


def main():
    global got_rgb_image
    args = parse_args()
    if args.update_iptables and sys.platform.startswith("linux"):
        update_iptables()
    
    inference_model = infer.EyeGazeInference(
        args.model_checkpoint_path, args.model_config_path, args.device
    )

    aria.set_log_level(aria.Level.Info)

    # 1. Create StreamingClient instance
    streaming_client = aria.StreamingClient()

    # 2. Subscribe to RGB and EyeTrack streams
    config = streaming_client.subscription_config
    config.subscriber_data_type = (
        aria.StreamingDataType.Rgb | aria.StreamingDataType.EyeTrack
    )

    config.message_queue_size[aria.StreamingDataType.Rgb] = 1
    config.message_queue_size[aria.StreamingDataType.EyeTrack] = 1

    options = aria.StreamingSecurityOptions()
    options.use_ephemeral_certs = True
    config.security_options = options
    streaming_client.subscription_config = config

    # 3. Create and attach observer
    class StreamingClientObserver:
        def __init__(self):
            self.images = {}

        def on_image_received(self, image: np.array, record: ImageDataRecord):
            self.images[record.camera_id] = image

    observer = StreamingClientObserver()
    streaming_client.set_streaming_client_observer(observer)

    # 4. Start listening
    print("Start listening to image data")
    streaming_client.subscribe()

    # 5. Visualize the streaming data
    rgb_window = "Aria RGB"
    eye_window = "Aria EyeTrack"

    cv2.namedWindow(rgb_window, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(rgb_window, 1024, 1024)
    cv2.setWindowProperty(rgb_window, cv2.WND_PROP_TOPMOST, 1)
    cv2.moveWindow(rgb_window, 50, 50)

    cv2.namedWindow(eye_window, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(eye_window, 640, 480)
    cv2.setWindowProperty(eye_window, cv2.WND_PROP_TOPMOST, 1)
    cv2.moveWindow(eye_window, 1100, 50)

    while not quit_keypress():
         # Show RGB image (camera_id = 2)
        if aria.CameraId.Rgb in observer.images:
            rgb_image = np.rot90(observer.images[2], -1)
            rgb_image = cv2.cvtColor(rgb_image, cv2.COLOR_BGR2RGB)
            orig_h, orig_w = rgb_image.shape[:2]
            got_rgb_image = True
            del observer.images[aria.CameraId.Rgb]

        # Show EyeTrack image (camera_id = 3)
        if aria.CameraId.EyeTrack in observer.images and got_rgb_image:
            eye_image = observer.images[3]

            if eye_image.dtype != np.uint8:
                eye_image = cv2.normalize(eye_image, None, 0, 255, cv2.NORM_MINMAX)
                eye_image = eye_image.astype(np.uint8)

            if len(eye_image.shape) == 2:
                eye_image = cv2.cvtColor(eye_image, cv2.COLOR_GRAY2BGR)

            cv2.imshow(eye_window, eye_image)

            eye_image = cv2.cvtColor(eye_image, cv2.COLOR_BGR2GRAY)
            img = torch.from_numpy(eye_image).to(dtype=torch.uint8)

            preds, lower, upper = inference_model.predict(img)

            eye_gaze = EyeGaze
            eye_gaze.yaw = preds[0][0]
            eye_gaze.pitch = preds[0][1]
            print(f"Yaw: {eye_gaze.yaw}, Pitch: {eye_gaze.pitch}")

            gaze_projection = get_gaze_vector_reprojection(
                    eye_gaze,
                    rgb_stream_label,
                    device_calibration,
                    rgb_camera_calibration,
                    1,
            )

            gaze_x, gaze_y = gaze_projection
            rotated_gaze_x = orig_h - gaze_y
            rotated_gaze_y = gaze_x
            cv2.circle(rgb_image, (int(rotated_gaze_x), int(rotated_gaze_y)), 10, (0, 0, 255), -1)

            del observer.images[aria.CameraId.EyeTrack]
        
        if got_rgb_image:
            cv2.imshow(rgb_window, rgb_image)

    # 6. Cleanup
    print("Stop listening to image data")
    streaming_client.unsubscribe()


if __name__ == "__main__":
    main()