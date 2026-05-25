FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY ["PTReadinessQuestions-01-10_with ab2.xlsx", "."]

ENV SURVEY_CSV=/app/PTReadinessQuestions-01-10_with\ ab2.xlsx

EXPOSE 8050

CMD [ "python", "app.py"]