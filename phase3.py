import re
from bsddb3 import db

TE = 'te.idx'
YE = 'ye.idx'
RE = 're.idx'

teDB = db.DB()
yeDB = db.DB()
reDB = db.DB()
teDB.open(TE, None, db.DB_BTREE, db.DB_DIRTY_READ)
yeDB.open(YE, None, db.DB_BTREE, db.DB_DIRTY_READ)
reDB.open(RE, None, db.DB_HASH, db.DB_DIRTY_READ)
teCurs = teDB.cursor()
yeCurs = yeDB.cursor()
reCurs = reDB.cursor()

mode = 1  # 1:full mode 2: key mode

outputKey = True

def grammar():
    global mode

    tids = []
    queries = input('Enter a query: ').lower()


    specialQuery = queries.split(' ')

    #check some special query.
    for s in specialQuery:
        # CASE -1 : [Quit]
        if 'stop' in s:
            quit()
        # CASE 0 : [mode change]
        if 'output=full' in s:
            mode = 1
            print("Switch to full record")
        elif 'output=key' in s:
            mode = 2
            print("Switch to key record")

    #check if there are substrings 
    if checkQuotation(queries):
        queryNum = 0
        queries = queries.split(':')
        if queries[0] == 'title':
            termPrefix = 't-'
        else:
            raise RuntimeError('Invalid input')

        text = queries[1]
        substringT = text[1:-1]
        substring = substringT.split(" ")
        #print(substring) 
        for tTerm in substring:
            newTids = search(termPrefix, tTerm)

            if queryNum == 0:
                tids = newTids
            else:
                tids = list(set(tids).intersection(newTids))

            queryNum += 1

        return tids

    else:



        queries = queries.split(' ')
        queryNum = 0

        for query in queries:

            #CASE 1 : [prefix:term]
            if ':' in query:
                query = query.split(':')
                if query[0] == 'title':
                    termPrefix = 't-'
                elif query[0] == 'author':
                    termPrefix = 'a-'
                elif query[0] == 'other':
                    termPrefix = 'o-'
                ####    
                elif query[0] == 'year':
                    termPrefix = ''
              
                else:
                    raise RuntimeError('Invalid Query') 

                newTids = search(termPrefix, query[1])


            #CASE 2: Year   
            elif '>' in query:
                query = query.split('>')
                if query[0] != 'year':
                    raise RuntimeError('Invalid query')

                else:
                    newTids = afterDate(query[1])

            elif '<' in query:
                query = query.split('<')
                if query[0] != 'year':
                    raise RuntimeError('Invalid query')
                else:
                    newTids = beforeDate(query[1])  

            # elif checkQuotation(query):
            #     query = query.split(':')
            #     text = query[1]
            #     substringT = text[1:-1]
            #     substring = substringT.split(" ")
            #     print(substring) 



            else:

                titleTids = search('t-', query)
                authorTids = search('a-', query)
                otherTids = search('o-', query)
                newTids = list(set(titleTids).union(set(authorTids).union(otherTids)))  

            if queryNum == 0:
                tids = newTids
            else:
                tids = list(set(tids).intersection(newTids))

            queryNum += 1

        return tids

def checkQuotation(string):
    for c in string:
        if c == '"':
            return True
    return False



def search(termPrefix, term):
    if termPrefix == '':
        curs = yeCurs
    else:
        curs = teCurs

    key = termPrefix + term
    key = key.encode()
    results = []

    result = curs.get(key, db.DB_SET)
    while result != None: # curs.get(key, db.DB_NEXT_DUP) will return None if it reaches end
        # print(result)
        results.append(result[1])
        result = curs.get(key, db.DB_NEXT_DUP)

    return results

def afterDate(year):
    year = year.encode()
    results = []

    result = yeCurs.get(year, db.DB_SET_RANGE)
    while result != None: # when the date goes through to the end, it will return None
        if result[0] != year: # we just want to include result after the given date
            # print(result)
            results.append(result[1])
        result = yeCurs.get(year, db.DB_NEXT)

    return results

def beforeDate(year):
    year = year.encode()
    results = []

    result = yeCurs.get(year, db.DB_SET_RANGE)
    result = yeCurs.get(year, db.DB_PREV) # move the cursor to previous one
    while result != None: # when the date goes through to the end, it will return None
        # print(result)
        results.append(result[1])
        result = yeCurs.get(year, db.DB_PREV) # since it goes through the databse reversely, the result will be from latest date to earliest date

    return results

def searchTweets(tids):
    for tid in tids:
        result = reCurs.get(tid, db.DB_SET)
        output(result[1])


def output(line):
    global mode 

    line = line.decode()
    # print('debug: ' + line)
    # mode 2 only key is printed
    tkey = re.findall(r'<article key="(.+?)">', line)
    # mode 1 full record is printed
    if mode == 1:
        title = re.findall(r'<title>(.+?)</title>', line)
        tauthor = re.findall(r'<author>(.+?)</author>', line)
        tpages = re.findall(r'<pages>(.+?)</pages>', line)
        tyear = re.findall(r'<year>(.+?)</year>', line)
        journal = re.findall(r'<journal>(.+?)</journal>', line)
        print("key: %s \ntitle: %s \nauthor: %s \npages: %s \nyear: %s \njournal: %s \n" % (''.join(tkey),''.join(title), ''.join(tauthor), ''.join(tpages), ''.join(tyear),''.join(journal)))
    else:
        print("key: %s \n" % (''.join(tkey)))

    print('\n')

def main():
    while True:

        invalidInput = True
        while invalidInput:
            try:
                tids = grammar()
                invalidInput = False
            except RuntimeError:
                print('invalid query')

        if tids == []:
            print('')
        else:
            searchTweets(tids)

main()

teDB.close()
yeDB.close()
reDB.close()
teCurs.close()
yeCurs.close()
reCurs.close()
