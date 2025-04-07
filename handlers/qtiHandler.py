import html
import os
import re
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from bs4 import BeautifulSoup
from bs4.formatter import HTMLFormatter
from text2qti.config import Config
from text2qti.qti import QTI
from text2qti.quiz import Quiz


def qti_handler(dir_input: str, dir_output: str):
    with open(os.path.join(dir_input), "r", encoding="utf-8") as f:
        content = f.read()

    text2qti_config = Config()
    quiz = Quiz(content, config=text2qti_config, source_name=os.path.dirname(dir_input))
    qti = QTI(quiz)

    qti_dir = os.path.join(dir_output, "qti.zip")
    qti.save(qti_dir)

    # Black magic
    with TemporaryDirectory() as tmpdir:
        with ZipFile(qti_dir, "r") as zf:
            zf.extractall(tmpdir)

        for root, _, files in os.walk(tmpdir):
            for file in files:
                if os.path.basename(file).startswith("text2qti_assessment_"):
                    with open(os.path.join(root, file), "r") as f:
                        soup = BeautifulSoup(f.read(), features="xml")

                    for mattext_tag in soup.find_all("mattext"):
                        mattext_soup = BeautifulSoup(
                            mattext_tag.string, features="lxml"
                        )
                        for false_img in mattext_soup.find_all(
                            "img",
                            src=re.compile(
                                r"\.(?!bmp$|gif$|jpeg$|jpg$|svg$|tiff$|png$).*"
                            ),
                        ):
                            src_tag = false_img["src"]
                            extension = re.search(r"\.([a-zA-Z0-9]+)$", src_tag).group(
                                1
                            )
                            if extension == "mp3":
                                audio_tag = soup.new_tag("audio", controls=True)
                                source_tag = soup.new_tag(
                                    "source", type="audio/mp3", src=src_tag
                                )
                                audio_tag.append(source_tag)
                                false_img.replaceWith(audio_tag)
                        mattext_tag.string = html.escape(str(mattext_soup))

                    with open(os.path.join(root, file), "w") as f:
                        f.write(soup.prettify(formatter=HTMLFormatter(indent=2)))

        with ZipFile(qti_dir, "w") as zf:
            for root, _, files in os.walk(tmpdir):
                for file in files:
                    zf.write(
                        os.path.join(root, file),
                        os.path.relpath(os.path.join(root, file), tmpdir),
                    )
