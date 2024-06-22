

# MindEngage Backend

## Introduction
MindEngage Backend serves as the server-side application for the MindEngage educational platform. It is built using Flask and is designed to handle API requests, session management, and dynamic content delivery powered by NVIDIA's NIM Generative AI and LangGraph knowledge query pipelines.

## Features
- API endpoints for quizzes, session management, and user interactions
- Integration with NVIDIA's NIM Generative AI for dynamic quiz generation
- Utilization of LangGraph for structured knowledge querying
- Session management and logging of user performance stats

## Architecture Overview
![Archotecture](./docs/SocraticLearningAgentOverview.png)

## Directory Structure

- **/agents**: Contains Python modules implementing the Generative AI Agents. query_agent for user interaction, course_agent for teacher interaction.
- **/cli**: Command-line interface utilities to interact with the services.
- **/docs**: Documentation files and images for the project.
- **/servers**: Server-side scripts to handle API requests.
- **/tests**: Unit tests for the project modules.
- **/topic_embeddings**: Sample topic embedding models.
- **/quiz.db**: A SQLite database file containing cached sample quiz data.
## Getting Started

### Prerequisites
- Python 3.10 or newer
- Flask
- Virtual environment (Conda recommended)

### Installation
1. Clone the repository:
```bash
git clone https://github.com/mind-engage/mind-engage-backend.git
```
2. Navigate to the project directory:
```bash
cd mind-engage-backend
```
3. Install python3.10 or above and pip

5. Install required packages
```
pip install -r requirements.txt
```

## Usage

Export API Keys
```
export NVIDIA_API_KEY=<API KEY>
export LANGCHAIN_API_KEY=<API KEY>
```
To start the Query Agent server:
```bash
python -m servers.query_server
```
This will start the Flask server on `http://localhost:8080`. The API can now respond to requests from the mobile front-end.

To start the Course Agent server:
```bash
python -m servers.course_server
```
This will start the Flask server on `http://localhost:5000`. The API can now respond to requests from the mobile front-end.

## Using Docker

### Build the docker image
```
docker build -t mind-engage-api .
```

### Using Docker for quirey_agent

Run the docker image for local testing.
Map the quiz.db for persisting the new session data.
```
docker run -e NVIDIA_API_KEY=<API_KEY> -v $PWD/quiz.db:/app/quiz.db -p 8080:8080 -it mind-engage-api
```

### Using Docker for course_agent

Run the docker image for local testing.
Map the quiz.db, topic_embeddings for persisting the new session data. Default command of the container is overrided with course_agent
```
docker run -e NVIDIA_API_KEY=<API_KEY> -v $PWD/quiz.db:/app/quiz.db -v $PWD/topic_embeddings:/app/topic_embeddings -p 8080:8080 -it mind-engage-api python -m servers.course_server
```

## Contributing
We welcome contributions from everyone. To contribute:
1. Fork the repository.
2. Create your feature branch (`git checkout -b feature/YourFeature`).
3. Commit your changes (`git commit -m 'Add some YourFeature'`).
4. Push to the branch (`git push origin feature/YourFeature`).
5. Open a Pull Request.

## License
This project is licensed under the MIT License - see the `LICENSE` file for details.

## Contact
- Project Link: [https://github.com/mind-engage/mind-engage-backend](https://github.com/mind-engage/mind-engage-backend)

## Acknowledgments
- NVIDIA for NIM Generative AI Inference
- LangGraph knowledge pipeline
- All contributors who have helped develop and maintain this project.
