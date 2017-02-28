# food.py
# Python classes and methods for handling food taxonomy.

from nltk import wordnet
wn = wordnet.wordnet
from util import loadCategorization

FOOD_FILES = ['resources/VegetarianIngredientSubstitutes.csv']

class Index(dict):
	def __init__(self):
		self.lemmas = {}

	def _all_properties(self, node, properties):
		return not properties or all(p in node.properties for p in properties)

	def search(self, query=None, n=None, properties=None):
		if query:
			results = [self[name] for name in self if name.find(query) >= 0]
		else:
			results = self.values()
		if properties: # List of properties that must be directly on the node.
			results = [r for r in results if self._all_properties(r, properties)]
		return results[:n] if n else results

	def search_lemmas(self, query=None, n=None, properties=None):
		if query:
			results = [node for lemma in self.lemmas if lemma.find(query) >= 0 for node in self.lemmas[lemma]]
		else:
			results = self.values()
		if properties: # List of properties that must be directly on the node.
			results = [r for r in results if self._all_properties(r, properties)]
		return results[:n] if n else results

	def pick_one(self, query=None, properties=None):
		if not query:
			results = self.values()
			for result in results:
				if self._all_properties(result, properties):
					return result
		if query in self:
			if self._all_properties(self[query], properties):
				return self[query]
		if query in self.lemmas:
			for result in self.lemmas[query]:
				if self._all_properties(result, properties):
					return result
		for lemma in self.lemmas:
			if lemma.find(query) >= 0 and len(self.lemmas[lemma]) > 0:
				for result in self.lemmas[lemma]:
					if self._all_properties(result, properties):
						return result
		return None

class Node(object):
	def __init__(self, name=None, synset=None, lemmas=None, properties=None,
						parents=None, children=None, cancels=None, index=None):
		self.synset = synset				# WordNet synset corresponding to the node.
		self.name = name or (self.synset.name() if self.synset else None)
		self.lemmas = lemmas or [l.name() for l in self.synset.lemmas()] \
					if self.synset else [self.name]	# Lemmas that may refer to the node.
		self.properties = properties or []	# Properties of the node.
		self.parents = []
		self.children = []
		self.cancels = []
		if parents:
			self.add_parents(parents)
		if children:
			self.add_children(children)
		if cancels:
			self.add_cancels(cancels)
		# Use assigned index or first index found among parents, then children.
		# If no indexes are found, create one.
		if index is None:
			indexes = [node.index for node in self.parents + self.children if node.index]
			index = indexes[0] if len(indexes) > 0 else Index()
		self.index = index
		if self.name:
			self.index[self.name] = self
			for lemma in self.lemmas:
				if lemma not in self.index.lemmas:
					self.index.lemmas[lemma] = []
				self.index.lemmas[lemma].append(self)

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

	def walk_descendants(self, fn, before=True, test=False):
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
		"""
		if before:
			result = fn(self)
			if test and result:
				return result
		for child in self.children:
			child.walk_descendants(fn, before=before, test=test)
		if not before:
			result = fn(self)
			if test and result:
				return result
		return None

	def walk_ancestors(self, fn, before=True, test=False, cancels=None):
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

		cancels is used internally.
		"""
		cancels = self.cancels + (cancels or [])
		if before:
			result = fn(self)
			if test and result:
				return result
		for parent in self.parents:
			if parent not in cancels:
				parent.walk_ancestors(fn, before=before, test=test, cancels=cancels)
		if not before:
			result = fn(self)
			if test and result:
				return result
		return None

	def has_property(self, property):
		return self.walk_ancestors(lambda n: property in n.properties, test=True)

	def get_properties(self):
		properties = []
		self.walk_ancestors(lambda n: properties.extend([p for p in n.properties if p not in properties]))
		return properties

	def first_ancestor_with_prop(self, property):
		if property in self.properties:
			return self
		queue = [parent for parent in self.parents]
		while queue:
			item, queue = queue[0], queue[1:]
			if property in item.properties:
				return item
		return None

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

def read_graph_files(files, graph=None):
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
			base = index.pick_one(category) or Node(name=category, index=index)
			name = category + ' alternatives'
			root = index.pick_one(name) or Node(name=name, index=index, properties=['alternatives'])
			root.add_child(base)
			roots.append(root)
			for member in members:
				child = index.pick_one(member) or Node(name=member, index=index)
				child.add_parent(root)
	return graph if graph else Node(name='<root>', index=index, children=roots)

def food_graph(files=FOOD_FILES):
	root = wn_subgraph([wn.synset('food.n.01'), wn.synset('food.n.02')])
	if files:
		read_graph_files(files, graph=root)
	return root

# graph = food_graph(files=FOOD_FILES)
