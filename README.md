
# NLIP Kivy Client

Chat client built using Kivy and speaking NLIP protocol

- text
- images

![Mach2 Screenshot](imgs/mach2-1.png)

![Mach2 Screenshot the Second](imgs/mach2-2.png)


## Building

This project works well with `uv`.

1. Create a virtual environment.

        $ uv venv
    	$ . .venv/bin/activate
		
2. Synchronize the project dependencies

        $ uv sync
		
3. Run the app

        $ python kivy_chat_app.py
		

## Usage

By default, the app will connect to the server connection configured in the top input area.  You should enter a string like `http://localhost:8000`, where your NLIP server is listening.  Press `[RETURN]`.


## Testing and Development

Set the following flag to `True` to disable the NLIP server connection.

    USE_MOCK_SERVER = True
	
When set this way, the app will generate canned responses.  This can be helpful during development, when working on layout or design.


