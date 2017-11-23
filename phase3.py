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
            'terms':[], # store terms like a-xxx,o-xxx,t-xxx
            'year':[],  # store years xxxx, or >xxxx <xxxx
            'substring':[], # store tuples like (filed,substring)
            'all' : False
        }



    def search(self,onlyKey):
        key_set = None

        curs = teidx.cursor()
        # for terms, look up key in teidx
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
                
        # for years, look up key in yeidx
        
        
        # for substring, look up key in teidx for terms
        # and get the whole record from reidx
        # then check if substring is a substring of certain field
        # of the record
        
        
        return key_set
    
    def addSubstrConstrain(self,field,term):
        words = term.split(" ")
        for word in words:
            if not checkAlphaNumeric(word):
                return False
        self.constrain['substring'].append((field,term))
        return True
    def addConstrain(self,exp):
        # case 1: field:term
        if ":" in exp:
            pair = exp.split(':')
            if len(pair) != 2:
                return False
            field,term = pair
            
            # check for grammer for certain field
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
        # case 2: year>xxxx or year<xxxx, range constrain
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
        # case 3: all records
        elif exp == 'database':
            self.constrain['all'] = True
            
        # case 4: error
        else:
            return False
        return True
            
            
        

def parseQuery(query):
    inSubString = False
    exps = []
    exp = ""
    for c in query:
        # encounter space not in a substring
        if c == ' ' and not inSubString:
            if exp != "":
                # end a expression
                exps.append(exp)
                exp = ""
        # encounter a ", start or end a sbustring
        elif c == '"':
            inSubString = not inSubString
        # add char to expression
        if inSubString or c != ' ':
            exp += c
    # if still in substring after parsing (no end ")
    # error
    if inSubString:
        return
    # close last expression in case query not end with space
    elif exp != '':
        exps.append(exp)
    return exps



def main():
    onlyKey = False
    errorMessage = "Wrong query format"
    
    # take query from std input
    for query in fileinput.input():
        # convert query to expressions
        query = query.strip().lower()
        exps = parseQuery(query) 
        
        # if error in parsing query
        if exps == None:
            print(errorMessage)
            continue
            
        # if empty query
        if not len(exps):
            continue
            
        # create new Search object for every query
        search = Search()
        noError = True
        
        # loop through expressions
        for exp in exps:
            
            # check if the expression is change output setting
            if exp == 'output=key':
                onlyKey = True
            elif exp == 'output=full':
                onlyKey = False
                
            # add constrain to search
            else:
                noError = noError and search.addConstrain(exp)
                if not noError:
                    break
                    
        # if error in checking constrain
        if not noError:
            print(errorMessage)
            continue
        
        # search for result
        print(search.search(onlyKey))
        
        # close dbs
        reidx.close()
        yeidx.close()
        teidx.close()
main()
