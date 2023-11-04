docker image rm lmulot/pibot:latest
docker tag lmulot/pibot:%1 lmulot/pibot:latest
docker push lmulot/pibot:latest
docker push lmulot/pibot:%1

