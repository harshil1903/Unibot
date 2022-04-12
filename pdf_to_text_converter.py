import tika
from tika import parser
import os
tika.initVM()


IS_dir = "unibot/COMP6741"
AI_dir = "unibot/COMP6721"
IS = "unibot_text/COMP6741"
AI = "unibot_text/COMP6721"


def convert(folder, dest, target, filePrefix):
    print("Converting {} folder's {} files".format(folder, target))
    i = 1
    for file in os.listdir(folder + target):
        parsedFile = parser.from_file(folder + target + "/" + file)
        lines = parsedFile["content"].strip().split("\n")
        lines = set(lines)
        text = ""
        for line in lines:
            text += line.strip() + "\n"

        f = open(dest + target + filePrefix + str(i) + ".txt", 'w', encoding='UTF-8')
        f.write(text)
        f.close()
        i += 1


convert(IS_dir, IS, "/worksheets", "/worksheet")
convert(IS_dir, IS, "/lectures", "/slides")
convert(AI_dir, AI, "/worksheets", "/worksheet")
convert(AI_dir, AI, "/lectures", "/slides")