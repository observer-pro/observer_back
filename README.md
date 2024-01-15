# IDE Observer (Backend)

The Observer App is a real-time chat application built on the concept of WebSocket communication, that allows users to
create and join rooms, chat and share their code with teacher.

Backend is built on **python-socketio**.

![Observer](https://habrastorage.org/webt/ii/rt/u6/iirtu6stfynhos1m1bwekdms6vu.jpeg)
![Settings](https://habrastorage.org/webt/_h/-w/c_/_h-wc_xic8sdbqot6i1mf_adbs8.png)

## Features

- Hosts (teachers) can create new chat rooms, providing a platform for collaboration and communication.
- Users can join or leave existing chat rooms as participants (students and teacher).
- Students and teacher can send and receive messages in their rooms.
- Participants can reconnect to a room if they temporarily lose connection, ensuring continuity in communication.
- Teachers can initiate and terminate code sharing sessions, allowing participants to collaborate on code in real-time.
- Students can send files (code snippets, documents) to the teacher during code sharing sessions, promoting efficient
  collaboration.

## Installation and Run

- Clone the repository to your local machine `git clone git@github.com:bendenko-v/IDE_Observer.git`
- Create and activate a virtual environment (optional but recommended) `python3 -m venv venv`
  `source venv/bin/activate`
- Install the required packages `pip install -r requirements.txt`
- Run the app `uvicorn src.main:app --host 0.0.0.0 --port 8000`

## Usage

### Events:

**Room Creation and Connection:**

- `room/create`: Create a room. Sent by the host, a room is created, and data about the room is sent in
  the `room/update` event.
- `room/rehost`: Reconnect a teacher to the room.
- `room/join`: Join an existing room. Users connects to a room and receive `room/join` in response, containing their
  data.
- `room/rejoin`: Reconnect a student to the room.
- `room/kill`: Force user disconnect.
- `room/close`: Close the room by the host. Students got the `room/closed` event, notifying about room closure.

**Message Exchange:**

- `message/to_client`: Send a message from the teacher to the student.
- `message/to_mentor`: Send a message from the student to the teacher.
- `message/user`: Get messages from/to user.
- `message`: Information messages

**Collaborative Usage Control:**

- `settings`: Transmitting configuration settings.
- `sharing/start`: Initiates code sharing.
- `sharing/end`: End code sharing.
- `sharing/code_send`: Sends files to the host.
- `sharing/code_update`: Sends updated files to the host after making changes.
- `steps/all`: Sends tasks to all students.
- `steps/status/to_mentor`: Sends statuses about tasks from a student to a teacher.
- `steps/status/to_client`: Sends statuses about the acceptance of tasks by the teacher.
- `steps/import`: Imports task data from a Notion document by URL.
- `steps/table`: Retrieves data with the results of all students.
- `exercise`: Distributes the task content from the teacher to all students in the
  room. ![maintenance-status](https://img.shields.io/badge/event-deprecated-red.svg)
- `exercise/feedback`:Teacher sends accepts or rejects an exercise submitted by a
  student. ![maintenance-status](https://img.shields.io/badge/event-deprecated-red.svg)
- `exercise/reset`: Teacher to reset the accepted/rejected statuses of their
  exercises. ![maintenance-status](https://img.shields.io/badge/event-deprecated-red.svg)

- `signal`: Allows students to send signals to the teacher indicating their current status (e.g., inaction, in progress,
  help needed, ready). ![maintenance-status](https://img.shields.io/badge/event-deprecated-red.svg)

**Alerts:**

- `alerts`: Sends alerts with one of the statuses: INFORMATION, SUCCESS, WARNING and ERROR.

### HTTP Endpoints:

**Room Statistics:**
- `/roomstats/{room_id}`: Shows student results live


## Links

[💻 observer-app.pro](https://observer-app.pro/)
