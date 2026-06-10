# Sight-to-Speech 
An open-source AI assistive technology prototype built for UN SDG 3 (Good Health & Well-being) to help visually impaired individuals interact with everyday objects.

## Features
- Reads image text and analyzes spatial context using Ollama (LLaVA).
- Generates multi-language spoken descriptions (gTTS).
- Allows users to ask follow-up questions via text or voice.

## How to Run
1. Install dependencies: `pip install -r requirements.txt`
2. Start Ollama: `ollama serve` and `ollama pull llava`
3. Launch the app: `streamlit run app.py`
