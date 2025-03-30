import os

import text2qti.config
import text2qti.qti
import text2qti.quiz
from rich import print


def qti_handler(path: str):
    with open(os.path.join(path, "content.txt"), "r", encoding="utf-8") as log:
        content = log.read()

    text2qti_config = text2qti.config.Config()
    quiz = text2qti.quiz.Quiz(
        content, config=text2qti_config, source_name=os.path.join(path, "content.txt")
    )
    qti = text2qti.qti.QTI(quiz)
    qti.save(f"{os.path.join(path, 'qti.zip')}")

    print(
        "[blue]│   └── [/blue]"
        "[green]Đã tạo file zip QTI thành công: [/green]"
        f"[white]{os.path.join(path, 'qti.zip')}[/white]"
    )
