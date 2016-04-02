import tweepy
from newspaper import Article, fulltext
import random
import pprint
import py2neo
from py2neo import Graph
from py2neo import neo4j
from threading import Thread
import Queue
from Queue import Queue
from py2neo import authenticate




#graphdb = Graph('http://localhost:7474/default.graphdb')



#Sam
consumer_key = ''
consumer_secret = ''
access_token = ''
access_token_secret = ''



graphdb = Graph()
graphdb.delete_all()


INSERT_USER_URL_QUERY = '''
    MERGE (user:User {username: {username}})
    MERGE (url:URL {url: {url}})
    CREATE UNIQUE (user)-[:SHARED]->(url)
    FOREACH (kw in {keywords} | MERGE (k:Keyword {text: kw}) CREATE UNIQUE (k)<-[:IS_ABOUT]-(url))
    FOREACH (author in {authors} | MERGE (a:Author {name: author}) CREATE UNIQUE(a)<-[:WRITTEN_BY]-(url))
'''

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth, wait_on_rate_limit = True, wait_on_rate_limit_notify = True)
#api = tweepy.API(auth)

ids = api.friends_ids()
urls=[]
print ids
for friend in ids:
	#print "id" % friend
    statuses = api.user_timeline(id=friend, count=4)
    for status in statuses:
        if status.entities and status.entities['urls']:
            for url in status.entities['urls']:
            	urls.append((url['expanded_url'], status.author.screen_name))

with open('urls.csv', 'w') as f:
    for url in urls:
    	cad=url[0] + ',' + url[1] + '\n'
        f.write(cad.encode('utf-8'))
    f.close()

def parseURL(url):
    a = Article(url)
    try:
        a.download()
        a.parse()
        a.nlp()
        authors = a.authors
        keywords = a.keywords
        del(a)
        return (authors, keywords)
    except:
        return (None, None)



def insertUserURL(user, url):
    authors, keywords = parseURL(url)
    if authors and keywords:
        params = {}
        params['username'] = user
        params['url'] = url
        params['authors'] = authors
        params['keywords'] = keywords
        graphdb.cypher.execute(INSERT_USER_URL_QUERY, params)

#for user, url in urls:
#    insertUserURL(user, url)

concurrent = 200

def doWork():
    while True:
        urlTuple = q.get()
        insertUserURL(urlTuple[0], urlTuple[1])
        q.task_done()


q = Queue(concurrent * 2)

for i in range(concurrent):
    t = Thread(target=doWork)
    t.daemon = True
    t.start()
try:
    with open('urls.csv', 'r') as f:
        for line in f:
            l = line.split(',')
            url = l[0]
            user = l[1].replace('\n', '')
            q.put((user, url))
    q.join()
except:
    pass
