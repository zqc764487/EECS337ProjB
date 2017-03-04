import urllib
import re
import nltk
from bs4 import BeautifulSoup
from collections import Counter
from nltk.tokenize import RegexpTokenizer

UNITS_FILE = "resources/units.txt"
TOOLS_FILE = "resources/tools.txt"
METHODS_FILE = "resources/methods.txt"
VEGETARIAN_SUBSTITUTES = "resources/VegetarianIngredientSubstitutes.csv"

units = []
tools = []
methods = []
preparations = []


verb_tool = {
  'heat':'oven',
  'fry':'pan',
  'chop':'knife',
  'cut':'knife',
  'julienne':'knife',
  'mince':'knife',
  'dice':'knife',
  'minced':'knife',
  'slice':'knife',
  'stir':'spoon',
  'fold':'spoon',
  'glaze':'spoon',
  'drizzle':'spoon',
  'baste':'baster',
  'sift':'colander',
  'cream':'hand mixer',
  'grate':'grater',
  'whisk':'whisk',
  'marinate':'bowl',
  'shred':'food processor',
  'peel':'peeler',
}

#http://www.recipetips.com/kitchen-tips/t--482/units-of-measure.asp
unit_abbreviation = {
	'qt': 'quart',
    't': 'teaspoon',
    'tsp':'teaspoon',
    'c':'cup',
    'oz':'ounce',
    'pt': 'pint',
    'gal':'gallon',
    'lb':'pound'
}


def fetch_recipe(url):
    '''
    Input: the URL for a recipe, 
    Output:a dictionary of the parsed results
    '''
    read_file()
    r = urllib.urlopen(url).read()
    soup = BeautifulSoup(r, "html.parser")
    results = {}
    get_ingredients(soup, results)
    get_directions(soup)
    get_methods(soup, results)
    get_tools(soup, results)
    get_steps(soup, results)
    get_structuredsteps(soup, results)

    #test print recipe
    #print_recipe(results)
    return results

def read_file():
    text_file = open(UNITS_FILE, "r")
    lines = text_file.readlines()
    global units
    for x in lines:
        new = x.rstrip('\n')
        units.append(unicode(new, 'utf-8'))

    text_file = open(TOOLS_FILE, "r")
    lines = text_file.readlines()
    global tools
    for x in lines:
        new = x.rstrip('\n')
        tools.append(new)

    text_file = open(METHODS_FILE, "r")
    lines = text_file.readlines()
    global methods
    for x in lines:
        new = x.rstrip('\n')
        methods.append(new)



def get_ingredients(soup, dct):
    dct["ingredients"] = []
    letters = soup.find_all("span", itemprop="ingredients")

    for element in letters:
        quantity, measurement, name, preparation, descriptor = parse_ingredient(element.get_text().lower())
        d = {
          'name': unicode(name),
          'quantity':quantity,
          'measurement':unicode(measurement),
          'preparation':  unicode(preparation),
          'descriptor':  unicode(descriptor),
        }
        dct["ingredients"].append(d)


def get_structuredsteps(soup, dct):
    dct['structuredsteps'] = []
    new_steps = dct['steps']
    new_ingredients = dct['ingredients']
    tokenizer = RegexpTokenizer(r'\w+')

    time_units = ['min', 'minutes', 'minute', 'hour', 'hours', 'hr', 'hrs', 'min.', 'hr.', 'hrs.' ]

    ingredient_names = []
    for y in new_ingredients:
        ingredient_names.append(y['name'])

    for step in new_steps:
        if step != '':
            method_list = []
            for method in methods:
                if method in step:
                    method_list.append(method)
                elif method + "ing" in step:
                    method_list.append(method)
                elif method + "s" == step:
                    method_list.append(method)
                elif method + "er" == step:
                    method_list.append(method)
                elif method + "ed" == step:
                    method_list.append(method)
                elif method + "ing" == step:
                    method_list.append(method)
            tools_list = []
            for tool in tools:
                if tool in step:
                    tools_list.append(tool)

            for verb in verb_tool:
                if verb in step:
                    tools_list.append(verb_tool[verb])
            ingredient_list = []
            for x in ingredient_names:
                for y in x.split():
                    if y in step:
                        ingredient_list.append(x)

            cooking_time = " "
            step_list = tokenizer.tokenize(step)

            for x in range(0,len(step_list)-2):
                if step_list[x].isdigit():
                    if step_list[x+1] in time_units:
                        cooking_time += step_list[x]+ ' ' + step_list[x+1] + ' '
            d = {
                'step': step,
                'tools': list(set(tools_list)),
                'methods' : list(set(method_list)),
                'cooking time': cooking_time,
                'ingredients' : ingredient_list
            }
            dct["structuredsteps"].append(d)




def parse_ingredient(ingredient):
    quantity = 0
    name = ''
    measurement = ''
    preparation = ''
    descriptors = set()

    global unit_abbreviation
    synonyms = []

    global units

    for key in unit_abbreviation:
        synonyms.append(key)


    ingLst = ingredient.split()


    # parsing descriptor
    PosIngList = nltk.pos_tag(ingLst)
    #print PosIngList
    for index, tup in enumerate(PosIngList):
    	ele, typ = tup[0], tup[1]
    	if typ == 'NN' or typ =='NNS' and ele not in units:
			for ele, tp in reversed(PosIngList[:index]):
				if tp == 'JJ' or tp == 'VBD':
					descriptors.add(ele)
				

    quantityR = []
    measurementR = []
    for index, word in enumerate(ingLst):
        if word in synonyms:
            word = unit_abbreviation[word]
        if word[0].isnumeric():
            if quantity == '':
                quantity = float(convert(word))
                quantityR.append(word)
            else:
                quantity = float(quantity) + float(convert(word))
                quantityR.append(word)
            continue
        elif word in units:
            if measurement == '':
                measurementR.append(word)
                measurement = word
            else:
                measurementR.append(word)
                measurement += ' ' + word
            continue
        #preparation
        elif re.search(r'\,+$', word):
        	preparation += ''+ ' '.join(ingLst[index+1:])
        	ingLst = ingLst[:index+1]




    for word in measurementR:
        if word in ingLst:
            ingLst.remove(word)
    for word in quantityR:
        if word in ingLst:
            ingLst.remove(word)
    for word in descriptors:
        if word in ingLst:
            ingLst.remove(word)


    stopwords = [ 'more', 'as', 'needed', 'with', 'skin', 'to', 'taste', 'such']
    for word in stopwords:
        if word in ingLst:
            ingLst.remove(word)

    name = ' '.join(ingLst)
    name = name.replace(',', '')
    name = name.replace('(', '')
    name = name.replace(')', '')
    name = name.replace(u'\xae', '')

    if quantity == 0:
        quantity = 'to taste'

    if preparation == '':
        preparation = None	

    descriptor = ", ".join(descriptors)
    if not descriptor:
    	descriptor = None

    return quantity, measurement, name, preparation, descriptor


def convert(s):
    try:
        float(s)
        return s
    except ValueError:
        num, denom = s.split('/')
        return float(num) / float(denom)


def get_directions(soup):
    directions_string = ""
    directions = soup.find_all("span", class_="recipe-directions__list--item")
    for element in directions:
        #print str(element.text)
        directions_string += " " + str(element.text)
    return directions_string

def get_steps(soup, dct):
    dct['steps'] = []
    directions = soup.find_all("span", class_="recipe-directions__list--item")
    for element in directions:
        if element != '':
            dct['steps'].append(str(element.text).lower())
    return


def get_tools(soup, dct):
    cnt = Counter()
    dct["cooking tools"] = []

    tokenizer = RegexpTokenizer(r'\w+')

    directions_string = get_directions(soup)

    ingredients= dct['ingredients']

    global tools

    directions_list = map(lambda x:x.lower(),tokenizer.tokenize(directions_string))

    used_list = []
    for x in range(len(directions_list)):
        if x + 2 < len(directions_list):
            two_word_tool = directions_list[x] + ' ' + directions_list[x+1]
            three_word_tool = directions_list[x] + ' ' + directions_list[x+1] + ' ' + directions_list[x+2]
            used_word = directions_list[x+1]
            used_word_two = directions_list[x+2]

        one_word_tool = directions_list[x]
        for tool in tools:
            if tool == two_word_tool:
                used_list.append(used_word)
                cnt[tool] += 1
            elif tool == three_word_tool:
                used_list.append(used_word)
                used_list.append(used_word_two)
                cnt[tool] += 1

            elif tool == one_word_tool and tool not in used_list:
                cnt[tool] +=1

        for verb in verb_tool:
            tool = verb_tool[verb]
            if directions_list[x] == verb and tool not in cnt:
                cnt[tool] +=1

    for x in ingredients:
        for verb in verb_tool:
            tool = verb_tool[verb]
            if verb in x['name'] and tool not in cnt:
                cnt[tool] += 1

    for x in cnt.most_common():
        dct["cooking tools"].append(x[0])

def get_methods(soup, dct):
    cnt = Counter()
    dct["cooking methods"] = []
    dct["primary cooking method"] = " "
    tokenizer = RegexpTokenizer(r'\w+')
    title = soup.title.text
    # get rid of "- allrecipes.com"
    dct["title"] = title[:-17].lower()

    directions_string = get_directions(soup)

    global methods

    directions_list = tokenizer.tokenize(directions_string)

    for x in directions_list:
        for y in methods:
            if y + "ing" == x.lower():
                cnt[y] += 1
                cnt[y + "ing"] += 1
            elif y + "s" == x.lower():
                cnt[y]+=1
                cnt[y+ "s"] += 1
            elif y + "er" == x.lower():
                cnt[y] += 1
                cnt[y + "er"] += 1
            elif y + "ed" == x.lower():
                cnt[y] += 1
                cnt[y + 'ed'] += 1
            elif y[:-1]+ "ing" == x.lower():
                cnt[y]+=1
                cnt[y[:-1]+ "ing"] +=1

    max_list = []
    max_cnt = cnt.most_common(1)[0][1]

    for x,v in cnt.most_common():
        if v== max_cnt:
            max_list.append(x)

    max_list.sort()

    dct["primary cooking method"] = max_list[0]

    for x in cnt.most_common():
        dct["cooking methods"].append(x[0])

def print_recipe(dct):
    for key in dct:
        if key == 'structuredsteps':
            print 'Structured Steps:'
            for index, elem in enumerate(dct[key]):
                if elem != "":
                    print str(index + 1) + ". " + elem['step']
                    if len(elem['ingredients']) != 0:
                        ingredString = "ingredients: " + ', '.join(elem['ingredients'])
                        print ingredString
                    if elem['cooking time'] != ' ':
                        print "cooking time: " + elem['cooking time']
                    if len(elem['tools']) != 0:
                        toolString = "tools: " + ', '.join(elem['tools'])
                        print toolString
                    if len(elem['methods']) != 0:
                        methString = "methods: " + ', '.join(elem['methods'])
                        print methString
                    print '\n'
            print '\n'
        elif key != 'steps':
            print key + ":\n"
            if isinstance(dct[key], basestring):
                print dct[key]
            elif isinstance(dct[key], list):
                for value in dct[key]:
                    if isinstance(value, dict):
                        for x in value:
                            print x + ": " + str(value[x])
                        print '\n'
                    else:
                        print value
            print '\n'





#def main():
    #read_file()
    #recipe = fetch_recipe('http://allrecipes.com/recipe/87845/manicotti-italian-casserole/?clickId=right%20rail%201&internalSource=rr_feed_recipe&referringId=87845&referringContentType=recipe')
    #print '\n'
    #return


#if __name__ == '__main__':
 #   main()
