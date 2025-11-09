# Check container status
docker ps -a | grep sworms-lite

# Check logs
docker logs sworms-lite-main

# Execute commands in container
docker exec -it sworms-lite-main bash