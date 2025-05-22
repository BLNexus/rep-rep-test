FROM python:3.10-slim

RUN apt-get update && apt-get install -y libpq-dev

RUN pip install --upgrade pip
RUN pip install psycopg2-binary

WORKDIR /app

COPY . /app

RUN pip install -r requirements.txt

CMD ["python", "mtrepo.py"]
