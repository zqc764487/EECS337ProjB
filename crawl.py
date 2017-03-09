# crawl.py
# Utilities for crawling AllRecipes.com and collecting a sample set.

from bs4 import BeautifulSoup
import requests as r
import urllib
from urlparse import urljoin
from recipe import *
from collections import Counter

FREQ_FILE_I = 'resources/freq_set_i.txt'
FREQ_FILE_F = 'resources/freq_set_f.txt'
FREQ_FILE_G = 'resources/freq_set_g.txt'
FREQ_FILE_A = 'resources/freq_set_a.txt'
RECIPE_FILE = 'resources/recipe_set.txt'
RECIPE_INDIAN_FOOD = 'resources/indian_recipe_set.txt'
RECIPE_FRENCH_FOOD = 'resources/french_recipe_set.txt'
RECIPE_GERMAN_FOOD = 'resources/german_recipe_set.txt'
RECIPE_AFRICAN_FOOD = 'resources/african_recipe_set.txt'



BASE_URL = 'http://allrecipes.com'

def parse_url(url):
	return BeautifulSoup(r.get(url).content, 'html.parser')

def similar_links(page):
	soup = url if isinstance(page, BeautifulSoup) else parse_url(page)
	return [a['href'] for a in soup.find_all('a', attrs={'data-internal-referrer-link': 'similar_recipe_banner'})]

def read_recipe_file(file=RECIPE_FILE):
	with open(file) as fin:
		return [l.strip() for l in fin]

def write_recipe_file(links, file=RECIPE_FILE):
	with open(file, 'w') as fout:
		fout.writelines([l + '\n' for l in links])

def crawl(links, queue, limit=100):
	while len(links) < limit and queue:
		link, queue = queue[0], queue[1:]
		print 'Processing:', link
		similar = similar_links(link)
		for s in similar:
			if s[0] == '/':
				s = BASE_URL + s
			if s not in links:
				print 'Added to queue:', s
				links.append(s)
				queue.append(s)
			else:
				print 'Skipped:', s
	return links



#Traverse recipe

def collect_recipe_file(links, file=RECIPE_AFRICAN_FOOD):
	with open(RECIPE_AFRICAN_FOOD, 'a+') as fout:
		fout.writelines([l + '\n' for l in links])



def fetchRecipeURL(input_url):
    r = urllib.urlopen(input_url).read()
    soup = BeautifulSoup(r, "html.parser")
    baseSite = 'http://allrecipes.com'
    links = set()
    if 'File Not Found' not in soup.find_all('title'):
	    for article in soup.find_all('article', attrs={'class':'grid-col--fixed-tiles'}):
	        for link in article('a', attrs={'href':True}):
	            if link['href'].startswith('/recipe'):
	                links.add(urljoin(baseSite, link['href']))   
    return links


def traverseRecipeURL(input_url, page_amount):
	baseURL = input_url
	link_set = set()
	params = '?page=' if baseURL.endswith("/") else '&page='
	for i in range(1, page_amount+1):
		print "Processing page: " + str(i)
		url = baseURL + params + str(i)
		returned_links = fetchRecipeURL(url)
		if returned_links:
			link_set = link_set.union(fetchRecipeURL(url)) 
			print fetchRecipeURL(url)
		else:  
			print str(i-1) + " pages has been processed."
			collect_recipe_file(link_set, RECIPE_AFRICAN_FOOD)
			return 
	collect_recipe_file(link_set, RECIPE_AFRICAN_FOOD)



def write_freq_file(links, file):
	with open(RECIPE_FILE, 'a+') as fout:
		fout.writelines([l + '\n' for l in links])


def freq_ingredient(read_file, write_file):
	recipe_list = read_recipe_file(read_file)
	cnt = Counter()
	for recipe in recipe_list:
		temp = fetch_recipe(recipe)
		print "Processing..."
		for ingredient in temp.get('ingredients'):
			cnt[ingredient.get('name')] += 1


	for x, v in cnt.most_common():
		with open(write_file, 'a+') as fout:
			fout.write(str(x) + ": " + str(v) + "\n")

def order_freq(cusine_freq):
	total = 0
	for ingredient in cusine_freq:
		if ingredient:
			total += cusine_freq[ingredient]
	retList = []
	for ingredient in cusine_freq:
		if (float(cusine_freq[ingredient])/float(total) >= .0005):
			retList.append(ingredient)

	return retList




def read_freq_file(file=FREQ_FILE_I):
	d = {}
	with open(file) as fin:
		for line in fin:
			(key, val) = line.split(': ')
			val = re.sub('\n', '', val)
			d[str(key)] = int(val)
	return d