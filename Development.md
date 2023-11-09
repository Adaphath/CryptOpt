# How to develop
Follow normal docker installation. Start docker container with binds to src/ and dist/:
`docker run -v $(pwd)/results:/root/CryptOpt/results -v $(pwd)/src:/root/CryptOpt/src --name CryptOpt -ti cryptopt zsh`

Inside container: `make watch`

Connect in another terminal to the container: `docker exec -it CryptOpt /bin/zsh` and execute CryptOpt from there