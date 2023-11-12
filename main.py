#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# title: tts_openai
# date: "2023-11-09"
# author: Hsieh-Ting Lin, the Lizard 🦎
# import os
import os
import subprocess
import sys
import threading
import time
from datetime import datetime

import tiktoken
from openai import OpenAI


def start_animation(stop_flag):
    braille_chars = ["⡿", "⣟", "⣯", "⣷", "⣾", "⣽", "⣻", "⢿"]
    i = 0
    while not stop_flag.is_set():
        print(braille_chars[i % len(braille_chars)], end="\r")
        i += 1
        time.sleep(0.1)

    print("Done 🌈")


def green_text(text):
    return f"\033[92m{text}\033[0m"


def read_text_file(file_path):
    # Read the long text from a text file
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    lines = [line.strip() for line in lines if line.strip()]
    return lines


def chunk_text(lines):
    # Load the encoding for the model
    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")

    # Initialize variables
    chunks = []
    current_chunk = []
    current_token_count = 0

    # Loop through each line and group them into chunks
    for line in lines:
        # Calculate the token count for the current line
        line_token_count = len(encoding.encode(line))

        # Check if adding the current line to the current chunk would exceed the maximum token count
        if current_token_count + line_token_count > 500:
            # If it does, add the current chunk to the list of chunks and start a new chunk
            chunks.append(current_chunk)
            current_chunk = []
            current_token_count = 0

        # Add the current line to the current chunk and update the token count
        current_chunk.append(line)
        current_token_count += line_token_count

    # Add the last chunk to the list of chunks
    chunks.append(current_chunk)

    return chunks


def generate_audio_files(chunks, output_dir):
    # Initialize OpenAI client
    client = OpenAI()

    # Generate an MP3 file for each chunk
    now = datetime.now()
    date_time_string = now.strftime("%Y%m%d%H%M")

    for i, chunk in enumerate(chunks):
        # Combine the lines in the current chunk into a single string
        chunk_string = " ".join(chunk)
        print("〰️〰️〰️〰️〰️〰️")
        print(f"{green_text('Prepare for the chunk')} {i+1:06d} of {len(chunks)}")
        print(f"Input String: {chunk_string[:60]}...")
        if len(chunk_string) > 4000:
            print(
                f"Chunk {i+1:06d}: {chunk_string[:60]} is more than 4000 characters, please make it shorter, byebye"
            )
            exit()
        # Start the Braille animation
        stop_flag = threading.Event()
        animation_thread = threading.Thread(target=start_animation, args=(stop_flag,))
        animation_thread.start()

        # Generate an MP3 file for the current chunk
        response = client.audio.speech.create(
            model="tts-1",
            voice="onyx",
            input=chunk_string,
        )
        response.stream_to_file(
            f"{output_dir}/tmp_{date_time_string}_chunk{i+1:06d}.mp3"
        )

        # Stop the Braille animation
        stop_flag.set()
        animation_thread.join()

        print(
            f"A mp3 file saved as 🔀 {output_dir}/tmp_{date_time_string}_chunk{i+1:06d}.mp3"
        )


def combine_audio_files(input_file_path, output_dir):
    # Get the filename without the extension
    input_file_name = os.path.splitext(os.path.basename(input_file_path))[0]

    # Get a list of all the generated MP3 files
    mp3_files = sorted([f for f in os.listdir(output_dir) if f.endswith(".mp3")])

    # Concatenate the MP3 files using ffmpeg
    concat_file_path = f"{output_dir}/concat.txt"
    with open(concat_file_path, "w") as f:
        for mp3_file in mp3_files:
            f.write(f"file '{mp3_file}'\n")
    output_file_path = f"{output_dir}/{input_file_name}.mp3"
    subprocess.call(
        f"ffmpeg -f concat -safe 0 -i {concat_file_path} -c copy {output_file_path}",
        shell=True,
    )


def removed_tmp(outputdir):
    # Get a list of all files in the output directory
    files = os.listdir(outputdir)

    # Loop through the files and remove any that start with "tmp"
    for file in files:
        if file.startswith("tmp"):
            os.remove(os.path.join(outputdir, file))
    os.remove(os.path.join(outputdir, "concat.txt"))


if __name__ == "__main__":
    # Get the input text file name from the command-line argument
    if len(sys.argv) < 2:
        print("Usage: python main.py INPUT_FILE_NAME")
        sys.exit(1)
    input_file_path = sys.argv[1]

    # Create the output directory with the same name as the input file (without the extension) if it does not exist
    input_file_name = os.path.splitext(os.path.basename(input_file_path))[0]
    print(f"Now Create a folder called {green_text(input_file_name)} for you.")
    output_dir = f"./{input_file_name}"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Read the text from the input file, chunk it, and generate audio files for each chunk
    lines = read_text_file(input_file_path)
    chunks = chunk_text(lines)
    generate_audio_files(chunks, output_dir)
    print(
        f"Chunk mp3 files are already in 👉[ ./{green_text(input_file_name)} ]👈 for ffmpeg to combine.\n🎠🎠🎠🎠🎠🎠🎠🎠🎠🎠\n"
    )  # Combine the generated MP3 files into a single file with the same name as the input file
    combine_audio_files(input_file_path, output_dir)
    removed_tmp(output_dir)
    print(
        f"\n🎉 File 👉[ {green_text(input_file_name)} ]👈 is ready for you. 🎉\n"
    )  # Combine the generated MP3 files into a single file with the same name as the input file
