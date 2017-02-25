# food.py
# Python classes and methods for handling food taxonomy.

from nltk import wordnet
wn = wordnet.wordnet

class Node(object):
	def __init__(self, synset=None, lemmas=None, properties=None,
						parents=None, children=None, cancels=None):
		self.synset = synset				# WordNet synset corresponding to the node.
		self.lemmas = lemmas or [l.name() for l in self.synset.lemmas()] \
					if self.synset else []	# Lemmas that may refer to the node.
		self.properties = properties or []	# Properties of the node.
		self.parents = parents or []		# Nodes this node inherits properties from in the hierarchy.
		self.children = children or []		# Nodes that inherit properties from this node in the hierarchy.
		self.cancels = cancels or []		# Nodes this node should NOT inherit properties from.

	def __str__(self):
		return '<Node %s>' % self.synset.name()

	def __repr__(self):
		return '<Node %s>' % self.synset.name()

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

	def walk_graph(self, fn, before=True):
		"""
		Walk down the graph and call function fn on every node along the
		way.  If before is True, fn will be called on a Node before it is
		called on its descendants.  If before is False, fn will be called
		on the node after it has been called on its descendants.
		"""
		if before:
			fn(self)
		for child in self.children:
			child.walk_graph(fn, before=before)
		if not before:
			fn(self)

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
		graph.walk_graph(connect_parents)
	return graph, index

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