# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions

import requests
import json
import inflect

from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

PREFIX = """PREFIX fo: <http://purl.org/ontology/fo/>
            PREFIX fc: <http://www.freeclass.eu/freeclass_v1#>
            PREFIX ex: <http://example.org/>
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> 
            prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> 
            prefix foaf: <http://xmlns.com/foaf/0.1/> 
            prefix focu: <http://focu.io/schema#> 
            prefix dbo: <http://www.dbpedia.org/ontology/>
            prefix dbr: <http://www.dbpedia.org/resource/>
            prefix xsd: <http://www.w3.org/2001/XMLSchema#> 
            prefix dcterms: <http://purl.org/dc/terms/> 
            prefix dcmitype: <http://purl.org/dc/dcmitype/>"""


# Q1) How many courses are offered at Concordia?
class ActionNumberOfUniCourses(Action):

    def name(self) -> Text:
        return "action_number_of_courses_offered"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        response = requests.post("http://localhost:3030/uni/sparql",
                                 data={'query': PREFIX + """
                                                    SELECT (count(?courseId) as ?CourseCount)
                                                    WHERE {
                                                            ?courseId a focu:Course.
                                                    }
                                                    """
                                       })
        y = json.loads(response.text)

        results = y["results"]
        bindings = results["bindings"]

        numberOfCourses = 0

        for result in bindings:
            for key in result:
                if key == "CourseCount":
                    for subKey in result[key]:
                        if subKey == "value":
                            numberOfCourses = result[key][subKey]

        dispatcher.utter_message(text=f"\n Concordia University offers a total of {numberOfCourses} courses")


# Q2) Which topics are covered in COMP 6741 lectures?
class ActionTopicCoveredCourse(Action):

    def name(self) -> Text:
        return "action_topic_covered_course"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        course = tracker.slots['course'].strip()
        courseName = course[:4].upper()
        courseNumber = course[4:]

        response = requests.post("http://localhost:3030/uni/sparql",
                                 data={'query': PREFIX + """
                                        SELECT ?topics WHERE {
                                         ?sub focu:subject "%s" .
                                         ?sub focu:catalog "%s".
                                         ?sub rdfs:comment ?topics .
                                        }

                                        """ % (courseName, courseNumber)
                                       })

        y = json.loads(response.text)

        results = y["results"]
        bindings = results["bindings"]

        topics = ""

        for result in bindings:
            for key in result:
                if key == "topics":
                    for subKey in result[key]:
                        if subKey == "value":
                            topics += result[key][subKey]

        if len(topics) == 0:
            dispatcher.utter_message(text=f"No results found please try again ")
        else:
            dispatcher.utter_message(text=f"\n Here are topics covered in {course} \n {topics} ")


# Q3 Which topics is Arihant competent in?
class ActionCompetencyOfPerson(Action):

    def name(self) -> Text:
        return "action_person_competency"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        person = tracker.slots['person'].strip()

        response = requests.post("http://localhost:3030/uni/sparql",
                                 data={'query': PREFIX + """
                                                    SELECT ?Competencies WHERE {
                                                    ?sudent a focu:Student.
                                                     ?sudent focu:firstName "%s".
                                                     ?sudent focu:competencies ?Competencies.
                                                    }

                                                    """ % person
                                       })

        #
        y = json.loads(response.text)

        results = y["results"]
        bindings = results["bindings"]

        competencies = ""

        for result in bindings:
            for key in result:
                if key == "Competencies":
                    for subKey in result[key]:
                        if subKey == "value":
                            competencies += result[key][subKey] + "\n"

        if len(competencies) == 0:
            dispatcher.utter_message(text=f"No results found please try again ")
        else:
            dispatcher.utter_message(text=f"\n {person} is  Competent in \n {competencies}")


# Q4) Which courses at Concordia teaches deep learning?
class WhichCourseAtUniTeachTopic(Action):

    def name(self) -> Text:
        return "action_course_teach_topic"

    def response_request(self, topic):
        response = requests.post("http://localhost:3030/uni/sparql",
                                 data={'query': PREFIX + """
                                SELECT ?cname (count (?cname) as ?count)
                                WHERE { 
                                ?sub a focu:Course.
                                ?sub focu:courseName ?cname.
                                ?lecture dcterms:isPartOf ?sub. 
                                ?lecture foaf:topic ?topicid.
                                ?topicid rdfs:label "AI"
                                } GROUP BY ?cname ORDER BY DESC(?count)
                            """
                                       })
        # Use the json module to load CKAN's response into a dictionary.
        # % topic
        y = json.loads(response.text)

        # the result is a Python dictionary:
        results = y["results"]

        # courses = []
        #
        # for result in results["bindings"]:
        #     courseCode = result["c1"]
        #     courseName = result["cname"]
        #     topicCount = result["topicCount"]
        #     code = courseCode["value"]
        #     name = courseName["value"]
        #     count = topicCount["value"]
        #     course = {"courseCode": code, "courseName": name, "topicCount": count}
        #     courses.append(course)
        #
        # return courses
        return y

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        p = inflect.engine()

        t = tracker.slots['topic'].strip()

        t_sing = p.singular_noun(t)

        if t_sing is False:
            t_sing = t

        otopic = t_sing.replace(" ", "_")
        y = self.response_request(otopic)

        results = y["results"]
        bindings = results["bindings"]

        coursesTeaching = ""

        for result in bindings:
            for key in result:
                if key == "cname":
                    for subKey in result[key]:
                        if subKey == "value":
                            coursesTeaching += result[key][subKey] + " "

                if key == "count":
                    for subKey in result[key]:
                        if subKey == "value":
                            coursesTeaching += "With topic: " + otopic + " Appearing " + result[key][
                                subKey] + " times \n"

        if len(coursesTeaching) == 0:
            dispatcher.utter_message(text=f"No results found please try again ")
        else:
            dispatcher.utter_message(text=f"\n Courses which covers {otopic} are \n{coursesTeaching}")
        return []


# Q5) Where can I get more information about [COMP6721](course)?
class ActionMoreInformation(Action):

    def name(self) -> Text:
        return "action_information"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        course = tracker.slots['course'].strip()
        courseName = course[:4].upper()
        courseNumber = course[4:]

        response = requests.post("http://localhost:3030/uni/sparql",
                                 data={'query': PREFIX + """
                                        SELECT ?information
                                        WHERE {
                                        ?subject a focu:Course.
                                         ?subject focu:subject "%s".
                                         ?subject focu:catalog "%s".
                                         ?subject rdfs:seeAlso ?information.
                                        }
                                        """ % (courseName, courseNumber)
                                       })

        y = json.loads(response.text)

        results = y["results"]
        bindings = results["bindings"]

        seeAlso = ""

        for result in bindings:
            for key in result:
                if key == "information":
                    for subKey in result[key]:
                        if subKey == "value":
                            seeAlso += result[key][subKey]

        if len(seeAlso) == 0:
            dispatcher.utter_message(text=f"No results found please try again ")
        else:
            dispatcher.utter_message(text=f"\n Here are some useful links \n {seeAlso} ")


# Q6) What are grades of Brendon(person)?
class ActionGetGrade(Action):

    def name(self) -> Text:
        return "action_grade"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        person = tracker.slots['person'].strip()

        response = requests.post("http://localhost:3030/uni/sparql",
                                 data={'query': PREFIX + """
                                        SELECT ?course ?grade WHERE {
                                         ?student a focu:Student.
                                         ?student focu:firstName "%s".
                                         ?student focu:hasRecord ?record.
                                         ?record focu:courseTaken ?course.
                                         ?record focu:grade ?grade
                                        }
                                    """ % person
                                       })

        y = json.loads(response.text)

        results = y["results"]
        bindings = results["bindings"]

        courseAndGrade = ""

        for result in bindings:
            for key in result:
                if key == "course":
                    for subKey in result[key]:
                        if subKey == "value":
                            iresult=result[key][subKey]
                            iresult=iresult[19:]
                            courseAndGrade += iresult + " "

                if key == "grade":
                    for subKey in result[key]:
                        if subKey == "value":
                            courseAndGrade += result[key][subKey] + " \n"

        if len(courseAndGrade) == 0:
            dispatcher.utter_message(text=f"No results found please try again ")
        else:
            dispatcher.utter_message(text=f"\n Here are grades of {person}\n{courseAndGrade} ")


# Q7) Which COMP courses are taught at Concordia?
class ActionDepartmentCourse(Action):

    def name(self) -> Text:
        return "action_department_courses"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        department = tracker.slots['department'].strip()

        response = requests.post("http://localhost:3030/uni/sparql",
                                 data={'query': PREFIX + """           
                                        SELECT ?subjects
                                        WHERE {
                                        ?subject a focu:Course.
                                         ?subject focu:subject "%s".
                                          ?subject focu:courseName ?subjects
                                        } LIMIT 5
                                        """ % department
                                       })

        y = json.loads(response.text)

        results = y["results"]
        bindings = results["bindings"]

        courses = ""

        for result in bindings:
            for key in result:
                if key == "subjects":
                    for subKey in result[key]:
                        if subKey == "value":
                            courses += result[key][subKey] + " \n"

        if len(courses) == 0:
            dispatcher.utter_message(text=f"No results found please try again ")
        else:
            dispatcher.utter_message(text=f"\n Here are courses offered by {department} \n {courses} ")


# Q8
class ActionLectureTopic(Action):
    def name(self) -> Text:
        return "action_lecture_course_topic"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        course = tracker.slots['course'].strip()
        courseName = course[:4].upper()
        courseNumber = course[4:]
        topic = tracker.slots['topic'].strip()


        response = requests.post("http://localhost:3030/uni/sparql",
                                 data={'query': PREFIX + """                
                                    SELECT ?lecture
                                    WHERE {
                                    ?subject a focu:Course.
                                    ?subject focu:subject "%s".
                                    ?subject focu:catalog "%s".
                                    ?lecture dcterms:isPartOf ?subject.
                                    ?lecture foaf:topic "%s".
                                }
                                """ % (courseName, courseNumber, topic)
                                       })

        y = json.loads(response.text)

        results = y["results"]
        bindings = results["bindings"]

        courses = ""

        for result in bindings:
            for key in result:
                if key == "lecture":
                    for subKey in result[key]:
                        if subKey == "value":
                            res=result[key][subKey]
                            res=res[-4:]
                            courses += res + " "

        if len(courses) == 0:
            dispatcher.utter_message(text=f"No results found please try again ")
        else:
            dispatcher.utter_message(text=f"\n {topic} is covered in  {course} Lecture: {courses}")


# Q9 Similar topics 2 courses
class ActionCourseSimilarTopic(Action):
    def name(self) -> Text:
        return "action_similar_topic_courses"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:


        course = tracker.slots['course'].strip()
        courses = course.split("&")

        courseName1 = courses[0][:4].upper()
        courseNumber1 = courses[0][4:]

        courseName2 = courses[1][:4].upper()
        courseNumber2 = courses[1][4:]

        response = requests.post("http://localhost:3030/uni/sparql",
                                 data={'query': PREFIX + """
                                    SELECT ?topics
                                    WHERE {
                                    ?subject1 a focu:Course.
                                     ?subject1 focu:subject "%s".
                                     ?subject1 focu:catalog "%s".
                                     ?subject1 foaf:topic ?topics.
                                     ?subject2 a focu:Course.
                                     ?subject2 focu:subject "%s".
                                     ?subject2 focu:catalog "%s".
                                     ?subject2 foaf:topic ?topics.

                                }
                                """ % (courseName1, courseNumber1, courseName2, courseNumber2)
                                       })

        y = json.loads(response.text)

        results = y["results"]
        bindings = results["bindings"]

        commom = ""

        for result in bindings:
            for key in result:
                if key == "topics":
                    for subKey in result[key]:
                        if subKey == "value":
                            commom += result[key][subKey] + " "

        if len(commom) == 0:
            dispatcher.utter_message(text=f"No results found please try again ")
        else:
            dispatcher.utter_message(text=f"\n {courses[0]} and {courses[1]} covers following similar \n {commom}")


# Q10) Where can I get more information about [COMP6721](course)?
class StudentTakenCourses(Action):

    def name(self) -> Text:
        return "action_students_taken_course"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        course = tracker.slots['course'].strip()
        courseName = course[:4].upper()
        courseNumber = course[4:]
        response = requests.post("http://localhost:3030/uni/sparql",
                                 data={'query': PREFIX + """
                                        SELECT ?firstName ?lastName 
                                        WHERE { 
                                          ?student a focu:Student. 
                                          ?student focu:firstName ?firstName . 
                                          ?student focu:lastName ?lastName. 
                                          ?student focu:hasRecord ?record.
                                          ?record focu:courseTaken ?course.
                                          ?course a focu:Course. 
                                          ?course focu:subject "%s". 
                                          ?course focu:catalog "%s". 
                                        } 
                                        LIMIT 5
                                        """ % (courseName, courseNumber)
                                       })

        y = json.loads(response.text)
        results = y["results"]
        bindings = results["bindings"]

        students = ""

        for result in bindings:
            for key in result:
                if key == "firstName":
                    for subKey in result[key]:
                        if subKey == "value":
                            students += result[key][subKey] + "\n"

        if len(students) == 0:
            dispatcher.utter_message(text=f"No results found please try again ")
        else:
            dispatcher.utter_message(text=f"\n Here is List of students who have taken {course} \n{students} ")


# QN1) What is COMP6741 about [COMP6721](course)?
class ActionGetCourseAbout(Action):

    def name(self) -> Text:
        return "action_course"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        course = tracker.slots['course'].strip()
        course = course.replace(" ", "")
        courseName = course[:4].upper()
        courseNumber = course[4:]

        response = requests.post("http://localhost:3030/uni/sparql",
                                 data={'query': PREFIX + """
                                        SELECT ?desc
                                        WHERE { 
                                        ?sub a focu:Course.
                                        ?sub focu:subject "%s" . 
                                        ?sub focu:catalog "%s". 
                                        ?sub rdfs:comment ?desc
                                        }

                                        """ % (courseName, courseNumber)
                                       })

        y = json.loads(response.text)

        results = y["results"]
        bindings = results["bindings"]

        about = ""

        for result in bindings:
            for key in result:
                if key == "desc":
                    for subKey in result[key]:
                        if subKey == "value":
                            about += result[key][subKey]

        if len(about) == 0:
            dispatcher.utter_message(text=f"No results found please try again ")
        else:
            dispatcher.utter_message(text=f"\n {course} is about \n{about}")


# QN2) Which topics are covered in Lab2 covers?
class ActionGetEvent(Action):

    def name(self) -> Text:
        return "action_event"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        course = tracker.slots['course'].strip()
        course = course.replace(" ", "")
        courseName = course[:4].upper()
        courseNumber = course[4:]


        event = tracker.slots['event'].strip()
        event = event.replace(" ", "").upper()
        events = event.split("#")
        if (events[0] == 'LECTURE'):
            events[0] = 'SLIDES'

        response = requests.post("http://localhost:3030/uni/sparql",
                                 data={'query': PREFIX + """
                                        SELECT ?topic ?source
                                        WHERE { 
                                        ?sub a focu:Course.
                                        ?sub focu:subject "%s" . 
                                        ?sub focu:catalog "%s". 
                                        ?lecture dcterms:isPartOf ?sub. 
                                        ?lecture dcmitype:identifier "Lecture %s".
                                        ?lecture foaf:topic ?topicid.
                                        ?topicid rdfs:label ?topic.
                                        ?topicid focu:topicSource "%s"
                                        }
                                        """ % (courseName, courseNumber, events[1], events[0])
                                       })

        y = json.loads(response.text)

        results = y["results"]
        bindings = results["bindings"]

        topics = ""

        for result in bindings:
            for key in result:
                if key == "topic":
                    for subKey in result[key]:
                        if subKey == "value":
                            topics += result[key][subKey] + "\n"


        if len(topics) == 0:
            dispatcher.utter_message(text=f"No results found please try again ")
        else:
            dispatcher.utter_message(text=f"Following topics are covered in {event} of {course} \n{topics}")
