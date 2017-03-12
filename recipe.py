import urllib
import re
import nltk
from bs4 import BeautifulSoup
from collections import Counter, defaultdict
from nltk.tokenize import RegexpTokenizer
from urlparse import urljoin
import random
from food import *
from crawl import *

UNITS_FILE = "resources/units.txt"
TOOLS_FILE = "resources/tools.txt"
METHODS_FILE = "resources/methods.txt"
VEGETARIAN_SUBSTITUTES = "resources/VegetarianIngredientSubstitutes.csv"

units = []
tools = []
methods = []
preparations = []

FREQ_FILE_I = 'resources/freq_set_i.txt'
FREQ_FILE_F = 'resources/freq_set_f.txt'
FREQ_FILE_G = 'resources/freq_set_g.txt'
FREQ_FILE_A = 'resources/freq_set_a.txt'

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

graph = food_graph()

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
                'ingredients' : list(set(ingredient_list))
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
        if unicode(word[0]).isnumeric() and re.search(r'^\d\/\d+$', word):
            if quantity == '':
                quantity = float(convert(word))
                quantityR.append(word)
            else:
                quantity = float(quantity) + float(convert(word))
                quantityR.append(word)
            continue
        elif unicode(word).isnumeric():
            if quantity == '':
                quantity = float(convert(word))
                quantityR.append(word)
            else:
                quantity = float(quantity) + float(convert(word))
                quantityR.append(word)
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
            elif y == x.lower():
                cnt[y] += 1

    max_list = []
    max_cnt = 1
    if len(cnt) > 0:
        max_cnt = cnt.most_common(1)[0][1]
    else:
        max_cnt =0
    

    for x, v in cnt.most_common():
        if v == max_cnt:
            max_list.append(x)

    max_list.sort()
    if max_list:
        dct["primary cooking method"] = max_list[0]
    else:
        dct["primary cooking method"] = None

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

def fetchRecipeURL(req_recipe):
    baseURL = 'http://allrecipes.com/search/results/'
    params = '?wt=' + req_recipe.replace(' ', '%20') + '&sort=re'

    r = urllib.urlopen(baseURL + params).read()
    soup = BeautifulSoup(r, "html.parser")

    baseSite = 'http://allrecipes.com'
    links = []
    for article in soup.find_all('article', attrs={'class':'grid-col--fixed-tiles'}):
        for link in article('a', attrs={'href':True}):
            if link['href'].startswith('/recipe'):
                links.append(urljoin(baseSite, link['href']))
    return random.choice(links[1:])

def replaceWholeWord(sentence, replacement, sub):
    words = nltk.word_tokenize(sentence)
    for index, word in enumerate(words):
        if word == str(replacement):
            words[index] = str(sub)
    return " ".join(words)


def replaceIngredients(recipe, substitutes):
    for replacement in substitutes:
        substitute = substitutes[replacement]
        swap = str(random.choice(substitute).name)

        # if has wordnet naming scheme, extract food name
        if "." in swap:
            swap = swap.split(".")[0]

        for ingredient in recipe['ingredients']:
            name = str(ingredient['name'])
            ingredient['name'] = replaceWholeWord(name, str(replacement), swap)

        for index, step in enumerate(recipe['steps']):
            recipe['steps'][index] = replaceWholeWord(step, str(replacement), swap)

        for i, strucstep in enumerate(recipe['structuredsteps']):
            ingredients = strucstep['ingredients']
            step = strucstep['step']

            for j, ingredient in enumerate(ingredients):
                recipe['structuredsteps'][i]['ingredients'][j] = replaceWholeWord(ingredient, str(replacement), swap)
            recipe['structuredsteps'][i]['step'] = replaceWholeWord(step, str(replacement), swap)

    return recipe


def makeVegetarian(recipe):
    ingredients = [x['name'] for x in recipe['ingredients']]
    substitutes = {}
    for ingredient in ingredients:
        node = graph.pick_one(ingredient)
        if node:
            if node.has_property('meat'):
                substitutes[ingredient] = node.get_substitutes(properties = ['-meat'])
    return substitutes


def frequenciesToNodes(frequentIngredients):
    collect = []
    for ingredient in frequentIngredients:
        if ingredient:
            node = graph.pick_one(ingredient)
            if node:
                collect.append((ingredient,node))

    return collect 
#recipe.convertCuisine(fetch_recipe('http://allrecipes.com/recipe/219929/heathers-fried-chicken/'), 'indian')
def convertCuisine(recipe, toType):
    '''
    Inputs: Recipe Schema, And Type of cuisine you wish to convert it to "french" "indian" "african"
    '''
    localType = FREQ_FILE_I
    if toType == "indian":
        localType = FREQ_FILE_I
    elif toType == 'german':
        localType = FREQ_FILE_G 
    elif toType == 'french':
        localType = FREQ_FILE_F
    elif toType == 'african':
        localType = FREQ_FILE_A

    frequentIngredients = order_freq(read_freq_file(localType))

    freqNodes = frequenciesToNodes(frequentIngredients)

    basicLevels = {}
    for node in freqNodes:
        temp = [child for parent in node[1].parents for child in parent.children]
        basicLevels[node] = temp

    ingredients = [x['name'] for x in recipe['ingredients']]

    recipeBasicLevels = {}
    for ingredient in ingredients:
        node = graph.pick_one(ingredient)
        if node:
            temp = [child for parent in node.parents for child in parent.children]
            #recipeBasicLevels[(ingredient,node)] = temp
            recipeBasicLevels[ingredient] = temp

    #intersections = intersect(basicLevelList, recipeBasicLevelList) #gets the ingredient nodes that appear in the basic levels for the common items in "X" cusine and the recipe that was inputted
    substitutes = defaultdict(list)
    for ingredient in recipeBasicLevels:
        for node in basicLevels:
            if intersect(recipeBasicLevels[ingredient],basicLevels[node]):
                if node[0] != ingredient:
                    substitutes[ingredient].append(node[0])

    return substitutes
def intersect(a, b):
    return list(set(a) & set(b))

#Globals for Scentence Splitting
caps = "([A-Z])"
prefixes = "(Mr|St|Mrs|Ms|Dr)[.]"
suffixes = "(Inc|Ltd|Jr|Sr|Co)"
starters = "(Mr|Mrs|Ms|Dr|He\s|She\s|It\s|They\s|Their\s|Our\s|We\s|But\s|However\s|That\s|This\s|Wherever)"
acronyms = "([A-Z][.][A-Z][.](?:[A-Z][.])?)"
websites = "[.](com|net|org|io|gov)"
digits = "([0-9])"

def split_into_sentences(text):
    text = " " + text + "  "
    text = text.replace("\n"," ")
    text = re.sub(prefixes,"\\1<prd>",text)
    text = re.sub(websites,"<prd>\\1",text)
    if "Ph.D" in text: text = text.replace("Ph.D.","Ph<prd>D<prd>")
    text = re.sub("\s" + caps + "[.] "," \\1<prd> ",text)
    text = re.sub(acronyms+" "+starters,"\\1<stop> \\2",text)
    text = re.sub(caps + "[.]" + caps + "[.]" + caps + "[.]","\\1<prd>\\2<prd>\\3<prd>",text)
    text = re.sub(caps + "[.]" + caps + "[.]","\\1<prd>\\2<prd>",text)
    text = re.sub(" "+suffixes+"[.] "+starters," \\1<stop> \\2",text)
    text = re.sub(" "+suffixes+"[.]"," \\1<prd>",text)
    text = re.sub(" " + caps + "[.]"," \\1<prd>",text)
    if "”" in text: text = text.replace(".”","”.")
    if "\"" in text: text = text.replace(".\"","\".")
    if "!" in text: text = text.replace("!\"","\"!")
    if "?" in text: text = text.replace("?\"","\"?")
    text = text.replace(".",".<stop>")
    text = text.replace("?","?<stop>")
    text = text.replace("!","!<stop>")
    text = text.replace("<prd>",".")
    text = re.sub(digits + "[.]" + digits,"\\1<prd>\\2",text)
    sentences = text.split("<stop>")
    sentences = sentences[:-1]
    sentences = [s.strip() for s in sentences]
    return sentences



# Functions to trace references to methods/ingredients in a recipe.

def find_whole_word(sentence, word):
    return word in nltk.word_tokenize(sentence)

def ingredient_references(recipe, graph=graph):
    """Given a recipe and a food graph, a list of ingredient nodes used in each step."""
    refs = []
    for index, step in enumerate(recipe['structuredsteps']):
        step_refs = []
        for ingredient in step['ingredients']:
            step_refs.append(graph.pick_one(ingredient))
        refs.append(step_refs)
    return refs

def method_references(recipe):
    """Return the list of methods used in each step."""
    return [step['methods'] for step in recipe['structuredsteps']]

