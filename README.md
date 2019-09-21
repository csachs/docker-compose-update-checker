# docker-compose-update-checker

A tiny container you can use to check if any of the images used in your `docker-compose.yml` might have updates available.
 (No guarantees it will properly find them!)
 
## Usage

```bash
> docker run --rm -v `pwd`/docker-compose.yml:/docker-compose.yml:ro csachs/docker-compose-update-checker
```

## Usage as a sub-service in `docker-compose`

You can as well directly define everything as a service in your `docker-compose.yml`:
```yaml
services:
  update-check:
    image: csachs/docker-compose-update-checker
    restart: "no"
    volumes:
      - ./docker-compose.yml:/docker-compose.yml:ro
```
And then simply run it to check your local `docker-compose.yml`:
```bash
> docker-compose run --rm update-check
```