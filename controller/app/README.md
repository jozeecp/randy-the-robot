# Robot Controller App


## Building and deploying

```bash
docker kill robot-controller && \
docker rm robot-controller && \
docker pull ambientlabsjose/robot-controller:latest && \
docker run -d --name robot-controller -p 8020:8020 -e REDIS_HOST=172.17.0.7 ambientlabsjose/robot-controller:latest
```
