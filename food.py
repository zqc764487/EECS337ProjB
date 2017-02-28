# food.py
# Python classes and methods for handling food taxonomy.

from nltk import wordnet
wn = wordnet.wordnet

class Index(dict):
	def __init__(self):
		self.lemmas = {}

class Node(object):
	def __init__(self, name=None, synset=None, lemmas=None, properties=None,
						parents=None, children=None, cancels=None, index=None):
		self.synset = synset				# WordNet synset corresponding to the node.
		self.name = name or (self.synset.name() if self.synset else None)
		self.lemmas = lemmas or [l.name() for l in self.synset.lemmas()] \
					if self.synset else []	# Lemmas that may refer to the node.
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

	def pick_one(self, query):
		if query in self.lemmas:
			return self.lemmas[query]
		for lemma in self.lemmas:
			if query in lemma:
				return self.lemmas[lemma][0]
		return None

	def search(self, query, n=None):
		results = [self.index[name] for name in self.index if query in name]
		return results[:n] if n else results

	def search_lemmas(self, query, n=None):
		results = [node for lemma in self.index.lemmas if query in lemma for node in self.index.lemmas[lemma]]
		return results[:n] if n else results

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

def wn_subgraph(synsets, max_depth=-1, index=None, toplevel=True):
	"""
	Given a list of WordNet synsets, construct a Graph of Nodes corresponding
	to all the hyponyms of those synsets up to max_depth.  A negative max_depth
	means the depth is unbounded.  index and toplevel are used internally.

	Returns the Nodes in the graph corresponding to each synset.
	"""

	# Initial setup.
	index = index or {}
	roots = [index[synset] if synset in index else Node(synset=synset, index=index)\
				for synset in synsets]

	# Recursively attach WordNet hyponyms to the graph.
	if max_depth != 0:
		for root in roots:
			hyps = synset.hyponyms()
			children = wn_subgraph(hyps, max_depth=max_depth-1, index=index, toplevel=False)
			root.add_children(children)

	# Make any other connections needed using the populated index.
	if toplevel: # Only do this once.
		def connect_parents(node):
			for hyp in node.synset.hypernyms():
				# We only care about synsets that are part of the subgraph.
				if hyp in index:
					index[hyp].add_child(node)
		for root in roots:
			root.walk_descendants(connect_parents)
	return roots

def make_sample_graph():
	food = Node(synset='food')
	fruit = Node(synset='fruit', properties=['fruit'], parents=[food])
	animal = Node(synset='animal product', properties=['animal'], parents=[food])
	eggs = Node(synset='eggs', parents=[animal])
	dairy = Node(synset='dairy', properties=['dairy'], parents=[animal])
	cheese = Node(synset='cheese', properties=['base'], parents=[dairy])
	meat = Node(synset='meat', properties=['meat', 'base'], parents=[animal])
	red_meat = Node(synset='red_meat', properties=['base'], parents=[meat])
	beef = Node(synset='beef', parents=[red_meat])
	fish = Node(synset='fish', parents=[meat], properties=['fish', 'base'])
	rockfish = Node(synset='rockfish', parents=[fish])
	catfish = Node(synset='catfish', parents=[fish])
	poultry = Node(synset='poultry', parents=[meat], properties=['poultry', 'base'])
	chicken = Node(synset='chicken', parents=[poultry])
	turkey = Node(synset='turkey', parents=[poultry])

	tofu = Node(synset='tofu', properties=['tofu'])
	protein = Node(synset='protein', properties=['protein'], children=[meat, fish, poultry, tofu], parents=[food])
	tofurkey = Node(synset='tofurkey', parents=[tofu, turkey], cancels=[meat])

	return food

#def read_file_to_graph(file, graph=None):

def food_graph(files=None):
	roots = wn_subgraph([wn.synset('food.n.01'), wn.synset('food.n.02')])
	#if files:
	#	for file in files:
	#		read_file_to_graph()
	return graph

# graph = food_graph()
# lemmas = make_lemma_index(index)

# TODO:
# -Read graph additions from .txt/.csv file.
# -