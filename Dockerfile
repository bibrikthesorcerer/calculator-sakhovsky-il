FROM python:3.13-alpine

WORKDIR /calc_app

RUN apk add --no-cache gcc g++ musl-dev linux-headers make

COPY src/ src
COPY tests/ tests
COPY CalculatorApp/ CalculatorApp
COPY Makefile .

EXPOSE 8000

ENV PYTHONUNBUFFERED=1

RUN make venv-server

CMD ["make", "run-server-python"]