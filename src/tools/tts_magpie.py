# SPDX-FileCopyrightText: Copyright (c) 2022 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: MIT

import argparse
import time
import wave
import json
import base64
from pathlib import Path
import uuid
import logging
import requests
from typing import Optional, Dict, Any, List

import riva.client
from riva.client.argparse_utils import add_connection_argparse_parameters
from riva.client.proto.riva_audio_pb2 import AudioEncoding

logger = logging.getLogger(__name__)

def read_file_to_dict(file_path):
    result_dict = {}
    with open(file_path, 'r') as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()
            try:
                key, value = line.split('  ', 1)  # Split by double space
                result_dict[str(key.strip())] = str(value.strip())
            except ValueError:
                print(f"Warning: Malformed line {line}")
                continue
    if not result_dict:
        raise ValueError("Error: No valid entries found in the file.")
    return result_dict


class RivaTTS:
    """
    Client for Riva Text-to-Speech API.
    """
    def __init__(
        self,
        appid: str,
        access_token: str,
        cluster: str = "Riva_tts",
        voice_type: str = "Magpie-Multilingual.EN-US.Sofia",
        host: str = "grpc.nvcf.nvidia.com:443",
        function_id: str="",
        use_ssl: bool = True,
        ssl_cert: Optional[str] = None,
        metadata: Optional[List[str]] = None,
        language_code: str = "en-US",
        sample_rate_hz: int = 44100,
        encoding: str = "LINEAR_PCM",
    ):
        self.server = host
        self.use_ssl = use_ssl
        self.ssl_cert = ssl_cert
        self.language_code = language_code
        self.voice = voice_type
        self.sample_rate_hz = sample_rate_hz
        self.encoding = encoding
        
        # Set up metadata for authentication
        self.metadata = []
        if function_id:
            self.metadata.append(("function-id", function_id))
        if access_token:
            self.metadata.append(("authorization", access_token))
        
        # Initialize Riva client
        auth = riva.client.Auth(
            self.ssl_cert, 
            self.use_ssl, 
            self.server, 
            self.metadata
        )
        self.service = riva.client.SpeechSynthesisService(auth)

    def list_voices(self) -> Dict[str, Any]:
        """
        List available voices from Riva service.

        Returns:
            Dictionary of available voices grouped by language code
        """
        config_response = self.service.stub.GetRivaSynthesisConfig(
                riva.client.proto.riva_tts_pb2.RivaSynthesisConfigRequest()
            )
        tts_models = dict()
        for model_config in config_response.model_config:
                language_code = model_config.parameters['language_code']
                voice_name = model_config.parameters['voice_name']
                subvoices = [voice.split(':')[0] for voice in model_config.parameters['subvoices'].split(',')]
                full_voice_names = [voice_name + "." + subvoice for subvoice in subvoices]

                if language_code in tts_models:
                    tts_models[language_code]['voices'].extend(full_voice_names)
                else:
                    tts_models[language_code] = {"voices": full_voice_names}

        tts_models = dict(sorted(tts_models.items()))
        return tts_models

    def text_to_speech(
        self,
        text: str,
        encoding: str = "mp3",
        speed_ratio: float = 1.0,
        volume_ratio: float = 1.0,
        pitch_ratio: float = 1.0,
        text_type: str = "plain",
        with_frontend: int = 1,
        frontend_type: str = "unitTson",
        uid: Optional[str] = None,
        output_file: Optional[Path] = None,

    ) -> Dict[str, Any]:
        """
        Convert text to speech using Riva TTS API.
        Returns:
            Dictionary containing the success status, audio data, and any errors
        """
        voice = self.voice
        language_code = self.language_code
        stream: bool = False
        zero_shot_audio_prompt_file: str = None
        zero_shot_quality: str = None
        zero_shot_transcript: str = None
        custom_dictionary: dict = {}
        play_audio: bool = False
        output_device: str = None

        # if custom_dictionary is None:
        #     custom_dictionary = {}
        
        nchannels = 1
        sampwidth = 2
        sound_stream, out_f = None, None
        audio_data = None
        
        try:
            start = time.time()
            
            # Setup audio output if needed
            if output_device is not None or play_audio:
                if output_device is not None:
                    print(type(output_device), output_device, "output_device")
                if play_audio:
                    print(type(play_audio), play_audio, "play_audio")
                try:
                    import riva.client.audio_io
                    sound_stream = riva.client.audio_io.SoundCallBack(
                        output_device, nchannels=nchannels, sampwidth=sampwidth, framerate=self.sample_rate_hz
                    )
                except ModuleNotFoundError as e:
                    return {"success": False, "error": f"PyAudio not installed: {str(e)}", "audio_data": None}
            
            if output_file is not None:
                out_f = wave.open(str(output_file), 'wb')
                out_f.setnchannels(nchannels)
                out_f.setsampwidth(sampwidth)
                out_f.setframerate(self.sample_rate_hz)

            # Handle encoding
            encoding_enum = AudioEncoding.OGGOPUS if self.encoding == "OGGOPUS" else AudioEncoding.LINEAR_PCM
            
            # Perform synthesis
            if stream:
                responses = self.service.synthesize_online(
                    text, voice, language_code,
                    sample_rate_hz=self.sample_rate_hz,
                    encoding=encoding_enum,
                    zero_shot_audio_prompt_file=zero_shot_audio_prompt_file,
                    zero_shot_quality=(20 if zero_shot_quality is None else zero_shot_quality),
                    custom_dictionary=custom_dictionary,
                )
                
                all_audio = bytearray()
                first = True
                for resp in responses:
                    if first:
                        first_audio_time = time.time() - start
                        first = False
                    
                    if sound_stream is not None:
                        sound_stream(resp.audio)
                    if out_f is not None:
                        out_f.writeframesraw(resp.audio)
                    all_audio.extend(resp.audio)
                
                audio_data = bytes(all_audio)
            else:
                resp = self.service.synthesize(
                    text, voice, language_code,
                    sample_rate_hz=self.sample_rate_hz,
                    encoding=encoding_enum,
                    zero_shot_audio_prompt_file=zero_shot_audio_prompt_file,
                    zero_shot_quality=(20 if zero_shot_quality is None else zero_shot_quality),
                    custom_dictionary=custom_dictionary,
                    zero_shot_transcript=zero_shot_transcript,
                )
                
                if sound_stream is not None:
                    sound_stream(resp.audio)
                if out_f is not None:
                    out_f.writeframesraw(resp.audio)
                audio_data = resp.audio
                
            processing_time = time.time() - start

            logger.info(f"TTS synthesis completed in {processing_time:.3f} seconds")
            if audio_data is None:
                logger.info(f"TTS synthesis completed in {processing_time:.3f} seconds")
                raise ValueError("No audio data returned from TTS service.")
            
            # Convert binary audio to base64 for API compatibility with VolcengineTTS
            audio_data_base64 = base64.b64encode(audio_data).decode('utf-8') if audio_data else None
            
            return {
                "success": True,
                "response": {
                    "processing_time": processing_time,
                    "text_length": len(text),
                    "audio_duration": len(audio_data) / (self.sample_rate_hz * sampwidth),
                },
                "audio_data": audio_data_base64
            }
            
        except Exception as e:
            error_msg = str(e)
            if hasattr(e, "details") and callable(e.details):
                error_msg = e.details()
            logger.exception(f"Error in TTS API call: {error_msg}")
            return {"success": False, "error": error_msg, "audio_data": None}
        
        finally:
            if out_f is not None:
                out_f.close()
            if sound_stream is not None:
                sound_stream.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Speech synthesis via Riva AI Services",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    # group = parser.add_mutually_exclusive_group(required=True)
    # group.add_argument("--text", type=str, help="Text input to synthesize.")
    # group.add_argument("--list-devices", action="store_true", help="List output audio devices indices.")
    # group.add_argument("--list-voices", action="store_true", help="List available voices.")
    parser.add_argument(
        "--text",
        type=str,
        help="Text input to synthesize. If this parameter is missing, then the server will try a first available model "
        "based on parameter `--language-code`.",
    )
    parser.add_argument(
        "--list-devices",
        action="store_true",
        help="List output audio devices indices. If this option is set, then no synthesis will be performed.",
    )
    parser.add_argument(
        "--list-voices",
        default=True,
        action="store_true",
        help="List available voices. If this option is set, then no synthesis will be performed.",
    )
    parser.add_argument(
        "--voice",
        default="Magpie-Multilingual.EN-US.Sofia",
        help="A voice name to use. If this parameter is missing, then the server will try a first available model "
        "based on parameter `--language-code`.",
    )
    parser.add_argument(
        "--zero_shot_audio_prompt_file",
        type=Path,
        help="Input audio prompt file for Zero Shot Model. Audio length should be between 3-10 seconds.",
    )
    parser.add_argument("-o", "--output", type=Path, default="output.wav", help="Output file .wav file to write synthesized audio.")
    parser.add_argument(
        "--zero_shot_quality",
        type=int,
        help="Required quality of output audio, ranges between 1-40.",
    )
    parser.add_argument(
        "--play-audio",
        action="store_true",
        help="Whether to play input audio simultaneously with transcribing. If `--output-device` is not provided, "
        "then the default output audio device will be used.",
    )
    parser.add_argument("--output-device", type=int, help="Output device to use.")
    parser.add_argument("--language-code", default="en-US", help="A language of input text.")
    parser.add_argument(
        "--sample-rate-hz", type=int, default=44100, help="Number of audio frames per second in synthesized audio."
    )
    parser.add_argument("--encoding", default="LINEAR_PCM", choices={"LINEAR_PCM", "OGGOPUS"}, help="Output audio encoding.")
    parser.add_argument("--custom-dictionary", type=str, help="A file path to a user dictionary with key-value pairs separated by double spaces.")
    parser.add_argument(
        "--stream",
        action="store_true",
        help="If this option is set, then streaming synthesis is applied. Streaming means that audio is yielded "
        "as it gets ready. If `--stream` is not set, then a synthesized audio is returned in 1 response only when "
        "all text is processed.",
    )
    parser.add_argument(
        "--zero_shot_transcript",
        type=str,
        help="Transcript corresponding to Zero shot audio prompt.",
    )
    
    # Add server and authentication parameters
    parser.add_argument("--server", default="grpc.nvcf.nvidia.com:443", help="Riva server endpoint.")
    parser.add_argument("--use-ssl", action="store_true", default=True, help="Use SSL for connection.")
    parser.add_argument("--function-id", help="The function ID for cloud-based Riva.")
    parser.add_argument("--authorization", help="The authorization bearer token.")
    parser.add_argument("--ssl-cert", help="Path to SSL certificate.")
    
    args = parser.parse_args()
    if args.output is not None:
        args.output = args.output.expanduser()
    try:
        if args.list_devices or args.output_device or args.play_audio:
            print(args.list_devices, args.output_device, args.play_audio)
            import riva.client.audio_io
    except ModuleNotFoundError as e:
        print(f"ModuleNotFoundError: {e}")
        print("Please install pyaudio from https://pypi.org/project/PyAudio")
        exit(1)
    return args


def main() -> None:
    app_id = "<your_app_id_here>"  # Replace with your actual app ID
    access_token = "Bearer <your_access_token_here>"  # Replace with your actual access token
    
    cluster = "Riva_tts"
    voice_type = "Magpie-Multilingual.EN-US.Sofia"

    request = {
        "text": "This is a test of the Riva TTS service.",
        "encoding": "mp3",
        "speed_ratio": 1.0,
        "volume_ratio": 1.0,
        "pitch_ratio": 1.0,
        "text_type": "plain",
        "with_frontend": 1,
        "frontend_type": "unitTson",
    }

    tts_client = RivaTTS(
        function_id=app_id,
        access_token=access_token,
        cluster=cluster,
        voice_type=voice_type,
    )
    # Call the TTS API
    result = tts_client.text_to_speech(
        text=request['text'][:1024],
        encoding=request['encoding'],
        speed_ratio=request['speed_ratio'],
        volume_ratio=request['volume_ratio'],
        pitch_ratio=request['pitch_ratio'],
        text_type=request['text_type'],
        with_frontend=request['with_frontend'],
        frontend_type=request['frontend_type'],
        output_file="output.wav",   # Specify output file for debugging
    )

    print("TTS Result:", result)

    if not result["success"]:
        print(f"Error: {result['error']}")
        # raise HTTPException(status_code=500, detail=str(result["error"]))

    # Decode the base64 audio data
    audio_data = base64.b64decode(result["audio_data"])

    if result["success"]:
        print(f"Audio generated successfully in {result['response']['processing_time']:.3f}s")
        # Access base64 audio data with result["audio_data"]
    else:
        print(f"Error: {result['error']}")


if __name__ == '__main__':
    main()

