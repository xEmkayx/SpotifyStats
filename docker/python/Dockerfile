# base image
# FROM python:3.10-alpine
# FROM python:3.8-alpine
FROM python:3.9
# WORKDIR /usr/app/src

# RUN mkdir SpotifyStats
# COPY ./../../../Spotify_Stats ./
COPY . ./SpotifyStats

# RUN apk update && apk add git && \
    # apk add vim && apk add nano && \
    # apk add curl # && apk add bash
# RUN apk add --no-cache mysql-client

RUN python -m pip install --upgrade pip && \
    cd SpotifyStats && \
    # cat requirements.txt | cut -f1 -d"#" | sed '/^\s*$/d' | xargs -n 1 pip install
    # pip install --only-binary=:all: -r requirements.txt
    # xargs -n 1 -a requirements.txt pip install --only-binary=:all:
    # cat requirements.txt | xargs -n 1 pip install
    python -m pip install -r requirements.txt

# ENTRYPOINT ["/bin/sh"]
# ENTRYPOINT ["python"]
CMD ["python", "./SpotifyStats/test.py"]
# CMD tail -f /dev/null