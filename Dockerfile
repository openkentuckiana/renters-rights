FROM python:3.7

RUN apt-get update && \
	apt-get install zlib1g-dev binutils libproj-dev gdal-bin libgeoip1 python-gdal -y && \
	apt-get install python3-pip git -y && \
	apt-get install build-essential python3-dev python3-pip python3-setuptools python3-wheel python3-cffi libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info -y && \
	pip3 install pipenv && \
	apt-get clean

RUN mkdir /app
WORKDIR /app

ADD Pipfile .
ADD Pipfile.lock .

# arg to pass to pipenv. useful for passing in `dev` when dev dependencies are needed.
ARG pipenv_arg=
RUN CC="cc -mavx2" pipenv install --system --skip-lock $pipenv_arg
#RUN pipenv install --system --skip-lock $pipenv_arg

ADD ./renters_rights/ /app

ENV DJANGO_SETTINGS_MODULE=renters_rights.settings.production

CMD /app/docker-entrypoint.sh