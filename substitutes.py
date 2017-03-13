# subs.py
# Functions for automatically extracting food substitutes.

import urllib
import string
from bs4 import BeautifulSoup

def make_soup(url):
	page = urllib.urlopen(url).read()
	return BeautifulSoup(page, 'html.parser')

# Scrape from foodsubs.com.

FS_URL = 'http://foodsubs.com/'
FS_SYN_FILE = 'resources/fs_synonyms.txt'
FS_SUB_FILE = 'resources/fs_substitutes.txt'

def fs_master(syn_file=FS_SYN_FILE, sub_file=FS_SUB_FILE):
	syn_list, sub_list = fs_scrape()
	with open(syn_file, 'w') as fout:
		for syns in syn_list:
			if syns and len(syns) >= 2:
				fout.write(','.join(syns) + '\n')
	with open(sub_file, 'w') as fout:
		for subs in sub_list:
			if subs and len(subs) >= 2:
				fout.write(','.join(subs) + '\n')
	return syn_list, sub_list

def fs_scrape(url=FS_URL):
	queue = fs_scrape_categories(url=url)
	queue = [FS_URL + item if not item.startswith('http') else item for item in queue]
	done = set()
	syns, subs = [], []
	while queue:
		item, queue = queue[0], queue[1:]
		if item in done:
			continue
		done.add(item)
		print item
		soup = make_soup(item)
		if 'Substitutes:' in soup.get_text():
			syns_, subs_ = fs_make_substitutes(soup)
			syns += syns_
			subs += subs_
		else:
			links = fs_scrape_links(soup)
			links = [FS_URL + link if not link.startswith('http') else link for link in links]
			links = [link for link in links if link not in done]
			links = [link for link in links if link.startswith(FS_URL)]
			queue += links
	return syns, subs

# Scrape category URLs off the homepage.
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

def fs_scrape_links(soup):
	return [a['href'] for a in soup.find_all('a', attrs={'href': True})]

_printable = set(string.printable)
def _decruft(s):
	return ''.join(filter(lambda x: x in _printable, s)).strip()

def _tokenize(s):
	return [_decruft(s) for s in s.split()]

def _strip_paren(s):
	if '(' in s:
		return s[:s.index('(')].strip()
	return s.strip()

def fs_make_substitutes(soup):
	synonyms = []
	substitutes = []
	targets = soup('p') + soup('td')
	for p in targets:
		ptoks = _tokenize(p.get_text().encode('utf8'))
		ptext = ' '.join(ptoks)
		if 'Substitutes:' in ptext:
			bolds = p('b')
			if bolds:
				#psyns = bolds[0].get_text()
				btoks = _tokenize(bolds[0].get_text().encode('utf8'))
				psyns = ' '.join(btoks).split('=') # ' = '
				# Hack off any headers that got in there.
				if psyns and psyns[-1].strip().endswith(':'):
					psyns[-1] = ' '.join(psyns[-1].split()[:-1])
				psyns = [_strip_paren(psyn) for psyn in psyns]
				synonyms.append(psyns)
				psubs = []
				sections = ptext.split(':')
				for i in xrange(len(sections)):
					s = sections[i]
					s_next = sections[i+1] if i + 1 < len(sections) else None
					if s.endswith('Substitutes') and s_next:
						ssubs = s_next.split('OR')
						if i + 2 < len(sections) and ssubs:
							ssubs[-1] = ssubs[-1].split()[:-1]
						for sub in ssubs:
							sub = _strip_paren(''.join(sub))
							psubs.append(sub)
				substitutes.append(psubs)
	return synonyms, substitutes

