import numpy as np
import torch
import torch.optim as optim
from sklearn.neighbors import kneighbors_graph
from sklearn.cluster import AgglomerativeClustering
from sklearn.decomposition import PCA
from sklearn.manifold import SpectralEmbedding
from typing import List, Dict, Tuple

from osd.utils.data_structures import GeoUnit
from osd.models.gnn import GraphSAGE, ContrastiveLoss
from osd.design.solver import Supergeo

class CandidateGenerator:
    def __init__(self, geo_units: List[GeoUnit], embedding_dim=32, method="pca"):
        """
        Args:
            geo_units: List of GeoUnit objects
            embedding_dim: Dimension of embeddings (for GNN/PCA)
            method: 'pca', 'gnn', 'spectral', 'random' (Default: pca)
        """
        self.geo_units = geo_units
        self.embedding_dim = embedding_dim
        self.method = method
        
        # Extract features
        self.feature_names = sorted(list(geo_units[0].covariates.keys()))
        self.X_raw = np.stack([g.to_feature_vector(self.feature_names) for g in geo_units])
        
        # Normalize
        self.X_norm = (self.X_raw - self.X_raw.mean(0)) / (self.X_raw.std(0) + 1e-6)
        
    def train_embeddings(self, epochs=100, lr=0.01):
        if self.method == "gnn":
            return self._train_gnn(epochs, lr)
        elif self.method == "pca":
            return self._train_pca()
        elif self.method == "spectral":
            return self._train_spectral()
        elif self.method == "random":
            self.embeddings = np.random.randn(len(self.geo_units), self.embedding_dim)
            return self.embeddings
        else:
            raise ValueError(f"Unknown method: {self.method}")

    def _train_gnn(self, epochs, lr):
        # Build Graph (k-NN)
        k = min(10, len(self.geo_units) - 1)
        adj_sparse = kneighbors_graph(self.X_norm, k, mode='connectivity', include_self=True)
        adj_dense = torch.tensor(adj_sparse.toarray(), dtype=torch.float32)
        
        features = torch.tensor(self.X_norm, dtype=torch.float32)
        
        # Model
        model = GraphSAGE(features.shape[1], 64, self.embedding_dim)
        optimizer = optim.Adam(model.parameters(), lr=lr)
        criterion = ContrastiveLoss()
        
        model.train()
        for epoch in range(epochs):
            optimizer.zero_grad()
            emb = model(features, adj_dense)
            loss = criterion(emb, adj_dense)
            loss.backward()
            optimizer.step()
            
        model.eval()
        with torch.no_grad():
            self.embeddings = model(features, adj_dense).numpy()
            
        return self.embeddings

    def _train_pca(self):
        n_components = min(self.embedding_dim, self.X_norm.shape[1])
        pca = PCA(n_components=n_components)
        self.embeddings = pca.fit_transform(self.X_norm)
        return self.embeddings

    def _train_spectral(self):
        k = min(10, len(self.geo_units) - 1)
        adj = kneighbors_graph(self.X_norm, k, mode='connectivity', include_self=True)
        embedding = SpectralEmbedding(n_components=self.embedding_dim, affinity='precomputed')
        # Note: SpectralEmbedding expects affinity matrix. kneighbors_graph returns adjacency (0/1).
        # We treat adjacency as affinity.
        self.embeddings = embedding.fit_transform(adj)
        return self.embeddings

    def generate_supergeos(self, n_supergeos: int) -> List[Supergeo]:
        """
        Cluster embeddings to form supergeos.
        """
        if not hasattr(self, 'embeddings'):
            self.train_embeddings()
            
        # Hierarchical Clustering
        clustering = AgglomerativeClustering(
            n_clusters=n_supergeos,
            metric='euclidean',
            linkage='ward'
        )
        labels = clustering.fit_predict(self.embeddings)
        
        # Group units
        groups = {}
        for i, label in enumerate(labels):
            if label not in groups:
                groups[label] = []
            groups[label].append(self.geo_units[i])
            
        # Create Supergeo objects
        supergeos = []
        for label, units in groups.items():
            # Aggregate
            resp = sum(u.response for u in units)
            spend = sum(u.spend for u in units)
            covs = {f: 0.0 for f in self.feature_names}
            
            # Distinguish between extensive (sum) and intensive (weighted average) variables
            # We use a simple heuristic: "population", "spend", "response" are extensive.
            # All others (like "income") are treated as intensive.
            extensive_keywords = ["population", "spend", "response", "users", "count"]
            
            for f in self.feature_names:
                is_extensive = any(k in f.lower() for k in extensive_keywords)
                
                if is_extensive:
                    # Sum
                    covs[f] = sum(u.covariates.get(f, 0.0) for u in units)
                else:
                    # Weighted Average (weighted by population if available, else simple average)
                    values = [u.covariates.get(f, 0.0) for u in units]
                    weights = [u.covariates.get("population", 1.0) for u in units]
                    if sum(weights) > 0:
                        covs[f] = np.average(values, weights=weights)
                    else:
                        covs[f] = np.mean(values)
                
            supergeos.append(Supergeo(
                id=f"sg_{label}",
                units=[u.id for u in units],
                response=resp,
                spend=spend,
                covariates=covs
            ))
            
        return supergeos
