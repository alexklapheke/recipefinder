#!/usr/bin/env python3

import cgi
import re
import json
from nltk.stem import WordNetLemmatizer
from sqlite3 import dbapi2 as sq3

recipes_db = "recipes.db"

def getRecipes(ingredients):
    db = sq3.connect(recipes_db)

    cmd_query = "SELECT name, url FROM recipes WHERE id IN"
    cmd_select_ingredients = " INTERSECT ".join(["SELECT recipe_id FROM ingredients WHERE ingredient = \"%s\"" % i for i in ingredients])

    results = db.cursor().execute(cmd_query + " (" + cmd_select_ingredients + ");").fetchall()

    db.close()
    return json.dumps([{"recipe": r, "url": u} for (r, u) in results])

if __name__ == '__main__':
    args = cgi.FieldStorage()
    print("Content-Type: application/json\n\n")
    print(getRecipes(json.loads(args.getvalue("list"))))
