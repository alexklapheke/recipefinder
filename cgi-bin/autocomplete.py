#!/usr/bin/env python3

import cgi
import re
import json
from nltk.stem import WordNetLemmatizer
from sqlite3 import dbapi2 as sq3

recipes_db = "recipes.db"

def listIngredients(prefix):
    db = sq3.connect(recipes_db)

    cmd_query = "SELECT ingredient FROM ingredients WHERE ingredient LIKE '%s%%'" % prefix

    results = db.cursor().execute(cmd_query).fetchall()

    db.close()

    # From <https://stackoverflow.com/a/480227>
    results_sorted = sorted(results, key=results.count, reverse=True)
    seen = set()
    seen_add = seen.add
    return json.dumps([x[0] for x in results_sorted if not (x in seen or seen_add(x))])

if __name__ == '__main__':
    args = cgi.FieldStorage()
    print("Content-Type: application/json\n\n")
    print(listIngredients(args.getvalue("prefix")))

