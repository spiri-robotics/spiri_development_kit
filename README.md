
## Prerequisites

- Install `uv`: https://docs.astral.sh/uv/getting-started/installation/
- Install `docker`: https://docs.docker.com/engine/install/
- Create a .env file and copy in the contents of the default.env file, then fill in your spiri-gitea name and token

## Quickstart

```bash
uv run python -m spiriSdk.main #Run the main code
uv run pytest #Run tests
docker compose up --build #Run in docker
```
