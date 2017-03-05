# food.py
# Python classes and methods for handling food taxonomy.

from nltk import wordnet
wn = wordnet.wordnet
from util import loadCategorization

# Category lists.
CATEGORY_FILES = []
# Substitution lists.
SUBSTITUTE_FILES = ['resources/VegetarianIngredientSubstitutes.csv', 'resources/fs_substitutes.txt']
# Synonym lists.
SYNONYM_FILES = ['resources/fs_synonyms.txt']
# Properties to attach to various nodes.
PROPERTIES_FILES = ['resources/food_properties.txt']

def _strip_local(prop):
	if prop.startswith('.'):
		return prop[1:]
	return prop

def _strip_pos(prop):
	if prop.startswith('+'):
		return prop[1:]
	return prop

def _strip_neg(prop):
	if prop.startswith('-'):
		return prop[1:]
	return prop

def _make_local(prop):
	if prop.startswith('+'):
		return '.' + prop[1:]
	elif not prop.startswith('-') and not prop.startswith('.'):
		return '.' + prop
	return prop

def _make_pos(prop):
	if prop.startswith('+'):
		return prop
	elif prop.startswith('-') or prop.startswith('.'):
		return '+' + prop[1:]
	else:
		return '+' + prop

def _make_neg(prop):
	if prop.startswith('-'):
		return prop
	elif prop.startswith('+') or prop.startswith('.'):
		return '-' + prop[1:]
	else:
		return '-' + prop

def property_match(prop, plist):
	"""
	Return True if property prop matches the list of properties plist.

	There are three types of properties:
		+prop = positive properties
		-prop = negative properties
		.prop = local properties
	Properties without a +, -, or . are considered positive.  Local
	properties are also considered positive but do not inherit.
	
	A positive property will match a plist if a positive form of that
	property appears in the plist and no negative form does.

	A negative property will match a plist if a negative form of that
	property appears in the plist or no positive form does.
	"""
	prop = _strip_pos(prop)
	plist = [_strip_pos(p) for p in plist]
	if prop.startswith('-'):
		return prop in plist or (_strip_neg(prop) not in plist and \
			_make_local(_strip_neg(prop)) not in plist)
	else:
		return prop in plist and _make_neg(prop) not in plist

def all_properties(node, plist):
	"""
	Return True if the node's properties match the list of properties
	plist.

	The properties in plist can be positive, indicating the node must
	have that property; negative, indicating the node must not have
	that property; or local, indicating that the property must be on
	that node and not inherited.
	"""
	if not plist:
		return True
	props = [_strip_pos(p) for p in node.get_properties(local=True)]
	plist = [_strip_pos(p) for p in plist]
	return all(property_match(p, props) for p in plist)

class Index(dict):
	def __init__(self):
		self.lemmas = {}

	def search(self, query=None, n=None, properties=None):
		if query:
			results = [self[name] for name in self if name.find(query) >= 0]
		else:
			results = self.values()
		if properties: # List of properties that must be directly on the node.
			results = [r for r in results if all_properties(r, properties)]
		return results[:n] if n else results

	def search_lemmas(self, query=None, n=None, properties=None):
		if query:
			results = [node for lemma in self.lemmas if lemma.find(query) >= 0 for node in self.lemmas[lemma]]
		else:
			results = self.values()
		if properties: # List of properties that must be directly on the node.
			results = [r for r in results if all_properties(r, properties)]
		return results[:n] if n else results

	def pick_one(self, query=None, properties=None):
		if not query:
			results = self.values()
			for result in results:
				if all_properties(result, properties):
					return result
		if query in self:
			if all_properties(self[query], properties):
				return self[query]
		if query in self.lemmas:
			for result in self.lemmas[query]:
				if all_properties(result, properties):
					return result
		for lemma in self.lemmas:
			if lemma.find(query) >= 0 and len(self.lemmas[lemma]) > 0:
				for result in self.lemmas[lemma]:
					if all_properties(result, properties):
						return result
		return None

class Node(object):
	def __init__(self, name=None, synset=None, lemmas=None, properties=None,
						parents=None, children=None, cancels=None, index=None):
		self.synset = synset
		self.name = name or (self.synset.name() if self.synset else None)

		# Use assigned index or first index found among parents, then children.
		# If no indexes are found, create one.
		if index is None:
			indexes = [node.index for node in self.parents + self.children if node.index]
			index = indexes[0] if len(indexes) > 0 else Index()
		self.index = index
		if self.name:
			self.index[self.name] = self

		self.lemmas = []
		self.properties = []
		self.parents = []
		self.children = []
		self.cancels = []
	
		if lemmas:
			self.add_lemmas(lemmas)
		elif self.synset:
			self.add_lemmas([l.name() for l in self.synset.lemmas()])
		else:
			self.add_lemma(self.name)
	
		if properties:
			self.add_properties(properties)
		if parents:
			self.add_parents(parents)
		if children:
			self.add_children(children)
		if cancels:
			self.add_cancels(cancels)
	
	def __str__(self):
		return '<Node %s>' % self.name

	def __repr__(self):
		return '<Node %s>' % self.name

	def __len__(self):
		return len(self.index)

	def search(self, query=None, n=None, properties=None):
		raw_results = self.index.search(query=query, properties=properties) + \
						self.index.search_lemmas(query=query, properties=properties)
		results = []
		for result in raw_results:
			if result not in results:
				results.append(result)
		return results[:n] if n else results

	def pick_one(self, query=None, properties=None):
		return self.index.pick_one(query=query, properties=properties)

	def add_lemma(self, lemma):
		if lemma not in self.lemmas:
			self.lemmas.append(lemma)
		if lemma not in self.index.lemmas:
			self.index.lemmas[lemma] = []
		if self not in self.index.lemmas[lemma]:
			self.index.lemmas[lemma].append(self)

	def add_lemmas(self, lemmas):
		for lemma in lemmas:
			self.add_lemma(lemma)

	def add_property(self, property):
		if property not in self.properties:
			self.properties.append(property)

	def add_properties(self, properties):
		for property in properties:
			self.add_property(property)

	def add_parent(self, parent):
		if parent not in self.parents:
			self.parents.append(parent)
		if self not in parent.children:
			parent.children.append(self)

	def add_parents(self, parents):
		for parent in parents:
			self.add_parent(parent)

	def add_child(self, child):
		if child not in self.children:
			self.children.append(child)
		if self not in child.parents:
			child.parents.append(self)

	def add_children(self, children):
		for child in children:
			self.add_child(child)

	def add_cancel(self, cancel):
		self.cancels.append(cancel)

	def add_cancels(self, cancels):
		self.cancels += cancels

	def walk_descendants(self, fn, before=True, test=False, properties=None):
		"""
		Walk down the graph and call function fn on every node along the
		way.
		
		before determines when fn will be called.  If before is True,
		fn will be called on a Node before it is called on its descendants.
		Otherwise it will be called after.

		test determines whether fn acts as a test.  If test is True,
		the walk will stop when fn returns any non-false value and return
		that value.  Otherwise the results of fn will be ignored and the
		walk will return nothing.

		properties determines whether fn will be called for a given node.
		If properties is None, fn will always be called.  If properties is a
		property list, fn will only be called on nodes that match
		the property list.
		"""
		if before and all_properties(self, properties):
			result = fn(self)
			if test and result:
				return result
		for child in self.children:
			child.walk_descendants(fn, before=before, test=test, properties=properties)
		if not before and all_properties(self, properties):
			result = fn(self)
			if test and result:
				return result
		return None

	def walk_ancestors(self, fn, before=True, test=False, properties=None,
						cancels=None):
		"""
		Walk up the graph and call function fn on every node along the
		way.
		
		before determines when fn will be called.  If before is True,
		fn will be called on a Node before it is called on its ancestors.
		Otherwise it will be called after.

		test determines whether fn acts as a test.  If test is True,
		the walk will stop when fn returns any non-false value and return
		that value.  Otherwise the results of fn will be ignored and the
		walk will return nothing.

		properties determines whether fn will be called for a given node.
		If properties is None, fn will always be called.  If properties is a
		property list, fn will only be called on nodes that match
		the property list.

		cancels is used internally.
		"""
		cancels = self.cancels + (cancels or [])
		if before and all_properties(self, properties):
			result = fn(self)
			if test and result:
				return result
		for parent in self.parents:
			if parent not in cancels:
				parent.walk_ancestors(fn, before=before, test=test, properties=properties, cancels=cancels)
		if not before and all_properties(self, properties):
			result = fn(self)
			if test and result:
				return result
		return None

	def has_property(self, property):
		# There's probably a quicker way to do this with walk_ancestors and test=True.
		# However, taking +prop and -prop into account makes this nontrivial.
		# Therefore let's just use get_properties.
		return check_property(property, self.get_properties())

	def get_properties(self, local=False):
		# If local, pretend all positive direct properties are local.
		if local:
			properties = [_make_local(p) for p in self.properties if not p.startswith('-')]
		else:
			properties = [p for p in self.properties if p.startswith('.')] # Begin with local properties.
		def add_properties(n):
			for p in n.properties:
				if not p.startswith('.') and p not in properties and _make_local(p) not in properties:
					properties.append(p)
		self.walk_ancestors(add_properties)
		return properties

	# Broken.
	"""def first_ancestor_with_prop(self, property):
		if property in self.properties:
			return self
		queue = [parent for parent in self.parents]
		while queue:
			item, queue = queue[0], queue[1:]
			if property in item.properties:
				return item
		return None"""

	def ancestors(self):
		ancestors = []
		queue = [parent for parent in self.parents]
		while queue:
			item, queue = queue[0], queue[1:]
			if item not in ancestors:
				ancestors.append(item)
			queue += item.parents
		return ancestors

	def shared_ancestor(self, other):
		other_ancestors = other.ancestors()
		best_ancestor, best_position = None, len(other_ancestors)
		for a in self.ancestors():
			if a in other_ancestors:
				p = other_ancestors.index(a)
				if p < best_position:
					best_ancestor, best_position = a, p
		return best_ancestor

	def is_a(self, ancestor):
		if self == ancestor:
			return True
		for parent in self.parents:
			if parent.is_a(ancestor):
				return True
		return False

	def print_graph(self, tab=0):
		print '\t' * tab + str(self)
		for child in self.children:
			child.print_graph(tab=tab+1)

	def get_substitutes(self, properties=None):
		"""Find a substitute for this node consistent with the given properties."""
		sub_nodes = []
		self.walk_ancestors(lambda n: sub_nodes.append(n), properties=['.substitute'])
		subs = []
		for sub_node in sub_nodes:
			for child in sub_node.children:
				if child != self and child not in subs and all_properties(child, properties):
					subs.append(child)
		return subs

def wn_subgraph(synsets, max_depth=-1, index=None, toplevel=True):
	"""
	Given a list of WordNet synsets, construct a Graph of Nodes corresponding
	to all the hyponyms of those synsets up to max_depth.  A negative max_depth
	means the depth is unbounded.  index and toplevel are used internally.
	
	Returns the root of the graph if toplevel if True, otherwise returns the
	nodes corresponding to each synset given.
	"""

	# Initial setup.
	index = index or Index()
	roots = [index[synset.name()] if synset.name() in index else\
				Node(synset=synset, index=index) for synset in synsets]

	# Recursively attach WordNet hyponyms to the graph.
	if max_depth != 0:
		for root in roots:
			hyps = root.synset.hyponyms()
			children = wn_subgraph(hyps, max_depth=max_depth-1, index=index, toplevel=False)
			root.add_children(children)

	# Make any other connections needed using the populated index.
	if toplevel: # Only do this once.
		root = Node(name='<root>', index=index, children=roots)
		def connect_parents(node):
			if node.synset:
				for hyp in node.synset.hypernyms():
					# We only care about synsets that are part of the subgraph.
					if hyp.name() in index:
						index[hyp.name()].add_child(node)
		root.walk_descendants(connect_parents)
		return root
	# Return the roots if not toplevel.
	return roots

def sample_graph():
	food = Node(name='food')
	fruit = Node(name='fruit', properties=['fruit'], parents=[food])
	animal = Node(name='animal product', properties=['animal'], parents=[food])
	eggs = Node(name='eggs', parents=[animal])
	dairy = Node(name='dairy', properties=['dairy'], parents=[animal])
	cheese = Node(name='cheese', properties=['base'], parents=[dairy])
	meat = Node(name='meat', properties=['meat', 'base'], parents=[animal])
	red_meat = Node(name='red_meat', properties=['base'], parents=[meat])
	beef = Node(name='beef', parents=[red_meat])
	fish = Node(name='fish', parents=[meat], properties=['fish', 'base'])
	rockfish = Node(name='rockfish', parents=[fish])
	catfish = Node(name='catfish', parents=[fish])
	poultry = Node(name='poultry', parents=[meat], properties=['poultry', 'base'])
	chicken = Node(name='chicken', parents=[poultry])
	turkey = Node(name='turkey', parents=[poultry])

	tofu = Node(name='tofu', properties=['tofu'], parents=[food])
	protein = Node(name='protein', properties=['protein'], children=[meat, fish, poultry, tofu], parents=[food])
	tofurkey = Node(name='tofurkey', parents=[tofu, turkey], cancels=[meat])

	return food

def read_category_files(files, graph=None):
	"""
	Reads food categories from a file either converts them to a graph or adds them
	to an existing one, based on whether graph is given.  Attempts to convert category
	names into nodes based on node names, then lemmas.

	Return either the original graph or a root node for the new graph.
	"""
	index = graph.index if graph else Index()
	roots = []
	for file in files:
		for category, members in loadCategorization(file).iteritems():
			category, members = category.strip(), [member.strip() for member in members]
			root = index.pick_one(category) or Node(name=category, index=index)
			roots.append(root)
			for member in members:
				child = index.pick_one(member) or Node(name=member, index=index)
				child.add_parent(root)
	return graph if graph else Node(name='<root>', index=index, children=roots)

def read_substitute_files(files, graph=None):
	"""
	Reads food substitutions from a file either converts them to a graph or adds them
	to an existing one, based on whether graph is given.  Attempts to convert category
	names into nodes based on node names, then lemmas.

	Return either the original graph or a root node for the new graph.
	"""
	index = graph.index if graph else Index()
	roots = []
	for file in files:
		for category, members in loadCategorization(file).iteritems():
			category, members = category.strip(), [member.strip() for member in members]
			base = index.pick_one(category) or Node(name=category, index=index)
			name = category + ' substitutes'
			root = index.pick_one(name) or Node(name=name, index=index, properties=['.substitute'])
			root.add_child(base)
			roots.append(root)
			for member in members:
				child = index.pick_one(member) or Node(name=member, index=index)
				child.add_parent(root)
	return graph if graph else Node(name='<root>', index=index, children=roots)

def read_property_files(files, graph, signal=False):
	"""
	Reads food properties from a file and adds those properties to the graph.
	Attempts to convert food names into nodes based on node names, then lemmas.
	
	If signal, print a warning every time a nonexistent node is given properties.

	Return the graph.
	"""
	for file in files:
		for category, properties in loadCategorization(file).iteritems():
			category, properties = category.strip(), [property.strip() for property in properties]
			root = graph.pick_one(category)
			if root:
				root.add_properties(properties)
			else:
				root = Node(name=category, index=graph.index, properties=properties)
				if signal:
					sys.stderr.write('Warning: Node %s created with properties %s.\n' % (category, properties))
	return graph

def read_synonym_files(files, graph, signal=False):
	"""
	Reads food synonyms from a file and adds those lemmas to the graph.
	Attempts to convert food names into nodes based on node names, then lemmas.
	
	If signal, print a warning every time a nonexistent node is given properties.

	Return the graph.
	"""
	for file in files:
		for category, synonyms in loadCategorization(file).iteritems():
			category, synonyms = category.strip(), [synonym.strip() for synonym in synonyms]
			root = graph.pick_one(category)
			if root:
				root.add_lemmas(synonyms)
			else:
				lemmas = [category] + synonyms if category not in synonyms else synonyms
				root = Node(name=category, index=graph.index, lemmas=lemmas)
				if signal:
					sys.stderr.write('Warning: Node %s created with lemmas %s.\n' % (category, lemmas))
	return graph

def food_graph(cats=CATEGORY_FILES, subs=SUBSTITUTE_FILES, props=PROPERTIES_FILES, syns=SYNONYM_FILES):
	root = wn_subgraph([wn.synset('food.n.01'), wn.synset('food.n.02')])
	if cats:
		read_category_files(cats, graph=root)
	if subs:
		read_substitute_files(subs, graph=root)
	if props:
		read_property_files(props, root, signal=True)
	if syns:
		read_synonym_files(syns, root, signal=True)
	return root
