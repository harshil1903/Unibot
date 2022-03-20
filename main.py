from rdflib import Graph, Literal, Namespace, RDFS, URIRef, Literal
from rdflib.namespace import RDF, FOAF, DC, DCTERMS, Namespace, NamespaceManager #rdflib.namespace comes with predefined namespace
import pandas
from uuid import uuid4

#Knowledge Graph variable and namespace declaration
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
course_data = pandas.read_csv('data/output.csv')


#Process csv data and add it to graph




#Save data in N-Triple format
#graph.serialize('knowledge_base.nt',format='nt')
#graph.serialize('knowledge_base.nt',format='turtle')