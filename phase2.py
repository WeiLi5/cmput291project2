
import os

os.system('rm -f *.idx')

os.system('sort -u terms.txt -o terms.txt')
os.system('sort -u years.txt -o years.txt')
os.system('sort -u recs.txt -o recs.txt')

os.system('perl break.pl < terms.txt | db_load -c duplicates=1 -T -t btree te.idx')
os.system('perl break.pl < years.txt | db_load -c duplicates=1 -T -t btree ye.idx')
os.system('perl break.pl < recs.txt| db_load -c duplicates=1 -T -t hash re.idx')


os.system('db_dump -p -f 1.txt re.idx')
os.system('db_dump -p -f 2.txt te.idx')
os.system('db_dump -p -f 3.txt ye.idx')
