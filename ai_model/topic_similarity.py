from sentence_transformers import SentenceTransformer, util
import numpy as np

class TopicSimilarityModel:
    def __init__(self, model_name='all-mpnet-base-v2'):
        """
        Initialize the TopicSimilarityModel with a pre-trained Sentence-BERT model.
        
        :param model_name: Name of the pre-trained SentenceTransformer model.
        """
        self.model = SentenceTransformer(model_name)
    
    def find_similar_topics(self, product_topics, relevant_topics, threshold=0.5):
        """
        Find similar topics from a list of relevant topics efficiently.
        
        :param product_topics: List of topics related to the product.
        :param relevant_topics: List of all possible relevant topics.
        :param threshold: Cosine similarity threshold for relevance.
        :return: List of relevant topics with similarity scores.
        """
        if not product_topics or not relevant_topics:
            raise ValueError("Both product_topics and relevant_topics must be non-empty lists.")
        
        # Generate embeddings
        product_embeddings = self.model.encode(product_topics, convert_to_tensor=True, show_progress_bar=False)
        relevant_embeddings = self.model.encode(relevant_topics, convert_to_tensor=True, show_progress_bar=False)
        
        # Compute cosine similarities
        similarity_scores = util.cos_sim(product_embeddings, relevant_embeddings)
        similarity_scores_np = similarity_scores.cpu().numpy()  # Convert tensor to NumPy array
        
        # Extract relevant topics based on the threshold
        similar_topics = []
        for i, product_topic in enumerate(product_topics):
            indices = np.where(similarity_scores_np[i] > threshold)[0]  # Indices of relevant topics above threshold
            for j in indices:
                similar_topics.append({
                    "product_topic": product_topic,
                    "relevant_topic": relevant_topics[j],
                    "score": similarity_scores_np[i][j]
                })
        
        return sorted(similar_topics, key=lambda x: x["score"], reverse=True)

    def precompute_relevant_embeddings(self, relevant_topics):
        """
        Precompute embeddings for relevant topics to save computation time.
        
        :param relevant_topics: List of all possible relevant topics.
        :return: Precomputed embeddings for the relevant topics.
        """
        if not relevant_topics:
            raise ValueError("Relevant topics must be a non-empty list.")
        
        return self.model.encode(relevant_topics, convert_to_tensor=True, show_progress_bar=False)

    def find_similar_topics_with_precomputed(self, product_topics, relevant_embeddings, relevant_topics, threshold=0.5):
        """
        Find similar topics using precomputed embeddings for relevant topics.
        
        :param product_topics: List of topics related to the product.
        :param relevant_embeddings: Precomputed embeddings for relevant topics.
        :param relevant_topics: List of all possible relevant topics.
        :param threshold: Cosine similarity threshold for relevance.
        :return: List of relevant topics with similarity scores.
        """
        if not product_topics:
            raise ValueError("Product topics must be a non-empty list.")
        
        # Generate embeddings for product topics
        product_embeddings = self.model.encode(product_topics, convert_to_tensor=True, show_progress_bar=False)
        
        # Compute cosine similarities
        similarity_scores = util.cos_sim(product_embeddings, relevant_embeddings)
        similarity_scores_np = similarity_scores.cpu().numpy()
        
        # Extract similar topics
        similar_topics = []
        for i, product_topic in enumerate(product_topics):
            indices = np.where(similarity_scores_np[i] > threshold)[0]
            for j in indices:
                similar_topics.append({
                    "product_topic": product_topic,
                    "relevant_topic": relevant_topics[j],
                    "score": similarity_scores_np[i][j]
                })
        
        return sorted(similar_topics, key=lambda x: x["score"], reverse=True)

    def find_similar_words(self, word_list, related_words, threshold=0.5):
        """
        Detect similar relationships between words.
        
        :param word_list: List of words to compare.
        :param related_words: List of related words to match against.
        :param threshold: Cosine similarity threshold for relevance.
        :return: List of relevant word pairs with similarity scores.
        """
        if not word_list or not related_words:
            raise ValueError("Both word_list and related_words must be non-empty lists.")
        
        # Generate embeddings
        word_embeddings = self.model.encode(word_list, convert_to_tensor=True, show_progress_bar=False)
        related_embeddings = self.model.encode(related_words, convert_to_tensor=True, show_progress_bar=False)
        
        # Compute cosine similarities
        similarity_scores = util.cos_sim(word_embeddings, related_embeddings)
        similarity_scores_np = similarity_scores.cpu().numpy()
        
        # Extract similar word pairs
        similar_words = []
        for i, word in enumerate(word_list):
            indices = np.where(similarity_scores_np[i] > threshold)[0]
            for j in indices:
                similar_words.append({
                    "word": word,
                    "related_word": related_words[j],
                    "score": similarity_scores_np[i][j]
                })
        
        return sorted(similar_words, key=lambda x: x["score"], reverse=True)
