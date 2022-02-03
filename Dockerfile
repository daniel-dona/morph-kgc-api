FROM ubuntu:20.04
RUN apt update
RUN apt install -y wget unzip zip nano curl python3 python3-pip

RUN mkdir /code /mapping /data /result

COPY ./requirements.txt /code/requirements.txt

RUN python3 -m pip install -r /code/requirements.txt

COPY ./ /code

CMD ["python3","/code/server.py"]
