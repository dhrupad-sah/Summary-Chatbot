import os
from typing import Union

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
import requests
from fastapi.responses import FileResponse
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
    file_location = f"temp/{file.filename}"
    with open(file_location, "wb") as buffer:
        buffer.write(await file.read())
    user_message = transcribe_audio(file_location);
    chat_response = get_chat_response(user_message);
    audio_output = text_to_speech(chat_response);

    response = FileResponse(audio_output, media_type='audio/mpeg', filename='response.mp3')

    os.remove(file_location)

    def clean_up():
        os.remove(audio_output)
        
    with open('database.json', 'w') as file:
        file.truncate(0)
    
    return response

@app.post("/text")
async def post_audio(file: UploadFile):
    file_location = f"temp/{file.filename}"
    with open(file_location, "wb") as buffer:
        buffer.write(await file.read())
    user_message = transcribe_audio(file_location);
    chat_response = get_chat_response(user_message);
        
    with open('database.json', 'w') as file:
        file.truncate(0)
    
    return chat_response

def transcribe_audio(file_path):
    client = OpenAI()
    with open(file_path, "rb") as audio_file: 
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
            "role": "system", "content": "This is a conversation among people talking in a meeting. The first line is the first person the second line is the second person, third line is again the first one and so on. Give me a detailed summary of the conversation."
        })

    return messages

def save_messages(user_message, gpt_response):
    file = 'database.json'
    messages = load_messages()
    messages.append({"role": "user", "content": user_message})
    messages.append({"role": "assistant", "content": gpt_response})

    with open(file, 'w') as f:
        json.dump(messages, f)

def text_to_speech(text, output_path="result.mp3"):
    client = OpenAI()
    response = client.audio.speech.create(
    model="tts-1",
    voice="nova",
    input=text
    )
    response.stream_to_file(output_path)
    return output_path

@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile):
    return {"filename": file.filename}

