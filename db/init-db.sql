CREATE DATABASE IF NOT EXISTS `spotify_stats` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci */;
USE spotify_stats;

-- spotify_stats.artists definition

CREATE TABLE `artists` (
  `artist_id` varchar(100) NOT NULL,
  `artist_name` varchar(500) DEFAULT NULL,
  PRIMARY KEY (`artist_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- spotify_stats.albums definition

CREATE TABLE `albums` (
  `album_id` varchar(100) NOT NULL,
  `album_name` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`album_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- spotify_stats.songs definition

CREATE TABLE `songs` (
  `song_id` varchar(100) NOT NULL,
  `song_name` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `album_id` varchar(100) NOT NULL,
  `song_length` varchar(20) NOT NULL,
  PRIMARY KEY (`song_id`),
  KEY `songs_ibfk_1` (`album_id`),
  CONSTRAINT `songs_ibfk_1` FOREIGN KEY (`album_id`) REFERENCES `albums` (`album_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='wird nicht mehr benutzt!';

-- spotify_stats.stream_history definition

CREATE TABLE `stream_history` (
  `played_at` varchar(100) NOT NULL,
  `song_id` varchar(100) NOT NULL,
  PRIMARY KEY (`played_at`),
  KEY `sh_ibfk_1` (`song_id`),
  CONSTRAINT `sh_ibfk_1` FOREIGN KEY (`song_id`) REFERENCES `songs` (`song_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- spotify_stats.album_artists definition

CREATE TABLE `album_artists` (
  `album_id` varchar(100) NOT NULL,
  `artist_id` varchar(100) NOT NULL,
  PRIMARY KEY (`album_id`,`artist_id`),
  KEY `album_artists_ibfk_1` (`album_id`),
  CONSTRAINT `album_artists_ibfk_1` FOREIGN KEY (`album_id`) REFERENCES `albums` (`album_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `album_artists_ibfk_2` FOREIGN KEY (`artist_id`) REFERENCES `artists` (`artist_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- spotify_stats.art_songs definition

CREATE TABLE `art_songs` (
  `song_id` varchar(100) NOT NULL,
  `artist_id` varchar(100) NOT NULL,
  PRIMARY KEY (`artist_id`,`song_id`),
  KEY `song_id` (`song_id`),
  CONSTRAINT `art_songs_ibfk_1` FOREIGN KEY (`artist_id`) REFERENCES `artists` (`artist_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `art_songs_ibfk_2` FOREIGN KEY (`song_id`) REFERENCES `songs` (`song_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

