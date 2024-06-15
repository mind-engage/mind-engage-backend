FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app

# Environment variables
ENV NVIDIA_API_KEY=""
ENV LANGCHAIN_API_KEY=""
ENV OPENAI_API_KEY=""

EXPOSE 8080

CMD ["python", "-m", "servers.query_server"]