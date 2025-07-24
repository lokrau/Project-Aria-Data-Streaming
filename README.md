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