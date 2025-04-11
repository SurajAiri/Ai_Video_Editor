from deepgram import (
    DeepgramClient,
    PrerecordedOptions,
    FileSource,
)

def deepgram_transcribe(audio_path: str, model: str = "nova-3"):
    try:
        # STEP 1 Create a Deepgram client using the API key
        deepgram = DeepgramClient()

        with open(audio_path, "rb") as file:
            buffer_data = file.read()

        payload: FileSource = {
            "buffer": buffer_data,
        }

        #STEP 2: Configure Deepgram options for audio analysis
        options = PrerecordedOptions(
            model=model,
            smart_format=True,
        )

        # STEP 3: Call the transcribe_file method with the text payload and options
        response = deepgram.listen.rest.v("1").transcribe_file(payload, options)

        # STEP 4: Print the response
        # print(response.to_json(indent=4))
        return response.to_json(indent=4)
    except FileNotFoundError:
        print(f"File not found: {audio_path}")
    except Exception as e:
        print(f"Exception: {e}")