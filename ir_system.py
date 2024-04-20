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