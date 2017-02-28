# crawl.py
# Utilities for crawling AllRecipes.com and collecting a sample set.

from bs4 import BeautifulSoup
import requests as r

RECIPE_FILE = 'resources/recipe_set.txt'
BASE_URL = 'http://allrecipes.com'

def parse_url(url):
	return BeautifulSoup(r.get(url).content, 'html.parser')

def similar_links(page):
	soup = url if isinstance(page, BeautifulSoup) else parse_url(page)
	return [a['href'] for a in soup.find_all('a', attrs={'data-internal-referrer-link': 'similar_recipe_banner'})]

def read_recipe_file(file=RECIPE_FILE):
	with open(RECIPE_FILE) as fin:
		return [l.strip() for l in fin]

def write_recipe_file(links, file=RECIPE_FILE):
	with open(RECIPE_FILE, 'w') as fout:
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
