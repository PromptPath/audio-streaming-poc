# Project Setup
## MacOS only
- Install homebrew via homebrew.sh and add it to the PATH
- Install python `brew install python@3.10` 
- Add python to path `echo 'export PATH="/opt/homebrew/opt/python@3.10/bin:$PATH"' >> ~/.zshrc`
- Create a virtual environment. i.e `python3.10 -m venv env`
- Activate the virtual environment `source env/bin/activate`
- Install requirements inside the virtual environment `pip install -r requirements.txt`
- Install audio dependencies for `brew install portaudio`

# Run the project
- Use this command: `python3.10 microphone.py`
- See the terminal below.
- Once the conversation is ended, hit Enter.

# Check the results
- Login to NIO SBX
- Go to Testing Organization
- Go to Deepgram Dealer
- You should see all the conversations here once the execution is done.
