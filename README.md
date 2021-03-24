# Table of Contents

- [Introudction](#Introduction)
- [API sample](#API)
- [Deployment](#Deployment)
- [Pipeline](#Pipeline)
- [Installation](#Installation)

# Intrudction

[Demo Video](https://youtu.be/F-TqHESV-i4).

A simple web-based app using Flask and PostgreSQL database that allows different users to:

- Register and login.
- Search and submit reviews on their favourite books.

# API

Make a GET request to `/api/<isbn>` to get a JSON response containing
book's title, author, publication year, ISBN number, review count, and average score.

```javascript
// JSON sample
{
    "title": "Memory",
    "author": "Doug Lloyd",
    "year": 2015,
    "isbn": "1632168146",
    "review_count": 28,
    "average_score": 5.0
}
```

# Deployment

The app is deployed to a self-hosted kubernetes cluster on AWS EC2, which is provisioned using ansible and AWS CloudFormation. All source files are found in the [deploy](deploy) dir.

# Pipeline

- A linting job is run on every commit or a pull request.
- Once linting job passes, that triggers a docker build job which builds and containerize the application and push the new built image to Dokcer Hub.
- New commits on the main branch triggers a deployment pipeline which provisions a simple cloudformation stack that has an EC2 instance for hosting the kubernetes cluster. Once infrastructure is up and running, a provision job is run which uses ansible to set up and deploy a k3s cluster using [Rancher's k3d](https://k3d.io/).

# Installation

## Requirements

- A postgres database. This project is using a Heroku-hosted database instance.
- [A Goodreads developer API Key](https://www.goodreads.com/api/documentation).
- Inject the PostgreSQL url and API key in your environment

```bash
export DATABASE_URL=<url-here>
export GOODREADS_API_KEY=<key-her>
```

## Using rancher's k3d

Make sure that k3d and docker is installed, then simply run the bootstrap script:

```bash
$ ./deploy/kube/bootstrap
```

## Using docker

Clone the repo and in the project root, run:

```bash
$ docker build -t book-reviews:latest .
$ docker run -d -p 5000:5000 \
    -e "DATABASE_URL=${DATABASE_URL}" -e "GOODREADS_API_KEY=${GOODREADS_API_KEY}" \
    book-reviews:latest
```

Navigate to [http://localhost:8000](http://localhost:8000), register and submit a review for your favorite book!
