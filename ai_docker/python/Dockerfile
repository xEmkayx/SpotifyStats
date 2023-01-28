FROM python:3.10

# copy the package and its dependencies
COPY . /Spotify_Stats/
# COPY requirements.txt .
RUN pip install -r /Spotify_Stats/requirements.txt

# environment variables for connecting to the mysql container
ENV MYSQL_HOST=mysql
ENV MYSQL_USER=spotify
ENV MYSQL_PASSWORD=admin
ENV MYSQL_DATABASE=spotify_stats

# run the script
CMD ["python", "/Spotify_Stats/main.py"]

