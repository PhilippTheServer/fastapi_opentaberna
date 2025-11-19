Repo to the FastAPI of the OpenTaberna Project. See [Wiki](https://wiki.opentaberna.de) for more information.


# Coding Guidlines

**Tooling**
- Python 3.14
- uv package manager 0.4.0
- Docker
- Ruff 0.14.5

# Pipelines

This FastAPI can be build and tested via GitHub workflows. There are two available workflows:
1. test.yml -> to test the API
2. test-build-deploy.yml -> runs pytest for minor checks and builds the docker image.

## test.yml

This Pipeline is can be triggered either by merging a PR into main or run it manually in the Repository Action section.

The workflow tests for:
1. System Integration
2. Pytest
3. Linter and Formatter
4. Trivy checks dependencys
5. Bandit to audit the code

All results are uploaded as Artifacts.

## test-build-deploy.yml

This workflow runs small pytests before it builds the docker image for the API. After a successful build the image gets pushed into the organizations docker registry. The last Job deploys the whole `docker-compose.yml` in the root directory to a Portainer instance.

The workflow can be triggerd by a tag on any commit:

```bash
git tag vX.X.X && git push origin vX.X.X
```

> [!CAUTION]
> The workflow only tells if a deployment started on portainer. It can not detect if the API container or any other container fails on start as long as the container gets marked as "running".

