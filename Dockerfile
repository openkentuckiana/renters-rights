FROM node:14.15.5-buster-slim AS webpack

WORKDIR /app

RUN apt-get update \
  && apt-get install -y build-essential curl libpq-dev --no-install-recommends \
  && rm -rf /var/lib/apt/lists/* /usr/share/doc /usr/share/man \
  && apt-get clean \
  && mkdir -p /node_modules && chown node:node -R /node_modules /app

USER node

COPY --chown=node:node ./renters_rights .

WORKDIR /app/assets

RUN yarn install

ARG NODE_ENV="production"
ENV NODE_ENV="${NODE_ENV}" \
    USER="node"

RUN if [ "${NODE_ENV}" != "development" ]; then \
  yarn run build; else mkdir -p /app/public; fi

CMD ["bash"]

FROM python:3.9.5 as app

RUN apt-get update && \
	apt-get install zlib1g-dev binutils libproj-dev gdal-bin libgeoip1 python-gdal -y && \
	apt-get install python3-pip git -y && \
	apt-get install build-essential python3-dev python3-pip python3-setuptools python3-wheel python3-cffi libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info gettext -y && \
	pip3 install pipenv && \
	apt-get clean

RUN mkdir /app
WORKDIR /app

ADD Pipfile .
ADD Pipfile.lock .

# arg to pass to pipenv. useful for passing in `dev` when dev dependencies are needed.
ARG pipenv_arg=
RUN pipenv install --system --skip-lock $pipenv_arg

ADD ./renters_rights/ /app

ENV DJANGO_SETTINGS_MODULE=renters_rights.settings.base
COPY --from=webpack /app/public/ /app/public/
RUN python manage.py collectstatic --noinput

ENV DJANGO_SETTINGS_MODULE=renters_rights.settings.production

CMD /app/docker-entrypoint.sh