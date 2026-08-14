# orthanc-pygraphql

**orthanc-pygraphql** is a GraphQL API endpoint for [Orthanc](https://www.orthanc-server.com/), the lightweight, RESTful DICOM server. It runs as a script using the [Orthanc Python Plugin](https://orthanc.uclouvain.be/book/plugins/python.html) and uses [Ariadne](https://ariadnegraphql.org/) to process GraphQL queries.

It allows you to query your Orthanc server using GraphQL instead of the standard REST API, letting you request exactly the data you need.

## Features

- **Native Orthanc Integration:** Runs directly inside Orthanc via the Python Plugin.
- **GraphQL API:** Exposes a `/graphql` endpoint to query Orthanc resources.
- **Patients Query:** Fetch patient records natively from Orthanc.

## Installation / Usage

The easiest way to run the project is using Docker.

1. Clone this repository.
2. Run `docker-compose up --build`.
3. Orthanc will be available on port `8042`.

## Example Query

Once running, you can send a POST request with your GraphQL query to `http://localhost:8000/graphql`. (Note: The default `docker-compose.yml` maps port 8042 inside the container to port 8000 on your host machine, using basic auth credentials `demo:demo`).

```bash
curl -u demo:demo -X POST \
  http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "query { patients { id patientId patientName patientSex patientBirthDate } }"}'
```

## Running Tests / CI

This project enforces Google Style guide formatting using `yapf` and runs static analysis via `pylint`. A GitHub Actions pipeline automatically rejects code that fails validation tests or crashes during the Docker build.

To validate your code locally:
```bash
pip install yapf pylint
yapf --diff --style google --recursive orthanc/python/
pylint orthanc/python/
```

## Contributing

We welcome contributions from the community!

1. Fork the repository
2. Create a new branch (`git checkout -b feature/awesome-feature`)
3. Make your changes
4. Ensure code formatting is correct (`yapf --in-place --style google --recursive orthanc/python/`)
5. Submit a pull request!

Please assure your pull request descriptions are clear and include what dependencies (if any) you add to the Dockerfile.

## Licensing

This project is licensed under the GNU Affero General Public License v3.0 (AGPLv3) to comply with the official Orthanc Python Plugin licensing terms. 

Per the AGPLv3 requirements, if you run an Orthanc server equipped with this script on a Web portal or distribute it to clients, you must disclose the source code of your configuration and scripts under the same license terms.
