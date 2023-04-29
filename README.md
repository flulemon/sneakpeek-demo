# Sneakpeek Usage Demo

Demo project for [Sneakpeek framework](https://github.com/flulemon/sneakpeek).

# How to run locally

Install dependencies ([Poetry](https://python-poetry.org/) is required):

```bash
poetry install
```

Run handler locally:

```bash
poetry run debug-handler
```

Run server:

```bash
poetry run app
```

Open http://localhost:8080

# Run in Docker

Build image:

```bash
docker build -t sneakpeek-demo:latest .
```

Run the image:

```bash
docker run -it -p 8080:8080 --rm sneakpeek-demo:latest
```

Open http://localhost:8080
