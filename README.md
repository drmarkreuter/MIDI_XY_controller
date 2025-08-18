# MIDI_XY_controller
A python programme to send MIDI CC data using an XY pad

This python programme uses PyGame to create an XY pad that sends MIDI CC messages. This could be used to control synthesizers or virtual instruments within a DAW

## Setup
1. Create virtual environment: `python -m venv midi_controller_env`
2. Activate environment: `source midi_controller_env/bin/activate` (Mac/Linux) or `midi_controller_env\Scripts\activate` (Windows)
3. Install dependencies: `pip install -r requirements.txt`
4. Run: `python MIDI_XY_controller.py`

## Features
- XY pad for mouse/trackpad control
- Customizable MIDI CC numbers
- MIDI device and channel selection
- Real-time MIDI output
