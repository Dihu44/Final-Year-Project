"""
The majority of this code was extracted from a textbooks companion github repository.
I merely provided the implementation of another scoring function, BM25
"""

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
        title = url.split('/')[-1]
        docwords = words(text)
        docid = len(self.documents)
        self.documents.append(Document(title, url, len(docwords)))
        for word in docwords:
            if word not in self.stopwords:
                self.index[word][docid] += 1

    def queryBM25(self, query_text, n=10, k=2.0, b=0.75):
        """Return a list of n (score, docid) pairs for the best matches using BM25."""
        qwords = [w for w in words(query_text) if w not in self.stopwords]
        shortest = min(qwords, key=lambda w: len(self.index[w]))
        docids = self.index[shortest]
        return heapq.nlargest(n, ((self.total_scoreBM25(qwords, docid, k, b), docid) for docid in docids))

    def query(self, query_text, n=10):
        """Return a list of n (score, docid) pairs for the best matches."""
        qwords = [w for w in words(query_text) if w not in self.stopwords]
        shortest = min(qwords, key=lambda w: len(self.index[w]))
        docids = self.index[shortest]
        return heapq.nlargest(n, ((self.total_score(qwords, docid), docid) for docid in docids))

    def score(self, word, docid):
        """Compute a score for this word on the document with this docid."""
        # There are many options; here we take a very simple approach
        return np.log(1 + self.index[word][docid]) / np.log(1 + self.documents[docid].nwords)

    def scoreBM25(self, word, docid, k=2.0, b=0.75):
        """Compute a score for this word on the document with this docid using BM25."""
        term_frequency = self.index[word][docid]
        document_frequency = len(self.index[word])

        doc_len = self.documents[docid].nwords
        avg_doc_len = sum(doc.nwords for doc in self.documents) / len(self.documents)

        inverse_document_frequency = math.log((len(self.documents) - document_frequency + 0.5) / (document_frequency + 0.5) + 1)

        score = (term_frequency * (k + 1)) / (term_frequency + k * (1 - b + b * doc_len / avg_doc_len))

        return score * inverse_document_frequency
        

    def total_scoreBM25(self, words, docid, k=2.0, b=0.75):
        """Compute the sum of the scores using BM25 of these words on the document with this docid."""
        return sum(self.scoreBM25(word, docid, k, b) for word in words)

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

    def present_resultsBM25(self, query_text, n=10, k=2.0, b=0.75):
        """Get results for the query using the BM25 scoring function and present them"""
        return self.present(self.queryBM25(query_text, n, k, b))

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
