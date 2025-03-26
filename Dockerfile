FROM python:3.13-slim

WORKDIR /calc_app

# copy the requirements file first and install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# install make
RUN apt-get update && apt-get install -y build-essential

COPY src/ src
COPY tests/ tests
COPY calc_server.py .
COPY Makefile .

EXPOSE 8000

ENV PYTHONUNBUFFERED=1

# run server app via Makefile
CMD ["make", "run-server-python"]