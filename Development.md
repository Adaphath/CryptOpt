# How to develop
Follow normal docker installation. Start docker container with binds to src/ and dist/:
`docker run -v $(pwd)/src:/root/CryptOpt/src -v $(pwd)/dist:/root/CryptOpt/dist --name CryptOpt -ti cryptopt zsh`

Inside container: `make watch`

Connect in another terminal to the container: `docker exec -it CryptOpt /bin/zsh` and execute CryptOpt from there