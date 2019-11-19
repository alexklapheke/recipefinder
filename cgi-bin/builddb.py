#!/usr/bin/env python3

import re
from nltk.stem import WordNetLemmatizer
from sqlite3 import dbapi2 as sq3

recipes_db = "recipes.db"
recipes_file = "/home/alex/org/Cooking.org"

adj_sizes = "small|sm\.?|medium|med\.?|large|lg\.?|big|smallish|biggish|thick|thin|scant|generous|rounded|coarse|fine"
adj_states = "whole|crushed|chopped|cubed|diced|minced|smashed|pitted|peeled|cooked|uncooked|bone-in|boneless|fresh"
adj_units = "bottles?|bulbs?|bunch(?:es)?|c\.?|cans?|cans?|chunks?|cloves?|containers?|cups?|dash(?:es)?|fillets?|fistfuls?|fl\.? oz\.?|fluid ounces?|g.?|grams?|handfuls?|heads?|inch(?:es)?|ins?|kg.?|kilograms?|knots?|l\.?|lbs?\.?|liter|loaf|loaves|mg\.?|milligrams?|milliliters?|ml\.?|nobs?|ounces?|ozs?\.?|packages?|packets?|packets?|pieces?|pinch(?:es)?|pints?|pods?|pounds?|quarts?|recipes?|ribs?|slabs?|sprigs?|stalks?|sticks?|t\.?|tablespoons?|tbs?\.?|tbsp\.?s?|teaspoons?|tsps?\.?|x|\"|"

regex = re.compile("^- \[[ X]\] ([0-9.]*(?!\/)) *(?:and +)?(\d+ *\/ *\d+)? *(?:(?:or|to|-|–) *\d*(?: \d+\/\d+)?)? *(?:\([^)]+\))? *(?:very +)?(?:(?:(?:%s)(?:ly)?) +)?(?:(%s) +)*(?:(?:(?:%s)(?:ly)?) +)?(?:(?:%s) +)?(?:of +|\+ *)?([^,(\[$]+)" % (adj_sizes, adj_units, adj_sizes, adj_states), re.IGNORECASE)

def parseIngredient(s):
    # Do some initial cleanup
    s = s.replace("⁄", "/") # replace solidus with virgule
    s = s.replace("¼", "1/4")
    s = s.replace("½", "1/2")
    s = s.replace("¾", "3/4")
    s = s.replace("⅓", "1/3")
    s = s.replace("⅔", "2/3")
    s = s.replace("⅕", "1/5")
    s = s.replace("⅖", "2/5")
    s = s.replace("⅗", "3/5")
    s = s.replace("⅘", "4/5")
    s = s.replace("⅙", "1/6")
    s = s.replace("⅚", "5/6")
    s = s.replace("⅛", "1/8")
    s = s.replace("⅜", "3/8")
    s = s.replace("⅝", "5/8")
    s = s.replace("⅞", "7/8")

    s = re.sub(" one ",   " 1 ",  s, flags=re.IGNORECASE)
    s = re.sub(" two ",   " 2 ",  s, flags=re.IGNORECASE)
    s = re.sub(" three ", " 3 ",  s, flags=re.IGNORECASE)
    s = re.sub(" four ",  " 4 ",  s, flags=re.IGNORECASE)
    s = re.sub(" five ",  " 5 ",  s, flags=re.IGNORECASE)
    s = re.sub(" six ",   " 6 ",  s, flags=re.IGNORECASE)
    s = re.sub(" seven ", " 7 ",  s, flags=re.IGNORECASE)
    s = re.sub(" eight ", " 8 ",  s, flags=re.IGNORECASE)
    s = re.sub(" nine ",  " 9 ",  s, flags=re.IGNORECASE)
    s = re.sub(" ten ",   " 10 ", s, flags=re.IGNORECASE)

    # Resolve case-sensitive abbreviations
    s = re.sub("(\d *)T\.", "\\1 tablespoon", s)

    # The actual match
    s_parsed = regex.match(s)

    if s_parsed is not None:
        # Parse numbers
        try:
            whole = float(s_parsed.group(1))
        except ValueError:
            whole = 0
        if s_parsed.group(2) is not None:
            frac = s_parsed.group(2).split("/")
            num = int(frac[0])
            denom = int(frac[1])
        else:
            num = 0
            denom = 1
        amount = whole + num/denom

        if s_parsed.group(3) is not None:
            unit = s_parsed.group(3).lower()

            unit = re.sub("^c\.?$",          "cup",         unit)
            unit = re.sub("^g\.?$",          "gram",        unit)
            unit = re.sub("^ins?\.?$",       "inch",        unit)
            unit = re.sub("^fl\.? ozs?\.?$", "fluid ounce", unit)
            unit = re.sub("^kgs?\.?$",       "kilogram",    unit)
            unit = re.sub("^l\.?$",          "liter",       unit)
            unit = re.sub("^lbs?\.?$",       "pound",       unit)
            unit = re.sub("^mg\.?$",         "milligram",   unit)
            unit = re.sub("^ml\.?$",         "milliliter",  unit)
            unit = re.sub("^ozs?\.?$",       "ounce",       unit)
            unit = re.sub("^t\.?$",          "teaspoon",    unit)
            unit = re.sub("^tsps?\.?$",      "teaspoon",    unit)
            unit = re.sub("^tbsps?\.?$",     "tablespoon",  unit)
            unit = re.sub("^tbs?\.?$",       "tablespoon",  unit)
            unit = re.sub("^x\.?$",          "",            unit)
            unit = re.sub("^\"$",            "inch",        unit)

            unit = WordNetLemmatizer().lemmatize(unit).strip()
        else:
            unit = ""

        ingredient = WordNetLemmatizer().lemmatize(s_parsed.group(4)).strip()

        return (amount, unit, ingredient)
    else:
        return None

def createDB():

    db = sq3.connect(recipes_db)

    cmd_createtable = """
    DROP TABLE IF EXISTS "recipes";
    DROP TABLE IF EXISTS "ingredients";
    CREATE TABLE "recipes" (
                    "id" INTEGER PRIMARY KEY NOT NULL,
                    "name" VARCHAR NOT NULL,
                    "url" VARCHAR,
                    "fulltext" VARCHAR
                    );
    CREATE TABLE "ingredients" (
                    "id" INTEGER PRIMARY KEY NOT NULL,
                    "amount" VARCHAR,
                    "unit" VARCHAR,
                    "ingredient" VARCHAR,
                    "recipe_id" INTEGER,
                    FOREIGN KEY(recipe_id) REFERENCES recipes(id)
                    );
    """
    db.cursor().executescript(cmd_createtable)
    db.commit()

    cmd_recipe = "INSERT INTO recipes (id, name, url, fulltext) VALUES (?, ?, ?, ?);"
    cmd_ingredient = "INSERT INTO ingredients (id, amount, unit, ingredient, recipe_id) VALUES (?, ?, ?, ?, ?);"

    r = 0
    i = 0

    name = re.compile("^\*\* [A-Z]+ (.*\S) +:.*")
    url = re.compile(":URL: +(\S+)")

    with open (recipes_file, "r") as f:
        for recipe in f.read().split('\n*'):
            if recipe.startswith("** "):
                try:
                    recipe_url = url.search(recipe).group(1)
                except AttributeError:
                    recipe_url = ""
                db.cursor().execute(cmd_recipe, (r, name.match(recipe).group(1), recipe_url, recipe))

                for line in recipe.split('\n'):
                    if line.startswith("- [ ] ") or line.startswith("- [X] "):
                        p = parseIngredient(line)
                        if p is not None:
                            db.cursor().execute(cmd_ingredient, (i, p[0], p[1], p[2], r))
                            i += 1
            r += 1
    db.commit()
    db.close()

if __name__ == '__main__':
    createDB()
