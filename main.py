from rdflib import Graph, RDFS, URIRef, Literal
from rdflib.namespace import RDF, FOAF, Namespace, NamespaceManager, XSD
import pandas as pd
import spacy

#Knowledge Graph variable and namespace declaration
from rdflib.util import from_n3

dbp = Namespace("http://dbpedia.org/resource/")
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


cd = course_data.values.tolist()
counter = 0
#Process csv data and add it to graph
for line in cd:
    counter += 1

    if counter == 50:
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


    #Add triples to the graph

    print(course_subject + str(course_number))

    course = from_n3('ex:' + course_subject + str(course_number), nsm=nsm)
    g.add((course, RDF.type, from_n3('dbr:Course_(education)', nsm=nsm)))
    g.add((course, RDFS.label, Literal(course_title)))
    g.add((course, from_n3('focu:subject', nsm=nsm), Literal(course_subject)))
    g.add((course, from_n3('focu:catalog', nsm=nsm), Literal(course_number)))
    g.add((course, from_n3('focu:credits', nsm=nsm), Literal(course_credit, datatype=XSD.integer)))
    g.add((course, from_n3('focu:offeredAt', nsm=nsm), concordia_university))
    g.add((course, RDFS.comment, Literal(course_description)))

    if(len(course_link) != 0):
        g.add((course, RDFS.seeAlso, Literal(course_link[0])))

    if(len(course_topics) != 0):
        for topic in course_topics:
            t = topic[0]
            t = t.replace(' ','_')
            #print("T : ",t)
            t = from_n3('ex:' + t + str(course_number), nsm=nsm)
            #print(t)
            g.add((course, FOAF.topic, Literal(topic[0])))
            g.add((t, RDFS.seeAlso, Literal(topic[1])))
            g.add((t, from_n3('focu:provenance', nsm=nsm), Literal("Concordia Open Data")))
    else:
        g.add((course, FOAF.topic, Literal("No topics for this course")))



#Save data in N-Triple format
g.serialize('knowledge_base_n3.nt',format='nt')
g.serialize('knowledge_base_ttl.ttl',format='turtle')