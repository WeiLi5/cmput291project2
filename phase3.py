import fileinput
from bsddb3 import db
yeidx = db.DB()
reidx = db.DB()
teidx = db.DB()
yeidx.open('ye.idx')
reidx.open('re.idx')
teidx.open('te.idx')

def checkNumeric(string):
    for c in string:
        if not c.isdigit():
            return False
    return True

def checkAlphaNumeric(string):
    for c in string:
        if not (c.isdigit() or c.isalpha() or c == '_'):
            return False
    return True

class Search:
    def __init__(self):
        self.constrain = {
            'terms':[],
            'year':[],
            'substring':[],
            'all' : False
        }



    def search(self,onlyKey):
        key_set = None

        curs = teidx.cursor()
        for term in self.constrain['terms']:
            result = curs.set(term)
            result_set = set()
            while result != None:
                result_set.add(result[1])
                result = curs.next_dup()
            if key_set == None:
                key_set = result_set
            else:
                key_set = key_set & result_set
        return key_set
    def addSubstrConstrain(self,field,term):
        words = term.split(" ")
        for word in words:
            if not checkAlphaNumeric(word):
                return False
        self.constrain['substring'].append((field,term))
        return True
    def addConstrain(self,exp):
        if ":" in exp:
            pair = exp.split(':')
            if len(pair) != 2:
                return False
            field,term = pair
            if field == 'title' or field == 'author' or field == 'other':
                if not checkAlphaNumeric(term):
                    if term[0] == term[-1] == '"':
                        return self.addSubstrConstrain(field,term[1:-1])
                    return False
                self.constrain['terms'].append(field[0]+'-'+term)
            elif field == 'year':
                if not checkNumeric(term):
                    return False
                self.constrain[field].append(term)
            else:
                return False
        elif '<' in exp or '>' in exp:
            if '<' in exp:
                sign = '<'
            else:
                sign = '>'
            pair = exp.split(sign)
            if len(pair) != 2:
                return False
            prefix,year = pair
            if prefix != 'year':
                return False
            if not checkNumeric(year):
                return False
            self.constrain['year'].append(sign+year)
        elif exp == 'database':
            self.constrain['all'] = True
        else:
            return False
        return True
            
            
        

def parseQuery(query):
    inSubString = False
    exps = []
    exp = ""
    for c in query:
        if c == ' ' and not inSubString:
            if exp != "":
                exps.append(exp)
                exp = ""
        elif c == '"':
            inSubString = not inSubString
        if inSubString or c != ' ':
            exp += c
    if inSubString:
        return
    elif exp != '':
        exps.append(exp)
    return exps



def main():
    onlyKey = False
    errorMessage = "Wrong query format"
    for query in fileinput.input():
        query = query.strip().lower()
        exps = parseQuery(query) 
        if exps == None:
            print(errorMessage)
            continue
        if not len(exps):
            continue
        search = Search()
        noError = True
        for exp in exps:
            if exp == 'output=key':
                onlyKey = True
            elif exp == 'output=full':
                onlyKey = False
            else:
                noError = noError and search.addConstrain(exp)
                if not noError:
                    break
        if not noError:
            print(errorMessage)
            continue
        print(search.search(onlyKey))
        reidx.close()
        yeidx.close()
        teidx.close()
main()
