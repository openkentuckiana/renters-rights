# Thanks to https://gist.github.com/miketheman/e17a9e5c6fedac4c34383931c01beb28

CURRENT_DIRECTORY := $(shell pwd)
GIT_SHA := $(shell git rev-parse HEAD)

help:
	@echo "Docker Compose Help"
	@echo "-----------------------"
	@echo ""
	@echo "Run tests to ensure current state is good:"
	@echo "    make test"
	@echo ""
	@echo "If tests pass, add fixture data and start up the app:"
	@echo "    make begin"
	@echo ""
	@echo "To start app (skipping image build and fixture installation):"
	@echo "    make start"
	@echo ""
	@echo "To stop app:"
	@echo "    make stop"
	@echo ""
	@echo "To stop and start app:"
	@echo "    make restart"
	@echo ""
	@echo "To rebuild images (needed after adding dependency):"
	@echo "    make build"
	@echo ""
	@echo "Reset container database and volumes:"
	@echo "    make clean"
	@echo ""
	@echo "Attach to running Django app:"
	@echo "    make attach"
	@echo ""
	@echo "See contents of Makefile for more targets."

begin: build makemigrations migrate fixtures start
	git config core.hooksPath .githooks

start:
	@docker-compose up -d
	@echo "Ready at http://localhost/"

stop:
	@docker-compose stop

status:
	@docker-compose ps

restart: stop start

restart-app:
	@docker-compose stop app
	@docker-compose up -d
	@echo "Ready at http://localhost/"

clean: stop
	@docker-compose rm --force
	@docker-compose down --volumes
	@find . -name \*.pyc -delete

build:
	@docker-compose build app

collectstatic:
	@docker-compose run --rm app python ./manage.py collectstatic

test: 
	@docker-compose run -e DJANGO_SETTINGS_MODULE=renters_rights.settings.test --rm app ./wait-for-it.sh db:5432 --timeout=60 -- python ./manage.py test --keepdb $(labels)

testwithcoverage:
	@docker-compose run -e DJANGO_SETTINGS_MODULE=renters_rights.settings.test --rm app bash -c "./wait-for-it.sh db:5432 --timeout=60 -- coverage run --source='.' ./manage.py test --keepdb --noinput && coverage html"

testwithcoverage-codecov: build
	@docker-compose run -e DJANGO_SETTINGS_MODULE=renters_rights.settings.test -e GIT_SHA=$(GIT_SHA) -e CODECOV_TOKEN=$(CODECOV_TOKEN) --rm app bash -c "./wait-for-it.sh db:5432 --timeout=60 -- coverage run --source='.' ./manage.py test --keepdb --noinput && codecov --commit=$(GIT_SHA)"

makemigrations:
	@docker-compose run --rm app ./wait-for-it.sh db:5432 --timeout=60 -- python ./manage.py makemigrations

makemessages:
	@docker-compose run --rm app ./wait-for-it.sh db:5432 --timeout=60 -- python ./manage.py makemessages -l es

compilemessage:
	@docker-compose run --rm app ./wait-for-it.sh db:5432 --timeout=60 -- python ./manage.py compilemessages

migrate:
	@docker-compose run --rm app ./wait-for-it.sh db:5432 --timeout=60 -- python ./manage.py migrate

fixtures:
	@docker-compose run --rm app ./wait-for-it.sh db:5432 --timeout=60 -- ./load-all-fixtures.sh

flushdb:
	@docker-compose run --rm app ./wait-for-it.sh db:5432 --timeout=60 -- python ./manage.py flush

bash:
	@docker-compose run --rm app bash

tail:
	@docker-compose logs -ft

tail-app:
	@docker-compose logs -ft app

attach:
	docker attach renters-rights_app_1

bash-running:
	docker exec -it renters-rights_app_1 bash

format:
	@docker-compose run --rm app black . -l 128
	@docker-compose run --rm app isort -rc --atomic .

.PHONY: start stop status restart clean build test makemigrations migrate fixtures flushdb cli tail