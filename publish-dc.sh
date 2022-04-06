#!/bin/bash
set -e

docker login -u "$DOCKER_USERNAME" -p "$DOCKER_PASSWORD" registry.vapronva.pw
docker pull registry.vapronva.pw/websites/fs_geoxoplace_vapronva_pw-website:latest
docker-compose -f 'docker-compose.yml' --project-name 'w-geoxorplacevapronvapw' down
docker-compose -f 'docker-compose.yml' --project-name 'w-geoxorplacevapronvapw' up -d
