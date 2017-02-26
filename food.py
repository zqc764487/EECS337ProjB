# food.py
# Python classes and methods for handling food taxonomy.

from nltk import wordnet
wn = wordnet.wordnet

class Node(object):
	def __init__(self, synset=None, lemmas=None, properties=None,
						parents=None, children=None, cancels=None):
		self.synset = synset				# WordNet synset corresponding to the node.
		self.lemmas = lemmas or [l.name() for l in self.synset.lemmas()] \
					if self.synset and hasattr(self.synset, 'lemmas') else []	# Lemmas that may refer to the node.
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

	def __str__(self):
		return '<Node %s>' % self.synset_name()

	def __repr__(self):
		return '<Node %s>' % self.synset_name()

	def synset_name(self):
		if isinstance(self.synset, basestring):
			return self.synset
		return self.synset.name()

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

def make_wn_subgraph(synset, max_depth=-1, index=None, toplevel=True):
	"""
	Given a WordNet synset, construct a graph of Nodes corresponding to
	all the hyponyms of that synset up to max_depth.  A negative max_depth
	means the depth is unbounded.  index and toplevel are used internally.

	Returns the root node of the graph and an index of all synsets in it.
	"""

	# Initial setup.
	index = index or {}
	graph = index[synset] if synset in index else Node(synset=synset)
	index[synset] = graph
	
	# Recursively attach WordNet hyponyms to the graph.
	if max_depth != 0:
		for hyp in synset.hyponyms():
			subgraph, index = make_wn_subgraph(hyp, max_depth=max_depth-1, index=index, toplevel=False)
			graph.add_child(subgraph)

	# Make any other connections needed using the populated index.
	if toplevel: # Only do this once.
		def connect_parents(node):
			for hyp in node.synset.hypernyms():
				# We only care about synsets that are part of the subgraph.
				if hyp in index:
					index[hyp].add_child(node)
		graph.walk_descendants(connect_parents)
	return graph, index

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

def make_food_graph():
	return make_wn_subgraph(wn.synset('food.n.01'))

def make_lemma_index(index):
	"""Converts a {synset: Node} index into a {lemma: Node} index."""
	lemma_index = {}
	for syn in index:
		for lemma in syn.lemmas():
			lemma_index[lemma.name()] = index[syn]
	return lemma_index

# graph, index = make_food_graph()
# lemmas = make_lemma_index(index)