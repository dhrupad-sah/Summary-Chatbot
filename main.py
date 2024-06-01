import os
from typing import Union

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
import requests

import openai
from openai import OpenAI
import json

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
openai.organization = os.getenv("OPENAI_AI_ORG")
elevenlabs_key = os.getenv("ELEVENLABS_KEY")

app = FastAPI()


@app.get("/")
async def read_root():
    return {"Hello": "World"}

@app.post("/talk")
async def post_audio(file: UploadFile):
    user_message = transcribe_audio(file);
    chat_response = get_chat_response(user_message);
    audio_output = text_to_speech(chat_response);
    
    return chat_response;

def transcribe_audio(file):
    client = OpenAI()
    audio_file = open(file.filename, "rb")
    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file
    )
    print(transcript.text)
    return transcript.text

def get_chat_response(user_message):
    client = OpenAI()

    messages = load_messages()
    messages.append({"role": "user", "content": user_message})

    gpt_response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=messages
    )

    parsed_gpt_response = gpt_response.choices[0].message.content
    print(parsed_gpt_response)

    save_messages(user_message, parsed_gpt_response)
    return parsed_gpt_response


def load_messages():
    messages = []
    file = 'database.json'

    empty = os.stat(file).st_size == 0

    if not empty:
        with open(file) as db_file:
            data = json.load(db_file)
            for item in data:
                messages.append(item)

    else:
        messages.append({
            "role": "system", "content": "This is a conversation between 2 people talking in a meeting. The first line is the first person the second line is the second person, third line is again the first one and so on. Generate a summary of this conversation"
        })

    return messages

def save_messages(user_message, gpt_response):
    file = 'database.json'
    messages = load_messages()
    messages.append({"role": "user", "content": user_message})
    messages.append({"role": "assistant", "content": gpt_response})

    with open(file, 'w') as f:
        json.dump(messages, f)

def text_to_speech(text):
    client = OpenAI()

    response = client.audio.speech.create(
    model="tts-1",
    voice="nova",
    input=text
    )
    
    response.stream_to_file("result.mp3")

    
    
    
        # voice_id = '21m00Tcm4TlvDq8ikWAM'
        # body =    {
        #             "text": text,
        #             "model_id": "eleven_monolingual_v1",
        #             "voice_settings": {
        #                 "stability": 0,
        #                 "similarity_boost": 0,
        #                 "style": 0.5,
        #                 "use_speaker_boost": True
        #             }
        #           }
        
        # headers = {
        #             "Content-Type": "application/json",
        #             "accept": "audio/mpeg",
        #             "xi-api-key": elevenlabs_key
        #           }
        # url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

        # try:
        #     response = requests.post(url, json=body, headers=headers)
        #     if response.status_code==200:
        #         with open("audio_file.mp3", "wb") as file:
        #             file.write(response.content)
        #         return response.content
        #     else:
        #         return{"Something went wrong"}
            
        # except Exception as e:
        #     print(e)
  


@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile):
    return {"filename": file.filename}

