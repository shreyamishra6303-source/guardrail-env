FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install uv && \
    uv pip install --system .
EXPOSE 7860
CMD ["python", "-m", "server.app"]
