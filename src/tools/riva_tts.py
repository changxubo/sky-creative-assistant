import argparse
import base64
import logging
import time
import wave
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import riva.client
from riva.client.proto.riva_audio_pb2 import AudioEncoding

logger = logging.getLogger(__name__)


def read_file_to_dict(file_path: str) -> Dict[str, str]:
    """
    Read a file and parse key-value pairs separated by double spaces.

    Args:
        file_path (str): Path to the file to read

    Returns:
        Dict[str, str]: Dictionary containing parsed key-value pairs

    Raises:
        ValueError: If no valid entries are found in the file
    """
    result_dict = {}
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            for line_number, line in enumerate(file, start=1):
                line = line.strip()
                if not line:  # Skip empty lines
                    continue

                try:
                    # Split by double space
                    key, value = line.split("  ", 1)
                    result_dict[key.strip()] = value.strip()
                except ValueError:
                    logger.warning(f"Malformed line {line_number}: {line}")
                    continue
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise
    except IOError as e:
        logger.error(f"Error reading file {file_path}: {e}")
        raise

    if not result_dict:
        raise ValueError("Error: No valid entries found in the file.")
    return result_dict


class RivaTTS:
    """
    Client for NVIDIA Riva Text-to-Speech API.

    This class provides a Python interface to interact with NVIDIA Riva's TTS service,
    supporting both streaming and non-streaming synthesis with various audio formats
    and voice options.

    Attributes:
        server (str): The Riva server endpoint
        use_ssl (bool): Whether to use SSL for connection
        ssl_cert (Optional[str]): Path to SSL certificate
        language_code (str): Target language code for synthesis
        voice (str): Voice type to use for synthesis
        sample_rate_hz (int): Audio sample rate in Hz
        encoding (str): Audio encoding format
        metadata (List[Tuple[str, str]]): Authentication metadata
        service: Riva SpeechSynthesisService instance
    """

    def __init__(
        self,
        appid: str,
        access_token: str,
        cluster: str = "Riva_tts",
        voice_type: str = "Magpie-Multilingual.EN-US.Sofia",
        host: str = "grpc.nvcf.nvidia.com:443",
        function_id: str = "",
        use_ssl: bool = True,
        ssl_cert: Optional[str] = None,
        metadata: Optional[List[Tuple[str, str]]] = None,
        language_code: str = "en-US",
        sample_rate_hz: int = 44100,
        encoding: str = "LINEAR_PCM",
    ) -> None:
        """
        Initialize RivaTTS client.

        Args:
            appid (str): Application ID for authentication
            access_token (str): Access token for API authentication
            cluster (str): Cluster name for the service
            voice_type (str): Default voice type to use
            host (str): Server host and port
            function_id (str): Function ID for cloud-based Riva
            use_ssl (bool): Whether to use SSL connection
            ssl_cert (Optional[str]): Path to SSL certificate file
            metadata (Optional[List[Tuple[str, str]]]): Additional metadata
            language_code (str): Default language code
            sample_rate_hz (int): Audio sample rate in Hz
            encoding (str): Audio encoding format
        """
        self.server = host
        self.use_ssl = use_ssl
        self.ssl_cert = ssl_cert
        self.language_code = language_code
        self.voice = voice_type
        self.sample_rate_hz = sample_rate_hz
        self.encoding = encoding

        # Set up metadata for authentication
        self.metadata = metadata or []
        if function_id:
            self.metadata.append(("function-id", function_id))
        if access_token:
            self.metadata.append(("authorization", access_token))

        # Initialize Riva client with error handling
        try:
            auth = riva.client.Auth(
                self.ssl_cert, self.use_ssl, self.server, self.metadata
            )
            self.service = riva.client.SpeechSynthesisService(auth)
        except Exception as e:
            logger.error(f"Failed to initialize Riva client: {e}")
            raise

    def list_voices(self) -> Dict[str, Any]:
        """
        List available voices from Riva service.

        Retrieves all available TTS voices from the connected Riva service,
        organized by language code.

        Returns:
            Dict[str, Any]: Dictionary of available voices grouped by language code.
                           Format: {language_code: {"voices": [voice_names]}}

        Raises:
            Exception: If there's an error communicating with the Riva service
        """
        try:
            config_response = self.service.stub.GetRivaSynthesisConfig(
                riva.client.proto.riva_tts_pb2.RivaSynthesisConfigRequest()
            )

            tts_models = {}
            for model_config in config_response.model_config:
                # Extract language code and voice information
                language_code = model_config.parameters.get("language_code", "unknown")
                voice_name = model_config.parameters.get("voice_name", "unknown")
                subvoices_str = model_config.parameters.get("subvoices", "")

                # Parse subvoices and create full voice names
                subvoices = [
                    voice.split(":")[0]
                    for voice in subvoices_str.split(",")
                    if voice.strip()
                ]
                full_voice_names = [
                    f"{voice_name}.{subvoice}" for subvoice in subvoices
                ]

                # Group voices by language code
                if language_code in tts_models:
                    tts_models[language_code]["voices"].extend(full_voice_names)
                else:
                    tts_models[language_code] = {"voices": full_voice_names}

            # Sort by language code for consistent output
            return dict(sorted(tts_models.items()))

        except Exception as e:
            logger.error(f"Error listing voices: {e}")
            raise

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

        Args:
            text (str): Text to convert to speech
            encoding (str): Output audio encoding format
            speed_ratio (float): Speech speed multiplier (1.0 = normal speed)
            volume_ratio (float): Volume multiplier (1.0 = normal volume)
            pitch_ratio (float): Pitch multiplier (1.0 = normal pitch)
            text_type (str): Type of input text ("plain" or "ssml")
            with_frontend (int): Whether to use frontend processing
            frontend_type (str): Type of frontend processing
            uid (Optional[str]): Unique identifier for the request
            output_file (Optional[Path]): Path to save audio file

        Returns:
            Dict[str, Any]: Dictionary containing:
                - success (bool): Whether synthesis was successful
                - response (Dict): Processing information if successful
                - audio_data (str): Base64-encoded audio data if successful
                - error (str): Error message if failed
        """
        if not text or not text.strip():
            return {
                "success": False,
                "error": "Input text is empty",
                "audio_data": None,
            }

        # Initialize synthesis parameters
        voice = self.voice
        language_code = self.language_code
        stream = False  # Non-streaming synthesis
        zero_shot_audio_prompt_file = None
        zero_shot_quality = None
        zero_shot_transcript = None
        custom_dictionary = {}
        play_audio = False
        output_device = None

        # Audio format settings
        num_channels = 1
        sample_width = 2
        sound_stream = None
        output_wave_file = None
        audio_data = None

        try:
            start_time = time.time()

            # Setup audio output devices if needed
            if output_device is not None or play_audio:
                try:
                    import riva.client.audio_io

                    sound_stream = riva.client.audio_io.SoundCallBack(
                        output_device,
                        nchannels=num_channels,
                        sampwidth=sample_width,
                        framerate=self.sample_rate_hz,
                    )
                except ModuleNotFoundError as e:
                    logger.warning(f"PyAudio not installed: {e}")
                    return {
                        "success": False,
                        "error": f"PyAudio not installed: {str(e)}",
                        "audio_data": None,
                    }

            # Setup output file if specified
            if output_file is not None:
                try:
                    output_wave_file = wave.open(str(output_file), "wb")
                    output_wave_file.setnchannels(num_channels)
                    output_wave_file.setsampwidth(sample_width)
                    output_wave_file.setframerate(self.sample_rate_hz)
                except Exception as e:
                    logger.error(f"Error opening output file {output_file}: {e}")
                    return {
                        "success": False,
                        "error": f"Cannot open output file: {str(e)}",
                        "audio_data": None,
                    }

            # Convert encoding string to enum
            encoding_enum = (
                AudioEncoding.OGGOPUS
                if self.encoding == "OGGOPUS"
                else AudioEncoding.LINEAR_PCM
            )

            # Perform synthesis (streaming vs non-streaming)
            if stream:
                # Streaming synthesis
                responses = self.service.synthesize_online(
                    text,
                    voice,
                    language_code,
                    sample_rate_hz=self.sample_rate_hz,
                    encoding=encoding_enum,
                    zero_shot_audio_prompt_file=zero_shot_audio_prompt_file,
                    zero_shot_quality=(
                        20 if zero_shot_quality is None else zero_shot_quality
                    ),
                    custom_dictionary=custom_dictionary,
                )

                all_audio_data = bytearray()
                for response in responses:
                    if sound_stream is not None:
                        sound_stream(response.audio)
                    if output_wave_file is not None:
                        output_wave_file.writeframesraw(response.audio)
                    all_audio_data.extend(response.audio)

                audio_data = bytes(all_audio_data)
            else:
                # Non-streaming synthesis
                response = self.service.synthesize(
                    text,
                    voice,
                    language_code,
                    sample_rate_hz=self.sample_rate_hz,
                    encoding=encoding_enum,
                    zero_shot_audio_prompt_file=zero_shot_audio_prompt_file,
                    zero_shot_quality=(
                        20 if zero_shot_quality is None else zero_shot_quality
                    ),
                    custom_dictionary=custom_dictionary,
                    zero_shot_transcript=zero_shot_transcript,
                )

                if sound_stream is not None:
                    sound_stream(response.audio)
                if output_wave_file is not None:
                    output_wave_file.writeframesraw(response.audio)
                audio_data = response.audio

            processing_time = time.time() - start_time

            # Validate audio data
            if audio_data is None or len(audio_data) == 0:
                logger.error("No audio data returned from TTS service")
                return {
                    "success": False,
                    "error": "No audio data returned from TTS service",
                    "audio_data": None,
                }

            # Convert binary audio to base64 for API compatibility
            audio_data_base64 = base64.b64encode(audio_data).decode("utf-8")

            # Calculate audio duration
            audio_duration = len(audio_data) / (
                self.sample_rate_hz * sample_width * num_channels
            )

            logger.info(f"TTS synthesis completed in {processing_time:.3f} seconds")

            return {
                "success": True,
                "response": {
                    "processing_time": processing_time,
                    "text_length": len(text),
                    "audio_duration": audio_duration,
                    "sample_rate": self.sample_rate_hz,
                    "encoding": self.encoding,
                },
                "audio_data": audio_data_base64,
            }

        except Exception as e:
            # Extract detailed error message
            error_msg = str(e)
            if hasattr(e, "details") and callable(e.details):
                error_msg = e.details()
            logger.exception(f"Error in TTS API call: {error_msg}")
            return {"success": False, "error": error_msg, "audio_data": None}

        finally:
            # Clean up resources
            if output_wave_file is not None:
                try:
                    output_wave_file.close()
                except Exception as e:
                    logger.warning(f"Error closing output file: {e}")
            if sound_stream is not None:
                try:
                    sound_stream.close()
                except Exception as e:
                    logger.warning(f"Error closing sound stream: {e}")


def parse_args() -> argparse.Namespace:
    """
    Parse command line arguments for Riva TTS client.

    Returns:
        argparse.Namespace: Parsed command line arguments

    Raises:
        SystemExit: If required dependencies are missing
    """
    parser = argparse.ArgumentParser(
        description="Speech synthesis via Riva AI Services",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Text input options
    parser.add_argument(
        "--text",
        type=str,
        help="Text input to synthesize. If missing, server will try first available model "
        "based on --language-code parameter.",
    )

    # Device and voice listing options
    parser.add_argument(
        "--list-devices",
        action="store_true",
        help="List output audio devices indices. No synthesis will be performed if set.",
    )
    parser.add_argument(
        "--list-voices",
        default=True,
        action="store_true",
        help="List available voices. No synthesis will be performed if set.",
    )

    # Voice and audio settings
    parser.add_argument(
        "--voice",
        default="Magpie-Multilingual.EN-US.Sofia",
        help="Voice name to use. If missing, server will try first available model "
        "based on --language-code parameter.",
    )
    parser.add_argument(
        "--zero_shot_audio_prompt_file",
        type=Path,
        help="Input audio prompt file for Zero Shot Model. Audio length should be 3-10 seconds.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default="output.wav",
        help="Output .wav file to write synthesized audio.",
    )
    parser.add_argument(
        "--zero_shot_quality",
        type=int,
        help="Required quality of output audio, ranges between 1-40.",
    )

    # Audio playback options
    parser.add_argument(
        "--play-audio",
        action="store_true",
        help="Play input audio simultaneously with transcribing. "
        "If --output-device not provided, default output device will be used.",
    )
    parser.add_argument("--output-device", type=int, help="Output device to use.")

    # Language and audio format settings
    parser.add_argument(
        "--language-code", default="en-US", help="Language of input text."
    )
    parser.add_argument(
        "--sample-rate-hz",
        type=int,
        default=44100,
        help="Number of audio frames per second in synthesized audio.",
    )
    parser.add_argument(
        "--encoding",
        default="LINEAR_PCM",
        choices={"LINEAR_PCM", "OGGOPUS"},
        help="Output audio encoding.",
    )

    # Additional options
    parser.add_argument(
        "--custom-dictionary",
        type=str,
        help="File path to user dictionary with key-value pairs separated by double spaces.",
    )
    parser.add_argument(
        "--stream",
        action="store_true",
        help="Enable streaming synthesis. Audio is yielded as it gets ready. "
        "If not set, synthesized audio is returned in 1 response when all text is processed.",
    )
    parser.add_argument(
        "--zero_shot_transcript",
        type=str,
        help="Transcript corresponding to Zero shot audio prompt.",
    )

    # Server and authentication parameters
    parser.add_argument(
        "--server", default="grpc.nvcf.nvidia.com:443", help="Riva server endpoint."
    )
    parser.add_argument(
        "--use-ssl", action="store_true", default=True, help="Use SSL for connection."
    )
    parser.add_argument("--function-id", help="Function ID for cloud-based Riva.")
    parser.add_argument("--authorization", help="Authorization bearer token.")
    parser.add_argument("--ssl-cert", help="Path to SSL certificate.")

    args = parser.parse_args()

    # Expand output file path if provided
    if args.output is not None:
        args.output = args.output.expanduser()

    # Check for audio dependencies if needed
    if args.list_devices or args.output_device or args.play_audio:
        try:
            import riva.client.audio_io
        except ModuleNotFoundError as e:
            print(f"ModuleNotFoundError: {e}")
            print("Please install PyAudio from https://pypi.org/project/PyAudio")
            exit(1)

    return args


def main() -> None:
    """
    Main function to demonstrate RivaTTS client usage.

    This function shows how to initialize the RivaTTS client and perform
    text-to-speech synthesis with proper error handling.
    """
    # Configuration - Replace with your actual credentials
    app_id = "<your_app_id_here>"  # Replace with your actual app ID
    access_token = (
        "Bearer <your_access_token_here>"  # Replace with your actual access token
    )

    cluster = "Riva_tts"
    voice_type = "Magpie-Multilingual.EN-US.Sofia"

    # Test request parameters
    synthesis_request = {
        "text": "This is a test of the Riva TTS service.",
        "encoding": "mp3",
        "speed_ratio": 1.0,
        "volume_ratio": 1.0,
        "pitch_ratio": 1.0,
        "text_type": "plain",
        "with_frontend": 1,
        "frontend_type": "unitTson",
    }

    try:
        # Initialize TTS client
        tts_client = RivaTTS(
            function_id=app_id,
            access_token=access_token,
            cluster=cluster,
            voice_type=voice_type,
        )

        # Perform text-to-speech synthesis
        result = tts_client.text_to_speech(
            text=synthesis_request["text"][:1024],  # Limit text length
            encoding=synthesis_request["encoding"],
            speed_ratio=synthesis_request["speed_ratio"],
            volume_ratio=synthesis_request["volume_ratio"],
            pitch_ratio=synthesis_request["pitch_ratio"],
            text_type=synthesis_request["text_type"],
            with_frontend=synthesis_request["with_frontend"],
            frontend_type=synthesis_request["frontend_type"],
            output_file=Path("output.wav"),  # Save to file for debugging
        )

        print("TTS Result:", result)

        if result["success"]:
            print(
                f"Audio generated successfully in {result['response']['processing_time']:.3f}s"
            )
            print(f"Audio duration: {result['response']['audio_duration']:.3f}s")
            print(f"Text length: {result['response']['text_length']} characters")

            # Decode and use the base64 audio data
            audio_data = base64.b64decode(result["audio_data"])
            print(f"Audio data size: {len(audio_data)} bytes")

        else:
            print(f"Error: {result['error']}")

    except Exception as e:
        logger.exception(f"Error in main function: {e}")
        print(f"Failed to initialize or use TTS client: {e}")


if __name__ == "__main__":
    main()
