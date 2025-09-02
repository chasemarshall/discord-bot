FROM python:3.12-slim

WORKDIR /app

# Install dependencies first (better Docker layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir --quiet -r requirements.txt

# Copy the application code
COPY main.py .

# Add a simple test to verify OpenAI import works
RUN python -c "import openai; print('OpenAI import successful')"

CMD ["python", "main.py"]