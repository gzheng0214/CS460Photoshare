CREATE DATABASE IF NOT EXISTS photoshare;
USE photoshare;
DROP TABLE IF EXISTS Pictures CASCADE;
DROP TABLE IF EXISTS Users CASCADE;

CREATE TABLE Users (
    user_id int4  AUTO_INCREMENT,
    email varchar(255) UNIQUE,
    password varchar(255),
    date_of_birth DATE,
    hometown varchar(255),
    gender varchar(255),
    CHECK (LENGTH(password) >= 4),
  CONSTRAINT users_pk PRIMARY KEY (user_id)
);

CREATE TABLE Pictures
(
  picture_id int4  AUTO_INCREMENT,
  user_id int4,
  imgdata longblob ,
  caption VARCHAR(255),
  INDEX upid_idx (user_id),
  CONSTRAINT pictures_pk PRIMARY KEY (picture_id)
);

CREATE TABLE Albums (
  album_id int4,
  user_id int4 NOT NULL,
  name varchar(255),
  date_of_creation DATE,
  PRIMARY KEY (album_id),
  FOREIGN KEY (user_id) REFERENCES Users(user_id)
);

CREATE TABLE Tags (
tag_label VARCHAR(255),
    CONSTRAINT tag_pk PRIMARY KEY ( tag_label ),
    CHECK (length( tag_label ) > 0)
);

CREATE TABLE Comments (
    comment_id int4 AUTO_INCREMENT,
    comment varchar(255) NOT NULL,
    user_id int4 NOT NULL,
    date DATE not null,
    PRIMARY KEY (comment_id),
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
);

CREATE TABLE has_tag (
    picture_id int4 NOT NULL,
    tag_label VARCHAR(255) NOT NULL,
    PRIMARY KEY (picture_id, tag_label),
    FOREIGN KEY (picture_id) REFERENCES Pictures(picture_id),
    FOREIGN KEY (tag_label) REFERENCES Tags(tag_label)
);

CREATE TABLE has_friends (
    user1 int4 NOT NULL,
    user2 int4 NOT NULL,
    PRIMARY KEY( user1, user2 ),
    FOREIGN KEY (user1) REFERENCES Users(user_id),
    FOREIGN KEY (user2) REFERENCES Users(user_id)
);

INSERT INTO Users (email, password) VALUES ('test@bu.edu', 'test');
INSERT INTO Users (email, password) VALUES ('test1@bu.edu', 'test');