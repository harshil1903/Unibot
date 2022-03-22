from rdflib import Graph, RDFS, URIRef, Literal
from rdflib.namespace import RDF, DCTERMS, FOAF, Namespace, NamespaceManager, XSD
import pandas as pd
import spacy
from spacy.util import filter_spans

#Knowledge Graph variable and namespace declaration
from rdflib.util import from_n3

import StudentData

DCMITYPE = Namespace("http://purl.org/dc/dcmitype/")
LOCAL = Namespace("file:///unibot/")
g = Graph()
result = g.parse("schema.ttl", format="turtle")
nsm = NamespaceManager(g)
nsm.bind('dbr', 'http://dbpedia.org/resource/')
nsm.bind('ex', 'http://example.org/')
nsm.bind('focu', 'http://focu.io/schema#')

concordia_university = URIRef('https://dbpedia.org/resource/Concordia_University')



#Read csv data
course_data = pd.read_csv('data/dataset.csv', encoding='cp1252')
lecture_data = pd.read_csv('data/lecture_data.csv')
content_data = pd.read_csv('data/content_data.csv')

cd = course_data.values.tolist()
counter = 0
coursewise_topics = {}

skiplist = ["Please see Graduate Calendar" , "Please see GRAD Calendar", "Please see UGRD Calendar",
            "*VRD*", "*BNR*"]


#Process csv data and add it to graph
for line in cd:
    counter += 1
    flag = True


    print(line)
    course_id = line[0]
    course_subject = line[1]
    course_number = line[2]
    course_title = line[3]
    course_credit = line[4]
    course_description = str(line[5]).strip()
    course_topics = []
    course_link = []


    if(course_description in skiplist):
        flag = False

    #DBPedia Spotlight to find links to add as topics
    if flag:
        try:
            nlp = spacy.load("en_core_web_sm")
            #nlp = spacy.blank('en')
            nlp.add_pipe('dbpedia_spotlight', config={'confidence': 0.5}) #change confidence back to 0.5
            doc_link = nlp(course_title)
            doc_topics = nlp(course_title + " " + course_description)

            topic_ents = doc_topics.ents
            topic_ents = filter_spans(topic_ents)

            #course_topics = list(set([(ent.text, ent.kb_id_) for ent in doc_topics.ents]))
            course_topics = list(set([(ent.text, ent.kb_id_) for ent in topic_ents]))
            course_link = list(set([(ent.text, ent.kb_id_) for ent in doc_link.ents]))
        except:
            pass
    coursewise_topics[course_subject + str(course_number)] = course_topics

    #Add triples to the graph

    print(course_subject + str(course_number))

    _course = from_n3('ex:' + course_subject + str(course_number), nsm=nsm)
    g.add((_course, RDF.type, from_n3('focu:Course', nsm=nsm)))
    g.add((_course, RDFS.label, Literal(course_title)))
    g.add((_course, from_n3('focu:subject', nsm=nsm), Literal(course_subject)))
    g.add((_course, from_n3('focu:catalog', nsm=nsm), Literal(course_number)))
    g.add((_course, from_n3('focu:credits', nsm=nsm), Literal(course_credit, datatype=XSD.integer)))
    g.add((_course, from_n3('focu:offeredAt', nsm=nsm), concordia_university))
    g.add((_course, RDFS.comment, Literal(course_description)))

    if(len(course_link) != 0):
        g.add((_course, RDFS.seeAlso, Literal(course_link[0])))

    if(len(course_topics) != 0):
        for topic in course_topics:
            t = topic[0]
            t = t.replace(' ','_')
            t = from_n3('dbr:' + t, nsm=nsm)
            g.add((_course, FOAF.topic, t))
            g.add((t, RDFS.seeAlso, Literal(topic[1])))
            g.add((t, from_n3('focu:provenance', nsm=nsm), Literal("Concordia Open Data")))
    else:
        g.add((_course, FOAF.topic, Literal("No topics for this course")))



    #Adding lecture data
    courseLectures = lecture_data[lecture_data['CourseId'] == course_id].values.tolist()
    for lecture in courseLectures:
        lecture_number = lecture[1]
        lecture_name = lecture[2]
        lecture_link = lecture[3]
        lecture_topic = lecture[4]

        _lecture_id = from_n3('ex:' + course_subject + str(course_number) + "_Lec" + str(lecture_number), nsm=nsm)

        g.add((_lecture_id, RDF.type, from_n3('focu:Lecture', nsm=nsm)))
        g.add((_lecture_id, DCMITYPE.identifier, Literal("Lecture " + str(lecture_number))))
        g.add((_lecture_id, RDFS.label, Literal(lecture_name)))
        g.add((_lecture_id, RDFS.seeAlso, URIRef(lecture_link)))
        g.add((_lecture_id, FOAF.topic, Literal(lecture_topic)))
        g.add((_lecture_id, DCTERMS.isPartOf, _course))

        #Content of lecture
        lecture_contents = content_data[(content_data['CourseId'] == course_id) & (content_data['Identifier'] == lecture_number)].values.tolist()
        cnt = 0
        for content in lecture_contents:
            _content_id = from_n3('ex:content_' + course_subject + str(course_number) + "_Lec" + str(lecture_number) + "_" + str(cnt), nsm=nsm)
            cnt += 1

            g.add((_lecture_id, from_n3('focu:hasContent', nsm=nsm), _content_id))
            g.add((_content_id, DCTERMS.type, Literal(content[2])))
            g.add((_content_id, RDF.type, DCTERMS.BibliographicResource))
            if('https' not in content[3] and 'http' not in content[3]):
                g.add((_content_id, DCTERMS.resource, LOCAL[content[3]]))
            else:
                g.add((_content_id, DCTERMS.resource, URIRef(content[3])))




#Add student info
students = StudentData.getStudents()

for student in students:
    _student = from_n3('ex:' + str(student[0]), nsm=nsm)
    g.add((_student, RDF.type, from_n3('focu:Student', nsm=nsm)))
    #g.add((_student, FOAF.name, Literal(student[1] + " " + student[2])))
    g.add((_student, from_n3('focu:firstName', nsm=nsm), Literal(student[1])))
    g.add((_student, from_n3('focu:lastName', nsm=nsm), Literal(student[2])))
    g.add((_student, FOAF.mbox, Literal(student[3])))

    for c in student[4]:
        g.add((_student, from_n3('focu:courseTaken', nsm=nsm), from_n3('ex:' + str(c), nsm=nsm)))

    rc = 0
    for crs in student[5]:
        _record = from_n3('ex:record' + "_" + str(student[0]) + "_" + str(rc), nsm=nsm)
        g.add((_student, from_n3('focu:hasRecord', nsm=nsm), _record))
        g.add((_record, from_n3('focu:courseTaken', nsm=nsm), from_n3('ex:' + str(crs[0]), nsm=nsm)))
        g.add((_record, from_n3('focu:grade', nsm=nsm), Literal(crs[1])))
        rc += 1

    for coursesTaken in student[4]:
        topics = coursewise_topics.get(coursesTaken)
        if topics is None:
            break
        for topic in topics:
            g.add((_student, from_n3('focu:competencies', nsm=nsm), Literal(topic[0])))




#Save data in N-Triple format
g.serialize('knowledge_base_n3.nt',format='nt')
g.serialize('knowledge_base_ttl.ttl',format='turtle')