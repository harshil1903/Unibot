from rdflib import Graph, RDFS, URIRef, Literal
from rdflib.namespace import RDF, DCTERMS, FOAF, Namespace, NamespaceManager, XSD
import pandas as pd
import spacy

#Knowledge Graph variable and namespace declaration
from rdflib.util import from_n3

import StudentData

DCMITYPE = Namespace("http://purl.org/dc/dcmitype/")
LOCAL = Namespace("http://localhost:3030")
#dbp = Namespace("http://dbpedia.org/resource/")
g = Graph()
result = g.parse("schema.ttl", format="turtle")
nsm = NamespaceManager(g)
nsm.bind('dbr', 'http://dbpedia.org/resource/')
nsm.bind('ex', 'http://example.org/')
nsm.bind('focu', 'http://focu.io/schema#')

course_counter = 0
list_of_indexes_of_resourceless_courses = []
list_of_valid_graph_entries = []
concordia_university = URIRef('http://example.org/Concordia')

#End of variable and namespace declaration


#Read csv data
course_data = pd.read_csv('data/output.csv')
lecture_data = pd.read_csv('data/lecture_data.csv')
content_data = pd.read_csv('data/content_data.csv')

cd = course_data.values.tolist()
counter = 0
coursewise_topics = {}

#Process csv data and add it to graph
for line in cd:
    counter += 1

    if counter == 10:
        break
    print(line)
    course_id = line[0]
    course_subject = line[1]
    course_number = line[2]
    course_title = line[3]
    course_credit = line[4]
    course_description = line[5].strip()
    #link = []
    #topics = []

    #DBPedia Spotlight to find links to add as topics
    nlp = spacy.blank('en')
    nlp.add_pipe('dbpedia_spotlight', config={'confidence': 0.4}) #change confidence back to 0.5
    doc_link = nlp(course_title)
    doc_topics = nlp(course_title + " " + course_description)
    #print(doc_topics)

    course_topics = list(set([(ent.text, ent.kb_id_) for ent in doc_topics.ents]))
    course_link = list(set([(ent.text, ent.kb_id_) for ent in doc_link.ents]))

    #print(course_topics)
    #print(course_link)

    coursewise_topics[course_subject + str(course_number)] = course_topics
    # for k,v in coursewise_topics.items():
    #     print(k,v)

    #Add triples to the graph

    print(course_subject + str(course_number))

    _course = from_n3('ex:' + course_subject + str(course_number), nsm=nsm)
    g.add((_course, RDF.type, from_n3('dbr:Course_(education)', nsm=nsm)))
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
            #print("T : ",t)
            t = from_n3('dbr:' + t, nsm=nsm)
            #print(t)
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

        _lecture_id = from_n3('ex:' + course_subject + str(course_number) + "_Lec" + str(lecture_number), nsm=nsm)

        g.add((_lecture_id, RDF.type, from_n3('focu:Lecture', nsm=nsm)))
        g.add((_lecture_id, DCMITYPE.identifier, Literal("Lecture " + str(lecture_number))))
        g.add((_lecture_id, RDFS.label, Literal(lecture_name)))
        g.add((_lecture_id, RDFS.seeAlso, URIRef(lecture_link)))
        g.add((_lecture_id, DCTERMS.ispartOf, _course))

        #Content of lecture
        lecture_contents = content_data[(content_data['CourseId'] == course_id) & (content_data['Identifier'] == lecture_number)].values.tolist()
        cnt = 0
        for content in lecture_contents:
            _content_id = from_n3('ex:content_' + course_subject + str(course_number) + "_Lec" + str(lecture_number) + "_" + str(cnt), nsm=nsm)
            cnt += 1

            g.add((_lecture_id, from_n3('focu:hasContent', nsm=nsm), _content_id))
            g.add((_content_id, DCTERMS.type, Literal(content[2])))
            g.add((_content_id, RDF.type, DCTERMS.BibliographicResource))
            g.add((_content_id, DCTERMS.resource, LOCAL[content[3]]))



#Add student info
#print(coursewise_topics)

students = StudentData.getStudents()

for student in students:
    _student = from_n3('ex:' + str(student[0]), nsm=nsm)
    #print(student[1])
    g.add((_student, RDF.type, from_n3('focu:student', nsm=nsm)))
    g.add((_student, FOAF.name, Literal(student[1] + student[2])))
    #g.add((_student, FOAF.lastName, Literal(student[2])))
    g.add((_student, FOAF.mbox, Literal(student[3])))

    for c in student[4]:
        g.add((_student, from_n3('focu:course', nsm=nsm), from_n3('ex:' + str(c), nsm=nsm)))

    rc = 0
    for crs in student[5]:
        #print(crs)
        _record = from_n3('ex:record' + "_" + str(student[0]) + "_" + str(rc), nsm=nsm)
        g.add((_student, from_n3('focu:hasRecord', nsm=nsm), _record))
        g.add((_record, from_n3('focu:course', nsm=nsm), from_n3('ex:' + str(crs[0]), nsm=nsm)))
        g.add((_record, from_n3('focu:grade', nsm=nsm), Literal(crs[1])))
        rc += 1

    for coursesTaken in student[4]:
        #print(coursesTaken)
        topics = coursewise_topics.get(coursesTaken)
        if topics is None:
            break
        for topic in topics:
            #print(topic[0])
            g.add((_student, from_n3('focu:competencies', nsm=nsm), Literal(topic[0])))




#Add lecture data




#Save data in N-Triple format
g.serialize('knowledge_base_n3.nt',format='nt')
g.serialize('knowledge_base_ttl.ttl',format='turtle')