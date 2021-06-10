import os
import glob
import requests
from bs4 import BeautifulSoup
from tinydb import TinyDB

with open("./db.json", "w") as fp:
    pass

DB = TinyDB("./db.json")
HOST = "https://batotoo.com"
SESSION = requests.Session()


def browse_pages(skip_saved=False):
    if not os.path.exists("./browse"):
        os.mkdir("browse")

    PAGE = 1
    MAX_PAGE = 1431
    IDENTIFIER = "Browse - Bato.To"

    while PAGE < MAX_PAGE:
        if skip_saved:
            if PAGE < len(glob.glob("./browse/*.html")):
                PAGE += 1
                continue

        print(f"BROWSE: {PAGE} of {MAX_PAGE}")
        response = SESSION.get(f"{HOST}/browse?page={PAGE}")
        soup = BeautifulSoup(response.text, "html.parser")
        if soup.title.get_text() == IDENTIFIER:
            file_path = "./browse/{PAGE}.html"
            file = open(file_path, "w")
            file.write(response.text)
            file.close()
            browse_series(file_path)
            PAGE += 1
        else:
            print(f"BOT DETECTED: {soup.title.get_text()}")
            break


def browse_series(file_path):
    if not os.path.exists("./series"):
        os.mkdir("series")

    html = open(file_path, "r").read()
    soup = BeautifulSoup(html, "html.parser")
    titles = soup.find_all("a", class_="item-title")

    for title in titles:
        filename = " ".join(title
                            .findAll(text=True, recursive=False)[0]
                            .split('/'))

        response = SESSION.get(f"{HOST}{title['href']}")
        soup = BeautifulSoup(response.text, "html.parser")

        if title.get_text() in soup.title.get_text():
            print(f"TITLE: {filename}")
            series_filepath = f"./series/{filename}.html"
            series_file = open(series_filepath, "w")
            series_file.write(response.text)
            series_file.close()
            browse_meta(series_filepath)
            break
        else:
            print(f"BOT DETECTED: {soup.title.get_text()}")
            break


def browse_meta(file_path):
    html = open(file_path, "r").read()
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text()
    print(title)


if __name__ == '__main__':
    browse_pages()
