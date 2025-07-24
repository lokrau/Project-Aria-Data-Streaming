# Project Aria Data Streaming
## Author: Lorenz Krause

This GitHub repository contains useful code snippets that demonstrate how different data streams from the Meta Project Aria Glasses can be accessed and processed live.

### Requirements

1. Install the Project Aria Client SDK by following the instructions in the [official documentation](https://facebookresearch.github.io/projectaria_tools/docs/ARK/sdk/setup).

2. In the project directory, install the required Python packages:
    ```bash
        pip install -r requirements.txt
    ``` 

### Currently there are two live operations available:

#### 1. Stream microphone audio and make it useable

This is contained in the folder `stream_sound`. The file `stream_sound.py` streams the microphone audio live from the glasses and saves them in `recorded_audio.wav` after the script is stopped. To use this script, run the following command in the terminal:

1. Start the data stream from the glasses in the terminal:
    1. Using a USB connection to the glasses:
        ```bash
            aria streaming start --interface usb --use-ephemeral-certs --profile profile18
        ```

    2. Using a Wi-Fi connection to the glasses (DEVICE_IP can be found in the Project Aria app):
        ```bash
            aria streaming start --interface wifi --use-ephemeral-certs --device-ip [DEVICE_IP] --profile profile18
        ```
2. After the connection is established, run the script:
    ```bash
        python -m stream_sound
    ```

3. After you are done recording, stop the script with `Ctrl+C`. The recorded audio will be saved in `recorded_audio.wav`.

#### 2. Live gaze estimation

This is contained in the folder `live_gaze_estimation`. The file `live_gaze_estimation.py` streams the eye images live from the glasses and estimates the gaze direction using a pre-trained model which is supplied by Meta for Gaze Estimation from VRS files (see [here](https://github.com/facebookresearch/projectaria_eyetracking)). The estimated gaze is directly visualized on the RGB stream from the glasses. To use this script, run the following command in the terminal:
1. Start the data stream from the glasses in the terminal:
    1. Using a USB connection to the glasses:
        ```bash
            aria streaming start --interface usb --use-ephemeral-certs --profile profile18
        ```
    
    2. Using a Wi-Fi connection to the glasses (DEVICE_IP can be found in the Project Aria app):
        ```bash
            aria streaming start --interface wifi --use-ephemeral-certs --device-ip [DEVICE_IP] --profile profile18
        ```

2. After the connection is established, run the script:
    ```bash
        python -m live_gaze_estimation
    ```

3. After you are done you can either stop the script by pressing q on the RGB stream window or by stopping the script with `Ctrl+C`.