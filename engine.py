import base64
import json
import re
import requests
from gtts import gTTS
import io
from deep_translator import GoogleTranslator
from PIL import Image
import numpy as np

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
OLLAMA_URL      = "http://localhost:11434/api/generate"
OLLAMA_CHAT_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL    = "llava"

# ─────────────────────────────────────────────
# SUPPORTED LANGUAGES (with translation targets)
# ─────────────────────────────────────────────
LANGUAGES = {
    "English":    {"gtts": "en",    "translate_to": "en"},
    "Hindi":      {"gtts": "hi",    "translate_to": "hi"},
    "Spanish":    {"gtts": "es",    "translate_to": "es"},
    "French":     {"gtts": "fr",    "translate_to": "fr"},
    "German":     {"gtts": "de",    "translate_to": "de"},
    "Arabic":     {"gtts": "ar",    "translate_to": "ar"},
    "Portuguese": {"gtts": "pt",    "translate_to": "pt"},
    "Japanese":   {"gtts": "ja",    "translate_to": "ja"},
    "Chinese":    {"gtts": "zh-CN", "translate_to": "zh-CN"},
    "Russian":    {"gtts": "ru",    "translate_to": "ru"},
}

def convert_to_jpeg(image_bytes: bytes) -> bytes:
    """
    Convert any image format (including WebP) to JPEG bytes for Ollama compatibility.
    """
    try:
        # Open the image from bytes
        img = Image.open(io.BytesIO(image_bytes))
        
        # Convert to RGB if necessary (handles RGBA, P, etc.)
        if img.mode not in ('RGB', 'L'):
            img = img.convert('RGB')
        
        # Save as JPEG to bytes
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=85)
        output.seek(0)
        return output.getvalue()
    except Exception as e:
        print(f"Image conversion error: {e}")
        # If conversion fails, return original bytes
        return image_bytes

def encode_image_to_base64(image_path: str) -> str:
    with open(image_path, "rb") as f:
        image_bytes = f.read()
        # Convert to JPEG for compatibility
        jpeg_bytes = convert_to_jpeg(image_bytes)
        return base64.b64encode(jpeg_bytes).decode("utf-8")

def encode_image_bytes_to_base64(image_bytes: bytes) -> str:
    # Convert to JPEG for compatibility
    jpeg_bytes = convert_to_jpeg(image_bytes)
    return base64.b64encode(jpeg_bytes).decode("utf-8")

# Natural language prompts for better translations
def make_natural_hindi(text: str) -> str:
    """Post-process Hindi translation to sound more natural and conversational."""
    # Remove overly formal constructions
    text = re.sub(r'दर्शाती है', 'है', text)
    text = re.sub(r'प्रदर्शित करता है', 'दिखाता है', text)
    text = re.sub(r'इंगित करता है', 'बताता है', text)
    text = re.sub(r'दृश्यमान', 'दिख रहा', text)
    text = re.sub(r'विशिष्ट', 'खास', text)
    text = re.sub(r'पता चलता है', 'लगता है', text)
    text = re.sub(r'सुझाव देते हैं', 'लग रहे हैं', text)
    text = re.sub(r'के दौरान', 'में', text)
    text = re.sub(r'स्थितियाँ', 'मौसम', text)
    
    # Make it more conversational
    text = re.sub(r'छवि', 'तस्वीर', text)
    text = re.sub(r'पाठ', 'लिखाई', text)
    text = re.sub(r'पृष्ठभूमि', 'पीछे', text)
    text = re.sub(r'अग्रभूमि', 'सामने', text)
    
    # Add natural flow
    if text.startswith('यह'):
        text = 'देखिए, ' + text[2:]
    
    return text

def translate_text_natural(text: str, target_language: str) -> str:
    """Translate English text to target language with natural sounding output."""
    if target_language == "English":
        return text
    
    lang_code = LANGUAGES.get(target_language, {}).get("translate_to", "en")
    if lang_code == "en":
        return text
    
    try:
        translator = GoogleTranslator(source='en', target=lang_code)
        
        # Split into sentences for better translation
        sentences = re.split(r'(?<=[.!?])\s+', text)
        translated_sentences = []
        
        for sentence in sentences:
            if not sentence.strip():
                continue
                
            # Translate the sentence
            translated = translator.translate(sentence)
            
            # Apply natural language post-processing for Hindi
            if lang_code == "hi":
                translated = make_natural_hindi(translated)
            
            translated_sentences.append(translated)
        
        result = ' '.join(translated_sentences)
        
        # For Hindi, add a natural opening if it's a summary
        if lang_code == "hi" and len(result) < 300:
            if not result.startswith(('देखिए', 'यहाँ', 'इस')):
                result = "देखिए, " + result.lower()
        
        return result
        
    except Exception as e:
        print(f"Translation error: {e}")
        return text  # Fallback to English

def get_analysis_prompt() -> str:
    """Get prompt for image analysis (always in English for Llava)."""
    return """You are a friendly accessibility assistant for visually impaired users.
Analyze the provided image carefully and return ONLY a valid JSON object — no extra text, no markdown, no code fences.

Respond in English using simple, conversational language (like you're talking to a friend).

The JSON must follow this exact structure:
{
  "quick_summary": "A simple 1-sentence overview of what the image shows. Keep it short and natural.",
  "detailed_readout": "A detailed but conversational description of what's in the image. Describe text, objects, scenery in a natural way."
}

Rules:
- Use simple, everyday language - no complex words
- If there's text in the image, read it out naturally
- Describe colors, shapes, and important details
- Sound helpful and warm, like a guide
- Return ONLY the raw JSON. Nothing else."""

# ─────────────────────────────────────────────
# VISION ANALYSIS (with natural translation)
# ─────────────────────────────────────────────
def analyze_image(image_b64: str, language: str = "English") -> dict:
    """Analyze image in English, then translate to target language naturally."""
    prompt = get_analysis_prompt()
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "images": [image_b64],
        "stream": False,
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            "Could not connect to Ollama. Make sure Ollama is running: `ollama serve`"
        )
    except requests.exceptions.Timeout:
        raise RuntimeError("Ollama timed out. Try a smaller image or check system resources.")
    except requests.exceptions.HTTPError as e:
        if response.status_code == 500:
            raise RuntimeError(
                "Ollama server error. This might be due to an unsupported image format. "
                "Make sure you're using JPG or PNG images. Error: " + str(e)
            )
        raise

    raw_text = response.json().get("response", "")
    cleaned  = re.sub(r"```(?:json)?", "", raw_text).strip().strip("`").strip()
    match    = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if not match:
        raise ValueError(f"Model did not return valid JSON.\nRaw response:\n{raw_text}")

    try:
        result = json.loads(match.group())
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON parse error: {e}\nRaw response:\n{raw_text}")

    for key in ("quick_summary", "detailed_readout"):
        if key not in result:
            raise ValueError(f"Missing key '{key}' in model response: {result}")

    # Translate naturally if needed
    if language != "English":
        result["quick_summary"] = translate_text_natural(result["quick_summary"], language)
        result["detailed_readout"] = translate_text_natural(result["detailed_readout"], language)

    return result

# ─────────────────────────────────────────────
# FOLLOW-UP CHAT (with natural translation)
# ─────────────────────────────────────────────
def chat_about_image(
    image_b64: str,
    user_question: str,
    chat_history: list,
    analysis_result: dict,
    language: str = "English",
) -> str:
    """
    Send a follow-up question about the image to Ollama.
    User question might be in target language - translate to English for Llava,
    then translate response back to target language naturally.
    """
    
    # Translate user question to English if needed
    if language != "English":
        lang_code = LANGUAGES.get(language, {}).get("translate_to", "en")
        try:
            # Need to translate from target language to English
            eng_translator = GoogleTranslator(source=lang_code, target='en')
            english_question = eng_translator.translate(user_question)
        except Exception:
            english_question = user_question
    else:
        english_question = user_question

    # Always use English context for Llava with natural language instruction
    system_context = (
        f"You are a friendly accessibility assistant. "
        f"The user has uploaded an image. Here's what you saw in it: "
        f"Quick look: {analysis_result.get('quick_summary', '')} "
        f"More details: {analysis_result.get('detailed_readout', '')} "
        f"Now answer the user's question about this image. "
        f"Be conversational, warm, and use simple everyday language. "
        f"Keep your answer helpful and natural, like talking to a friend. "
        f"Answer in English."
    )

    messages = [
        {"role": "user",      "content": system_context},
        {"role": "assistant", "content": "Got it! I'll help describe the image in a friendly, natural way."},
    ]

    for turn in chat_history:
        messages.append({"role": turn["role"], "content": turn["content"]})

    # Attach image to new question
    messages.append({
        "role":    "user",
        "content": english_question,
        "images":  [image_b64],
    })

    payload = {
        "model":    OLLAMA_MODEL,
        "messages": messages,
        "stream":   False,
    }

    try:
        response = requests.post(OLLAMA_CHAT_URL, json=payload, timeout=120)
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        raise RuntimeError("Could not connect to Ollama. Make sure it's running: `ollama serve`")
    except requests.exceptions.Timeout:
        raise RuntimeError("Ollama timed out responding to your question.")

    data  = response.json()
    reply = data.get("message", {}).get("content", "")
    if not reply:
        raise ValueError("Empty response from model.")
    
    # Translate reply back to user's language naturally
    if language != "English":
        reply = translate_text_natural(reply, language)
    
    return reply

# ─────────────────────────────────────────────
# TEXT-TO-SPEECH  (returns in-memory BytesIO)
# ─────────────────────────────────────────────
def text_to_audio_buffer(text: str, language: str = "English", slow: bool = False) -> io.BytesIO:
    """Convert text to audio in the specified language."""
    gtts_lang = LANGUAGES.get(language, {}).get("gtts", "en")
    tts = gTTS(text=text, lang=gtts_lang, slow=slow)
    buf = io.BytesIO()
    tts.write_to_fp(buf)
    buf.seek(0)
    return buf

def generate_summary_audio(result: dict, language: str = "English", slow: bool = False) -> io.BytesIO:
    return text_to_audio_buffer(result["quick_summary"], language, slow)

def generate_detailed_audio(result: dict, language: str = "English", slow: bool = False) -> io.BytesIO:
    return text_to_audio_buffer(result["detailed_readout"], language, slow)

def generate_full_audio(result: dict, language: str = "English", slow: bool = False) -> io.BytesIO:
    combined = f"{result['quick_summary']}. {result['detailed_readout']}"
    return text_to_audio_buffer(combined, language, slow)
