docker kill robot-gui && \
docker rm robot-gui && \
docker pull ambientlabsjose/robot-gui:latest && \
docker run -d --name robot-gui -p 9000:9000 ambientlabsjose/robot-gui:latest
