#FROM maven:3.8.6-jdk-11 AS build
#COPY src /home/app/src
#COPY pom.xml /home/app
#RUN mvn -f /home/app/pom.xml clean package -P flink-runner

FROM us-central1-docker.pkg.dev/endless-matter-387302/openlang/server-base-image:latest
COPY . /app
WORKDIR /app
RUN apk add gcc musl-dev libffi-dev
RUN apk add alpine-sdk
RUN pip install -r requirements.txt
ENTRYPOINT [ "python" ]
CMD ["main.py" ]
