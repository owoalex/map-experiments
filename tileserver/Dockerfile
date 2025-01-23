FROM python:3.9.20-bookworm
WORKDIR /app
SHELL ["/bin/bash", "-c"]
RUN pip install psycopg2-binary zarr
COPY src /app
WORKDIR /app
ENTRYPOINT ["python3 main.py"]
STOPSIGNAL SIGQUIT
