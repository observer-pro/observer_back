# IDE Observer (Backend)

The Observer App is a real-time chat application based on Sockets that allows users to create and join rooms, chat with other participants, and observe their activities in different rooms. 

Backend is built on python-socketio.

## Features:
- Create and host chat rooms.
- Join/Leave existing chat rooms as participants.
- Users can send and receive messages in their rooms.
- Participants are notified when someone joins or leaves the room.

## Installation:
- Clone the repository to your local machine `git clone <repository_url>`
- Create and activate a virtual environment (optional but recommended) `python3 -m venv venv`
`source venv/bin/activate`
- Install the required packages `pip install -r requirements.txt`

## Usage:
- Run the app `python main.py`

[//]: # (**Server-side Socket Events:**)

[//]: # (- **connect**: Triggered when a user connects to the server.)

[//]: # (- **disconnect**: Triggered when a user disconnects from the server.)

[//]: # (- **host**: Triggered when a user hosts a new room.)

[//]: # (- **join**: Triggered when a user joins an existing room.)

[//]: # (- **leave**: Triggered when a user leaves a room.)

[//]: # (- **message**: Triggered when a user sends a message in a room.)

[//]: # (- )

[//]: # (**Client-side Socket Events:**)

[//]: # (- **room_data**: Sent by the server in response to host and join events, provides room data including room ID, name, host, and participants.)

[//]: # (- **message**: Sent by the server in response to the message event, contains the message text.)

[//]: # ()
[//]: # (## API Endpoints:)

[//]: # ()
[//]: # (The application also provides API endpoints to fetch the list of active rooms and their participants.)

[//]: # ()
[//]: # (**GET /api/room**: Retrieves a list of all active rooms and their participants.)

[//]: # (**GET /api/users**: Retrieves a list of all users with names and roles.)

[//]: # ()
[//]: # (![GET examples]&#40;https://habrastorage.org/webt/9o/e7/w7/9oe7w7fmisaseozbwxzdsb2wjxy.png&#41;)

[//]: # ()
[//]: # (## Tests:)

[//]: # ()
[//]: # (Testing was performed manually using Postman. It involved creating rooms by hosts, connecting users to rooms, leaving rooms, and sending messages.)

[//]: # ()
[//]: # (![Testing]&#40;https://habrastorage.org/webt/pf/2x/z1/pf2xz15zbu9hzxwrbyusasqeng0.jpeg&#41;)