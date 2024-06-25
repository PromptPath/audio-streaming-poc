# Project Setup
## Only for MacOS
- Install homebrew via homebrew.sh and add it to the PATH
- Install python `brew install python@3.10` 
- Add python to path `echo 'export PATH="/opt/homebrew/opt/python@3.10/bin:$PATH"' >> ~/.zshrc`
- Activate virtual environment `source env/bin/activate`
- Install requirements `pip install -r requirements.txt`

# Run the project
- Install audio dependencies for `brew install portaudio`
- Use this command: `python3.10 microphone.py`
- See the terminal below.
- Once the conversation is ended, hit Enter.

# Check the results
- Login to NIO SBX
- Go to Testing Organization
- Go to Deepgram Dealer
- You should see all the conversations here once the execution is done.
