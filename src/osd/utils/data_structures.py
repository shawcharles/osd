from dataclasses import dataclass
from typing import Dict, List, Optional
import numpy as np

@dataclass
class GeoUnit:
    id: str
    response: float
    spend: float
    covariates: Dict[str, float]
    
    def to_feature_vector(self, feature_names: List[str]) -> np.ndarray:
        vec = [self.response, self.spend]
        for f in feature_names:
            vec.append(self.covariates.get(f, 0.0))
        return np.array(vec, dtype=np.float32)
