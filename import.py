#!/usr/bin/python3.6

import os
import csv
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

# set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


def main():
    with open("books.csv") as f:
        reader = csv.reader(f)
        isFirstLine = True

        for isbn, title, author, year in reader:
            if isFirstLine:  # skip the first line in the csv file
                isFirstLine = False
                continue

            db.execute(
                "INSERT INTO books(isbn, title, author, year \
                VALUES (:isbn, :title, :author, :year)",
                {"isbn": isbn, "title": title, "author": author, "year": year},
            )
            print(f"Added book: {isbn}, {title}, {author}, {year}")

    db.commit()


if __name__ == "__main__":
    main()
