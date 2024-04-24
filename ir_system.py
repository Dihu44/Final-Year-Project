from collections import defaultdict
import re
import os
import heapq
import numpy as np
import math

class IRSystem:
    """A very simple Information Retrieval System, as discussed in Sect. 23.2.
    The constructor s = IRSystem('the a') builds an empty system with two
    stopwords. Next, index several documents with s.index_document(text, url).
    Then ask queries with s.query('query words', n) to retrieve the top n
    matching documents. Queries are literal words from the document,
    except that stopwords are ignored, and there is one special syntax:
    The query "learn: man cat", for example, runs "man cat" and indexes it."""

    def __init__(self, stopwords='the a of'):
        """Create an IR System. Optionally specify stopwords."""
        # index is a map of {word: {docid: count}}, where docid is an int,
        # indicating the index into the documents list.
        self.index = defaultdict(lambda: defaultdict(int))
        self.stopwords = set(words(stopwords))
        self.documents = []

    def index_collection(self, filenames):
        """Index a whole collection of files."""
        prefix = os.path.dirname(__file__)
        for filename in filenames:
            self.index_document(open(filename).read(), os.path.relpath(filename, prefix))

    def index_document(self, text, url):
        """Index the text of a document."""
        # For now, use first line for title
        title = text[:text.index('\n')].strip()
        docwords = words(text)
        docid = len(self.documents)
        self.documents.append(Document(title, url, len(docwords)))
        for word in docwords:
            if word not in self.stopwords:
                self.index[word][docid] += 1

    def query(self, query_text, n=10):
        """Return a list of n (score, docid) pairs for the best matches.
        Also handle the special syntax for 'learn: command'."""
        if query_text.startswith("learn:"):
            doctext = os.popen(query_text[len("learn:"):], 'r').read()
            self.index_document(doctext, query_text)
            return []

        qwords = [w for w in words(query_text) if w not in self.stopwords]
        shortest = min(qwords, key=lambda w: len(self.index[w]))
        docids = self.index[shortest]
        return heapq.nlargest(n, ((self.total_score(qwords, docid), docid) for docid in docids))

    def score(self, word, docid):
        """Compute a score for this word on the document with this docid."""
        # There are many options; here we take a very simple approach
        return np.log(1 + self.index[word][docid]) / np.log(1 + self.documents[docid].nwords)

    def total_score(self, words, docid):
        """Compute the sum of the scores of these words on the document with this docid."""
        return sum(self.score(word, docid) for word in words)

    def present(self, results):
        """Present the results as a list."""
        lis = []
        for (score, docid) in results:
            doc = self.documents[docid]
            lis += [("{:5.2}|{:25} | {}".format(100 * score, doc.url, doc.title[:45].expandtabs()))]
        return lis

    def present_results(self, query_text, n=10):
        """Get results for the query and present them."""
        return self.present(self.query(query_text, n))

def words(text, reg=re.compile('[a-z0-9]+')):
    """Return a list of the words in text, ignoring punctuation and
    converting everything to lowercase (to canonicalize).
    >>> words("``EGAD!'' Edgar cried.")
    ['egad', 'edgar', 'cried']
    """
    return reg.findall(text.lower())

class Document:
    """Metadata for a document: title and url; maybe add others later."""

    def __init__(self, title, url, nwords):
        self.title = title
        self.url = url
        self.nwords = nwords

"""
SCORING FUNCTIONS
"""

class BM25:
    def __init__(self, documents, k=2.0, b=0.75):
        self.documents = documents  # List of documents, where each document is a list of terms
        self.k1 = k1  # Tuning parameter (1.5 is a common default value)
        self.b = b  # Tuning parameter (0.75 is a common default value)
        self.N = len(documents)  # Total number of documents
        self.doc_lengths = [len(doc) for doc in documents]  # Length of each document
        self.avg_doc_length = sum(self.doc_lengths) / self.N  # Average document length
        self.term_freqs = defaultdict(lambda: defaultdict(int))
        self.doc_freqs = defaultdict(int)
        self.idfs = {}

        # Compute term frequencies and document frequencies
        self.compute_frequencies()

        # Compute inverse document frequencies
        self.compute_idfs()

    def compute_frequencies(self):
        """Compute term frequencies and document frequencies."""
        for doc_id, doc in enumerate(self.documents):
            seen_terms = set()
            for term in doc:
                self.term_freqs[term][doc_id] += 1
                if term not in seen_terms:
                    self.doc_freqs[term] += 1
                    seen_terms.add(term)

    def compute_idfs(self):
        """Compute inverse document frequencies."""
        for term, doc_freq in self.doc_freqs.items():
            # Calculate IDF using log(N / df)
            self.idfs[term] = math.log((self.N + 1) / (doc_freq + 1)) + 1

    def score(self, query, doc_id):
        """Compute BM25 score for a given query and document."""
        score = 0.0
        doc_length = self.doc_lengths[doc_id]
        doc = self.documents[doc_id]

        for term in query:
            if term in self.term_freqs:
                # Calculate term frequency in the document
                tf = self.term_freqs[term][doc_id]
                # Calculate term frequency using BM25 formula
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * (doc_length / self.avg_doc_length))
                tf_component = numerator / denominator

                # Calculate the BM25 score
                idf = self.idfs[term]
                score += idf * tf_component

        return score

# Example usage
documents = [
    ['hello', 'world', 'foo'],
    ['foo', 'bar', 'baz'],
    ['hello', 'foo', 'bar', 'world']
]

query = ['hello', 'foo']

# Initialize BM25 instance
bm25 = BM25(documents)

# Calculate the BM25 score for the query against each document
for doc_id in range(len(documents)):
    bm25_score = bm25.score(query, doc_id)
    print(f"BM25 score for doc {doc_id}: {bm25_score}")