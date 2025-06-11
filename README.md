
## Prerequisites

- Install `uv`: https://docs.astral.sh/uv/getting-started/installation/
- Install `docker`: https://docs.docker.com/engine/install/
- Create a .env file in the root of your project and copy in the contents of the default.env file, then fill in your spiri-gitea username and token
    - A gitea access token can be generated on gitea by clicking on your profile picture -> Settings -> Applications, naming a token and giving it read permissions for both packages and repos, then hitting Generate Token, and copying the resulting token printed at the top of the page

## Quickstart

```bash
uv run python -m spiriSdk.main #Run the main code
uv run pytest #Run tests
docker compose up --build #Run in docker
```
