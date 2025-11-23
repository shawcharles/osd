import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import silhouette_score
from sklearn.manifold import TSNE

from osd.utils.synthetic_data import generate_synthetic_data
from osd.design.candidate_generation import CandidateGenerator

def diagnose_embeddings():
    print("Running GNN Diagnostic...")
    
    # Generate data with structure (spatial confounding = 0.5)
    units = generate_synthetic_data(n_units=200, spatial_confounding=0.5, non_linear_effect=True)
    
    methods = ['gnn', 'pca', 'random']
    
    for method in methods:
        print(f"\nTesting Method: {method}")
        gen = CandidateGenerator(units, method=method)
        
        # Train
        embeddings = gen.train_embeddings()
        
        # Check variance (collapse check)
        var = np.var(embeddings, axis=0).mean()
        print(f"  Average Embedding Variance: {var:.6f} (Should be > 0)")
        
        # Check clustering
        # We use HAC as in the pipeline
        from sklearn.cluster import AgglomerativeClustering
        clustering = AgglomerativeClustering(n_clusters=20)
        labels = clustering.fit_predict(embeddings)
        
        try:
            sil = silhouette_score(embeddings, labels)
            print(f"  Silhouette Score (k=20): {sil:.4f}")
        except:
            print("  Silhouette Score: Failed")
            
        # Check correlation with Ground Truth Latent U
        # If GNN works, embeddings should correlate with the hidden spatial U
        # because U drives Income, and Income is a feature.
        
        # We project embeddings to 1D via PCA to check corr
        from sklearn.decomposition import PCA
        pca1 = PCA(n_components=1)
        emb_1d = pca1.fit_transform(embeddings).flatten()
        
        true_u = np.array([u.latent_u for u in units])
        corr = np.corrcoef(emb_1d, true_u)[0,1]
        print(f"  Correlation with Latent Spatial U: {corr:.4f}")

if __name__ == "__main__":
    diagnose_embeddings()
