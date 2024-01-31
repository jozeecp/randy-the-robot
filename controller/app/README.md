# Robot Controller App


## API

### Examples

#### Spiral

Request body

```json
{
  "amount_of_steps": 150,
  "radius": 0.05,
  "height": 0.2,
  "amount_of_turns": 3,
  "clockwise": true
}
```

cURL

```bash
curl -X 'PUT' \
  'http://localhost:8020/run_example/spiral' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "amount_of_steps": 150,
  "radius": 0.05,
  "height": 0.2,
  "amount_of_turns": 3,
  "clockwise": true
}'
```


#### Swing

Request body 

```json
{
  "amount_of_steps": 175,
  "radius": 0.1,
  "height": 0.3,
  "amount_of_turns": 3
}
```

cURL

```bash
curl -X 'PUT' \
  'http://localhost:8020/run_example/swing' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "amount_of_steps": 175,
  "radius": 0.1,
  "height": 0.3,
  "amount_of_turns": 3
}'
```

#### Square

Request body 

```json
{
  "amount_of_steps": 50,
  "height": 0.1,
  "side_length": 0.6
}
```

cURL

```bash
curl -X 'PUT' \
  'http://localhost:8020/run_example/square' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "amount_of_steps": 50,
  "height": 0.1,
  "side_length": 0.6
}'
```


## Building and deploying

```bash
docker kill robot-controller && \
docker rm robot-controller && \
docker pull ambientlabsjose/robot-controller:latest && \
docker run -d --name robot-controller -p 8020:8020 -e REDIS_HOST=172.17.0.7 ambientlabsjose/robot-controller:latest
```
