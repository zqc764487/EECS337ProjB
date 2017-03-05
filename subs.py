# subs.py
# Functions for automatically extracting food substitutes.

import urllib
from bs4 import BeautifulSoup

def make_soup(url):
	page = urllib.urlopen(url).read()
	return BeautifulSoup(page, 'html.parser')

# Scrape from foodsubs.com.

FS_URL = 'http://foodsubs.com/'
FS_SYN_FILE = 'resources/fs_synonyms.txt'
FS_SUB_FILE = 'resources/fs_substitutes.txt'

def fs_scrape_categories(url=FS_URL):
	soup = make_soup(url)
	# Look for the table with a 'Categories' header.
	tds = soup('td')
	cat_tds = [td for td in tds if 'Categories' in td.text]
	categories = []
	for td in cat_tds:
		for a in td.find_all('a', attrs={'href': True}):
			categories.append(a['href'])
	return categories

def fs_scrape_links(url):
	soup = make_soup(url)
	return [a['href'] for a in soup.find_all('a', attrs={'href': True})]

def fs_make_substitutes(url):
	soup = make_soup(url)
	synonyms = []
	substitutes = []
	ps = [p for p in soup('p') if 'Substitutes:' in p.get_text()]
	for p in soup('p'):
		ptext = ' '.join(p.get_text().encode('utf8').split())
		if 'Substitutes:' in ptext:
			bolds = p('b')
			print len(bolds), bolds[0].split(' = ')
			psyns = bolds[0].split(' = ')
			# Hack off any headers that got in there.
			if psyns and psyns[-1].strip().endswith(':'):
				psyns[-1] = psyns[-1].split()[:-1]
			synonyms.append(psyns)
			psubs = []
			sections = ptext.split(':')
			for i in xrange(len(sections)):
				s = sections[i]
				s_next = sections[i+1] if i + 1 < len(sections) else None
				if s.endswith('Substitutes') and s_next:
					ssubs = s_next.split(' OR ')
					if i + 2 < len(sections) and ssubs:
						ssubs[-1] = ssubs[-1].split()[:-1]
					for sub in ssubs:
						if '(' in sub:
							sub = sub[:sub.index('(')].strip()
						psubs.append(sub)
			substitutes.append(psubs)
	return synonyms, substitutes


