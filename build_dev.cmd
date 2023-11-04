docker container rm devtest
docker image rm lmulot/pibot:dev
docker build -t lmulot/pibot:dev .
docker run --rm -ti --name devtest -v %cd%:/app lmulot/pibot:dev

