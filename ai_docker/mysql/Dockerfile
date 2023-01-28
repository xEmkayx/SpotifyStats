FROM mysql:8

# copy the sql dump file
COPY /ai_docker/mysql/db.sql /docker-entrypoint-initdb.d/

# environment variables for configuring mysql
ENV MYSQL_ROOT_PASSWORD=root
ENV MYSQL_DATABASE=spotify_stats
ENV MYSQL_USER=spotify
ENV MYSQL_PASSWORD=admin
