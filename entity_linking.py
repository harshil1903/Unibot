import os
import csv
import spacy

def generate_topics(courseID, lectureID, filePath, src):
    path = "data/topics.csv"
    flag = os.path.isfile(path)
    with open(path, 'a+', newline='') as f:
        f.seek(0)
        columns = ['CourseID', 'LectureID', 'Source', 'Topic', 'TopicLink']
        writer = csv.DictWriter(f, fieldnames=columns)
        if not flag:
            writer.writeheader()

        file = open(filePath, 'r', encoding="UTF-8")
        count = 1
        data = ""
        while True:
            line = file.readline()
            if not line:
                break
            #print("Line{}: {}".format(count, line.strip()))
            count = count + 1
            data += line.strip()

        try:
            nlp = spacy.load("en_core_web_sm")
            nlp.add_pipe('dbpedia_spotlight', config={'confidence': 0.75})  # change confidence back to 0.5

            doc = nlp(data)
            topics = set()
            l = []
            for token in doc:
                if token.ent_kb_id_ != "" and token.tag_ == "NNP" and token.text not in topics:
                    print(token.text, token.pos_, token.tag_, token.ent_kb_id_)
                    topic = dict()
                    topic['CourseID'] = courseID
                    topic['LectureID'] = lectureID
                    topic['Source'] = src
                    topic['Topic'] = token.text
                    topic['TopicLink'] = token.ent_kb_id_
                    l.append(topic)
                    topics.add(token.text)

            index = []
            for i in range(len(l)):
                link = l[i]['TopicLink']
                for j in range(i+1, len(l)):
                    if l[j]['TopicLink'] != link:
                        break
                    l[i]['Topic'] += " " + l[j]['Topic']
                    index.append(j)
                i = j

            for i in range(len(l)):
                if i not in index:
                    print(l[i])
                    writer.writerow(l[i])
        except:
            pass
        file.close()




if __name__ == "__main__":
    IS = "unibot_text/COMP6741"
    AI = "unibot_text/COMP6721"

    lec = 1
    for filename in os.listdir(IS + "/lectures"):
        print(str(filename))
        generate_topics('40355', lec, IS + "/lectures/"+ filename, "SLIDES")
        lec = lec + 1

    lec = 1
    for filename in os.listdir(AI + "/lectures"):
        print(str(filename))
        generate_topics('40353', lec, AI + "/lectures/" + filename, "SLIDES")
        lec = lec + 1

    lec = 2
    for filename in os.listdir(IS + "/worksheets"):
        print(str(filename))
        generate_topics('40355', lec, IS + "/worksheets/" + filename, "WORKSHEET")
        lec = lec + 1

    lec = 2
    for filename in os.listdir(AI + "/worksheets"):
        print(str(filename))
        generate_topics('40353', lec, AI + "/worksheets/" + filename, "WORKSHEET")
        lec = lec + 1

    lec = 1
    for filename in os.listdir(IS + "/labs"):
        print(str(filename))
        generate_topics('40355', lec, IS + "/labs/" + filename, "LAB")
        lec = lec + 1

    lec = 1
    for filename in os.listdir(AI + "/labs"):
        print(str(filename))
        generate_topics('40353', lec, AI + "/labs/" + filename, "LAB")
        lec = lec + 1
