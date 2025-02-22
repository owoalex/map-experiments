FROM python:3.9.20-bookworm
WORKDIR /app
SHELL ["/bin/bash", "-c"]
RUN pip install flask gunicorn requests pillow drawsvg[all] lxml SQLAlchemy psycopg2-binary
RUN apt install libcairo2
COPY src /app
WORKDIR /app
RUN mkdir -p cache/temp
ENTRYPOINT ["gunicorn -w 4 -b 0.0.0.0 'main:app'"]
STOPSIGNAL SIGQUIT
