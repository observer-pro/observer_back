# IDE Observer (Backend)

The Observer App is a real-time chat application built on the concept of WebSocket communication, that allows users to create and join rooms, chat and share their code with teacher.

Backend is built on **python-socketio**.

## Features:
- Hosts (teachers) can create new chat rooms, providing a platform for collaboration and communication.
- Users can join or leave existing chat rooms as participants (students and teacher).
- Students and teacher can send and receive messages in their rooms.
- Participants can reconnect to a room if they temporarily lose connection, ensuring continuity in communication.
- Teachers can initiate and terminate code sharing sessions, allowing participants to collaborate on code in real-time.
- Students can send files (code snippets, documents) to the teacher during code sharing sessions, promoting efficient collaboration.

## Installation and Run:
- Clone the repository to your local machine `git clone git@github.com:bendenko-v/IDE_Observer.git`
- Create and activate a virtual environment (optional but recommended) `python3 -m venv venv`
`source venv/bin/activate`
- Install the required packages `pip install -r requirements.txt`
- Run the app `python3 main.py`

## Usage:

### Events:
**Room Creation and Connection:**

- `room/create`: Create a room. Sent by the host, a room is created, and data about the room is sent in the `room/update` event.
- `room/rehost`: Reconnect a teacher to the room.
- `room/join`: Join an existing room. Users connect to a room and receive `room/join` in response, containing their data.
- `room/rejoin`: Reconnect a student to the room.
- `room/close`: Close the room by the host. Students got the `room/closed` event, notifying about room closure.

**Message Exchange:**

- `message/to_client`: Send a message from the teacher to the student.
- `message/to_mentor`: Send a message from the student to the teacher.
- `message`: Information messages

**Collaborative Usage Control:**

- `sharing/start`:  Start code sharing.
- `sharing/end`: End code sharing.
- `sharing/code_send`: Send files to the host.
- `sharing/code_update`: Send files after changes to the host.

**Additional Events:**

- `log`:  Event logging.
- `error`: Error messages.
