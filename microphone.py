# Copyright 2023-2024 Deepgram SDK contributors. All Rights Reserved.
# Use of this source code is governed by a MIT license that can be found in the LICENSE file.
# SPDX-License-Identifier: MIT

from dotenv import load_dotenv
import verboselogs
from logging import Logger
from time import sleep
import os
from http import HTTPStatus
import requests
from datetime import datetime, timezone

from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    LiveTranscriptionEvents,
    LiveOptions,
    Microphone,
)
import json

load_dotenv()

def get_endpointing_value():
    while True:
        try:
            value = int(input("\nEnter endpointing value in milliseconds (e.g., 500)\nBear in mind endpointing is the time in milliseconds of silence to wait for before finalizing speech: ").strip())
            if value > 0:
                return value
            else:
                print("Please enter a positive integer.")
        except ValueError:
            print("Invalid input. Please enter a positive integer.")


def get_user_event_selection():
    events = {
        "speech_final": False,
        "is_final": False,
        "utterance_end": False,
        "interim_results": False
    }
    message = ""
    message += "Select the events you want to add messages for (y/n):"
    message += "\nInstructions:"
    message += "\n- ONLY ONE option is allowed."
    message += "\n- The options are speech_final, is_final, utterance_end, interim_results"
    print(message)
    for event, _ in events.items():
        choice = input(f"{event.replace('_', ' ').title()}: ").strip().lower()
        if choice == 'y':
            events[event] = True
            break
    return events

def create_conversation(payload):
    try:
        url = os.getenv("NIO_SBX_URL")
        token = os.getenv("SBX_TESTING_ORG_X_API_KEY")
        r = requests.post(
            f"{url}/v2/conversations",
            data =json.dumps(payload),
            headers = {
                "X-API-Key": token,
                "accept": "application/json",
                "Content-Type": "application/json",
            }
        )
        r.raise_for_status()
        return r.json()
    except requests.exceptions.HTTPError as errh:
        Logger.error("Http Error:",errh)
    except requests.exceptions.ConnectionError as errc:
        Logger.error("Error Connecting:",errc)
    except requests.exceptions.Timeout as errt:
        Logger.error("Timeout Error:",errt)
    except requests.exceptions.RequestException as err:
        Logger.error("Oops: Something Else",err)

def add_message(payload, conversation_id):
    # TODO: Complete code to pull the conversations from a third party service
    try:
        url = os.getenv("NIO_SBX_URL")
        token = os.getenv("SBX_TESTING_ORG_X_API_KEY")
        r = requests.post(
            f"{url}/v2/messagelist/{conversation_id}",
            data =json.dumps(payload),
            headers = {
                "X-API-Key": token,
                "accept": "application/json",
                "Content-Type": "application/json",
            }
        )
        r.raise_for_status()
        return r.json()
    except requests.exceptions.HTTPError as errh:
        Logger.error("Http Error:",errh)
    except requests.exceptions.ConnectionError as errc:
        Logger.error("Error Connecting:",errc)
    except requests.exceptions.Timeout as errt:
        Logger.error("Timeout Error:",errt)
    except requests.exceptions.RequestException as err:
        Logger.error("Oops: Something Else",err)

def build_conversation_payload():
    return {
        "external_id": "my-deepgram-1",
        "dealerId": os.getenv("SBX_DEEPGRAM_TOYOTA_DEALER_ID"),
        "channelType": "deepgram",
        "deviceType": "string",
        "timestamp": "2024-06-13T14:56:05.491Z",
        "category": "string",
        "shopper_first_name": "string",
        "shopper_last_name": "string",
        "vehicle_of_interest": "string",
        "agent_name": "string"
    }

def build_add_message_payload(message):
    return {
        "additionalInfo1": "string",
        "additionalInfo2": "string",
        "additionalInfo3": "string",
        "id": "dpg-msg-3",
        "content": message,
        "senderId": "string",
        "role": "customer",
        "userIP": "string",
        "feedback": "bad",
        "timestamp": "2024-06-13T15:30:31.364Z",
        "agentName": "string"
    }

def end_conversation_payload(conversation_id):
    return {
        "endOfConversation": True,
        "id": conversation_id
    }

# We will collect the is_final=true messages here so we can use them when the person finishes speaking
is_finals = []
current_speaker = None
conversation_id = None
speakers = []


def main():
    try:
        # example of setting up a client config. logging values: WARNING, VERBOSE, DEBUG, SPAM
        # config = DeepgramClientOptions(
        #     verbose=logging.DEBUG, options={"keepalive": "true"}
        # )
        # deepgram: DeepgramClient = DeepgramClient("", config)
        # otherwise, use default config
        deepgram_api_key = os.getenv("DEEPGRAM_API_KEY", "")
        deepgram = DeepgramClient(deepgram_api_key)

        dg_connection = deepgram.listen.live.v("1")
        user_events = get_user_event_selection()
        endpointing = get_endpointing_value()

        def on_open(self, open, **kwargs):
            global conversation_id
            print(f"Connection Open")
            payload = build_conversation_payload()
            response = create_conversation(payload)
            conversation_id = response["id"]
            print(f"{ conversation_id = }")

        def on_message(self, result, **kwargs):
            global is_finals
            global current_speaker
            global speakers
            sentence = result.channel.alternatives[0].transcript
            # Check if speaker exist on the current message
            if result.channel.alternatives and result.channel.alternatives[0].words:
                current_speaker = result.channel.alternatives[0].words[0].speaker
                # speakers = [word.speaker for word in result.channel.alternatives[0].words]
                
            if len(sentence) == 0:
                return
            
            if result.is_final:
                # We need to collect these and concatenate them together when we get a speech_final=true
                # See docs: https://developers.deepgram.com/docs/understand-endpointing-interim-results
                is_finals.append(sentence)
                # print(f"{sentence = }")
                # return

                # Speech Final means we have detected sufficent silence to consider this end of speech
                # Speech final is the lowest latency result as it triggers as soon an the endpointing value has triggered
                if result.speech_final:
                    utterance =  " ".join(is_finals)
                    line = f"Speaker - {current_speaker} Speech Final - {utterance}"
                    print(line)
                    # Reset Is Finals Event
                    is_finals = []
                    # Reset current_speaker
                    current_speaker = None
                    # Reset list of speakers in a sentence
                    speakers = []
                    # Adds message to conversation based on user preferences
                    if user_events["speech_final"]:
                        print("Adding message to conversation!")
                        payload = build_add_message_payload(line)
                        add_message(payload, conversation_id)
                else:
                    # These are useful if you need real time captioning and update what the Interim Results produced
                    line = f"Speaker - {current_speaker} Is Final - {sentence}"
                    print(line)
                    # Adds message to conversation based on user preferences
                    if user_events["is_final"]:
                        print("Adding message to conversation!")
                        payload = build_add_message_payload(line)
                        add_message(payload, conversation_id)
            else:
                line = f"Speaker - {current_speaker} - Interim Results - {sentence}"
                # These are useful if you need real time captioning of what is being spoken
                print(line)
                # Adds message to conversation based on user preferences
                if user_events["interim_results"]:
                    print("Adding message to conversation!")
                    payload = build_add_message_payload(line)
                    add_message(payload, conversation_id)

        def on_metadata(self, metadata, **kwargs):
            print(f"Metadata: {metadata}")
            pass

        def on_speech_started(self, speech_started, **kwargs):
            print(f"Speech Started")

        def on_utterance_end(self, utterance_end, **kwargs):
            print(f"Utterance End")
            global is_finals
            if len(is_finals) > 0:
                utterance = " ".join(is_finals)
                line = f"Utterance End: {utterance}"
                print(line)
                is_finals = []
                # Adds message to conversation based on user preferences
                if user_events["utterance_end"]:
                    print("Adding message to conversation!")
                    payload = build_add_message_payload(line)
                    add_message(payload, conversation_id)

        def on_close(self, close, **kwargs):
            global conversation_id
            print(f"Connection Closed")
            end_conversation_payload(conversation_id)
            conversation_id = None
            print("Conversation Ended!")


        def on_error(self, error, **kwargs):
            print(f"Handled Error: {error}")

        def on_unhandled(self, unhandled, **kwargs):
            print(f"Unhandled Websocket Message: {unhandled}")

        dg_connection.on(LiveTranscriptionEvents.Open, on_open)
        dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
        dg_connection.on(LiveTranscriptionEvents.Metadata, on_metadata)
        dg_connection.on(LiveTranscriptionEvents.SpeechStarted, on_speech_started)
        dg_connection.on(LiveTranscriptionEvents.UtteranceEnd, on_utterance_end)
        dg_connection.on(LiveTranscriptionEvents.Close, on_close)
        dg_connection.on(LiveTranscriptionEvents.Error, on_error)
        dg_connection.on(LiveTranscriptionEvents.Unhandled, on_unhandled)

        options: LiveOptions = LiveOptions(
            model="nova-2-automotive",
            # model="automotive",
            language="en-US",
            # Apply smart formatting to the output
            smart_format=True,
            # Raw audio format details
            encoding="linear16",
            channels=1,
            sample_rate=16000,
            # To get UtteranceEnd, the following must be set:
            interim_results=True,
            utterance_end_ms="1000",
            vad_events=True,
            # Time in milliseconds of silence to wait for before finalizing speech
            endpointing=str(endpointing),
            # Get the speaker
            diarize=True,
            #  adds punctuation and capitalization to your transcript.
            # punctuate=True,
        )

        addons = {
            # Prevent waiting for additional numbers
            "no_delay": "true"
        }

        print("\n\nPress Enter to stop recording...\n\n")
        if dg_connection.start(options, addons=addons) is False:
            print("Failed to connect to Deepgram")
            return

        # Open a microphone stream on the default input device
        microphone = Microphone(dg_connection.send)

        # start microphone
        microphone.start()

        # wait until finished
        input("")

        # Wait for the microphone to close
        microphone.finish()

        # Indicate that we've finished
        dg_connection.finish()

        print("Finished")
        # sleep(30)  # wait 30 seconds to see if there is any additional socket activity
        # print("Really done!")

    except Exception as e:
        print(f"Could not open socket: {e}")
        return


if __name__ == "__main__":
    main()