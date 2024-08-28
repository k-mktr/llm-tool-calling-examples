"""
title: DeepL Translation Tool
author: Karol S. Danisz
author_url: https://github.com/k-mktr/llm-tool-calling-examples
buy_me_a_coffee: https://mktr.sbs/coffee
version: 0.1.0
license: MIT
description: A tool for translating text using the DeepL API.
"""

import json
import urllib.request
import urllib.parse
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Callable, Any

DEBUG = False

def get_translation(text: str, target_lang: str, api_key: str):
    url = "https://api-free.deepl.com/v2/translate"
    data = urllib.parse.urlencode({
        "auth_key": api_key,
        "text": text,
        "target_lang": target_lang
    }).encode('ascii')

    try:
        with urllib.request.urlopen(url, data=data) as response:
            result = json.loads(response.read().decode('utf-8'))
            if 'translations' in result and len(result['translations']) > 0:
                return result['translations'][0]['text']
            else:
                return None
    except urllib.error.URLError as e:
        if DEBUG:
            print(f"Translation error: {str(e)}")
        return None

def format_datetime(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")

class Tools:
    class Valves(BaseModel):
        DEEPL_API_KEY: str = Field(
            default=None, description="Your DeepL API key."
        )

    def __init__(self):
        self.valves = self.Valves()

    async def translate_text(self, text: str, target_lang: str, __event_emitter__: Callable[[dict], Any] = None, __user__: dict = {}) -> str:
        """
        Translate text using the DeepL API.
        
        :param text: The text to translate.
        :param target_lang: The target language code (e.g., 'EN' for English, 'DE' for German, 'FR' for French).
        :param __event_emitter__: An optional callback function to emit status events throughout the process.
        :param __user__: A dictionary containing user information.
        :return: Instructions for presenting the translation or an error message.
        """
        def status_object(description="Unknown State", status="in_progress", done=False):
            return {
                "type": "status",
                "data": {
                    "status": status,
                    "description": description,
                    "done": done,
                },
            }

        if __event_emitter__:
            await __event_emitter__(status_object("Initializing DeepL Translation"))

        if not self.valves.DEEPL_API_KEY:
            if __event_emitter__:
                await __event_emitter__(status_object("Error: DeepL API key is not set", status="error", done=True))
            return "DeepL API key is not set. Please set it in your environment variables."

        if __event_emitter__:
            await __event_emitter__(status_object("Sending translation request to DeepL API"))

        url = "https://api-free.deepl.com/v2/translate"
        data = urllib.parse.urlencode({
            "auth_key": self.valves.DEEPL_API_KEY,
            "text": text,
            "target_lang": target_lang
        }).encode('ascii')

        try:
            with urllib.request.urlopen(url, data=data) as response:
                result = json.loads(response.read().decode('utf-8'))
                if 'translations' in result and len(result['translations']) > 0:
                    translated_text = result['translations'][0]['text']
                    # Get the current time right before returning the result
                    current_time = format_datetime(datetime.utcnow())
                    
                    if __event_emitter__:
                        await __event_emitter__(status_object(f"Translation completed successfully at {current_time}", status="complete", done=True))
                    
                    return f"""
Present the following translation result:

Target language: {target_lang}
Translated text: {translated_text}

Provide this information in the following format:
**Target Language:** [target language]
**DeepL Translation Result:** [translated text]

Ensure you use the exact translated text without any modifications."""
                else:
                    if __event_emitter__:
                        await __event_emitter__(status_object("Error: No translation found in the response", status="error", done=True))
                    return "Translation failed: No translation found in the response."
        except urllib.error.URLError as e:
            if __event_emitter__:
                await __event_emitter__(status_object(f"Error: {str(e)}", status="error", done=True))
            return f"Translation failed: {str(e)}"

    def list_supported_languages(self) -> str:
        """
        List the languages supported by the DeepL API.
        
        :return: Instructions for presenting the list of supported languages.
        """
        languages = {
            "BG": "Bulgarian", "CS": "Czech", "DA": "Danish", "DE": "German", "EL": "Greek",
            "EN": "English", "ES": "Spanish", "ET": "Estonian", "FI": "Finnish", "FR": "French",
            "HU": "Hungarian", "ID": "Indonesian", "IT": "Italian", "JA": "Japanese", "LT": "Lithuanian",
            "LV": "Latvian", "NL": "Dutch", "PL": "Polish", "PT": "Portuguese", "RO": "Romanian",
            "RU": "Russian", "SK": "Slovak", "SL": "Slovenian", "SV": "Swedish", "TR": "Turkish",
            "UK": "Ukrainian", "ZH": "Chinese"
        }

        language_list = "\n".join([f"{code}: {name}" for code, name in languages.items()])

        return f"""
Present the following list of languages supported by the DeepL API:

{language_list}

Provide this information in a clear, formatted manner. Begin your response with 'DeepL Supported Languages:' and list the languages in a readable format."""