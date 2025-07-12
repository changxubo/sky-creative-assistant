"""
Text-to-Speech module using Volcengine TTS API.

This module provides a client for converting text to speech using the Volcengine
TTS service with comprehensive error handling and logging.
"""

import json
import logging
import uuid
from typing import Any, Dict, Optional

import requests

logger = logging.getLogger(__name__)


class VolcengineTTS:
    """
    Client for Volcengine Text-to-Speech API.
    
    This class provides a comprehensive interface to the Volcengine TTS service,
    allowing conversion of text to speech with configurable audio parameters.
    
    Attributes:
        appid (str): Platform application ID for API authentication
        access_token (str): Access token for API authorization
        cluster (str): TTS cluster identifier
        voice_type (str): Voice model identifier for speech synthesis
        host (str): API host domain
        api_url (str): Complete API endpoint URL
        header (Dict[str, str]): HTTP headers for API requests
    """

    def __init__(
        self,
        appid: str,
        access_token: str,
        cluster: str = "volcano_tts",
        voice_type: str = "BV700_V2_streaming",
        host: str = "openspeech.bytedance.com",
    ) -> None:
        """
        Initialize the Volcengine TTS client with authentication credentials.

        Args:
            appid (str): Platform application ID for API authentication
            access_token (str): Access token for API authorization
            cluster (str, optional): TTS cluster name. Defaults to "volcano_tts"
            voice_type (str, optional): Voice type identifier. Defaults to "BV700_V2_streaming"
            host (str, optional): API host domain. Defaults to "openspeech.bytedance.com"
            
        Raises:
            ValueError: If required parameters are empty or None
        """
        # Validate required parameters
        if not appid or not appid.strip():
            raise ValueError("appid cannot be empty or None")
        if not access_token or not access_token.strip():
            raise ValueError("access_token cannot be empty or None")
            
        self.appid = appid.strip()
        self.access_token = access_token.strip()
        self.cluster = cluster
        self.voice_type = voice_type
        self.host = host
        self.api_url = f"https://{host}/api/v1/tts"
        
        # Fixed header format - removed semicolon which could cause authentication issues
        self.header = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

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
    ) -> Dict[str, Any]:
        """
        Convert text to speech using Volcengine TTS API.

        Args:
            text (str): Text content to convert to speech
            encoding (str, optional): Audio encoding format (e.g., 'mp3', 'wav'). Defaults to "mp3"
            speed_ratio (float, optional): Speech speed multiplier (0.5-2.0). Defaults to 1.0
            volume_ratio (float, optional): Speech volume multiplier (0.1-3.0). Defaults to 1.0
            pitch_ratio (float, optional): Speech pitch multiplier (0.5-2.0). Defaults to 1.0
            text_type (str, optional): Input text type ('plain' or 'ssml'). Defaults to "plain"
            with_frontend (int, optional): Enable frontend text processing (0 or 1). Defaults to 1
            frontend_type (str, optional): Frontend processing type. Defaults to "unitTson"
            uid (Optional[str], optional): User identifier for tracking. Auto-generated if None

        Returns:
            Dict[str, Any]: Response dictionary containing:
                - success (bool): Whether the operation succeeded
                - response (Dict): Full API response (if successful)
                - audio_data (str): Base64-encoded audio data (if successful)
                - error (str): Error description (if failed)
                
        Raises:
            ValueError: If input parameters are invalid
        """
        # Validate input parameters
        if not text or not text.strip():
            return {
                "success": False, 
                "error": "Text cannot be empty or None", 
                "audio_data": None
            }
            
        # Validate numeric parameters ranges
        if not (0.5 <= speed_ratio <= 2.0):
            return {
                "success": False,
                "error": "speed_ratio must be between 0.5 and 2.0",
                "audio_data": None
            }
        if not (0.1 <= volume_ratio <= 3.0):
            return {
                "success": False,
                "error": "volume_ratio must be between 0.1 and 3.0", 
                "audio_data": None
            }
        if not (0.5 <= pitch_ratio <= 2.0):
            return {
                "success": False,
                "error": "pitch_ratio must be between 0.5 and 2.0",
                "audio_data": None
            }

        # Generate unique user ID if not provided
        if not uid:
            uid = str(uuid.uuid4())

        # Construct API request payload
        request_payload = {
            "app": {
                "appid": self.appid,
                "token": self.access_token,
                "cluster": self.cluster,
            },
            "user": {"uid": uid},
            "audio": {
                "voice_type": self.voice_type,
                "encoding": encoding,
                "speed_ratio": speed_ratio,
                "volume_ratio": volume_ratio,
                "pitch_ratio": pitch_ratio,
            },
            "request": {
                "reqid": str(uuid.uuid4()),  # Unique request identifier
                "text": text,
                "text_type": text_type,
                "operation": "query",
                "with_frontend": with_frontend,
                "frontend_type": frontend_type,
            },
        }

        try:
            # Sanitize text for logging (remove line breaks that could break logs)
            sanitized_text_for_log = text.replace("\r\n", "").replace("\n", "")
            logger.debug(f"Sending TTS request for text: {sanitized_text_for_log[:50]}...")
            
            # Make API request with proper error handling
            response = requests.post(
                self.api_url, 
                data=json.dumps(request_payload), 
                headers=self.header,
                timeout=30  # Added timeout to prevent hanging requests
            )
            
            # Parse response JSON with error handling
            try:
                response_json = response.json()
            except json.JSONDecodeError as json_error:
                logger.error(f"Failed to parse JSON response: {json_error}")
                return {
                    "success": False, 
                    "error": f"Invalid JSON response: {json_error}", 
                    "audio_data": None
                }

            # Check HTTP status code
            if response.status_code != 200:
                logger.error(f"TTS API HTTP error {response.status_code}: {response_json}")
                return {
                    "success": False, 
                    "error": f"HTTP {response.status_code}: {response_json}", 
                    "audio_data": None
                }

            # Validate response structure
            if "data" not in response_json:
                logger.error(f"TTS API returned no data field: {response_json}")
                return {
                    "success": False,
                    "error": "No audio data field in response",
                    "audio_data": None,
                }

            # Check if data field is not empty
            if not response_json["data"]:
                logger.warning("TTS API returned empty audio data")
                return {
                    "success": False,
                    "error": "Empty audio data returned",
                    "audio_data": None,
                }

            logger.info("TTS conversion completed successfully")
            return {
                "success": True,
                "response": response_json,
                "audio_data": response_json["data"],  # Base64 encoded audio data
            }

        except requests.exceptions.Timeout:
            logger.error("TTS API request timed out")
            return {
                "success": False, 
                "error": "Request timeout", 
                "audio_data": None
            }
        except requests.exceptions.ConnectionError as conn_error:
            logger.error(f"TTS API connection error: {conn_error}")
            return {
                "success": False, 
                "error": f"Connection error: {conn_error}", 
                "audio_data": None
            }
        except requests.exceptions.RequestException as req_error:
            logger.error(f"TTS API request error: {req_error}")
            return {
                "success": False, 
                "error": f"Request error: {req_error}", 
                "audio_data": None
            }
        except Exception as unexpected_error:
            logger.exception(f"Unexpected error in TTS API call: {unexpected_error}")
            return {
                "success": False, 
                "error": f"Unexpected error: {unexpected_error}", 
                "audio_data": None
            }
