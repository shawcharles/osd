# Review: "Adaptive Superego Design: A Scalable Framework for Geographic Marketing Experiments"

In this manuscript, the author considers the problem of designing randomized experiments where units are geographical units. The author's interests are motivated by marketing research. Building upon recent unpublished work of Chen et al (2024), the author proposes a new type of experimental design referred to as the "Adaptive Superego" design. The design proceeds in two stages: a graph neural network is first employed to create an embedding of the geographical units and then a SAT solver is used to construct a partition given the embeddings. Note that the final treatment assignment is not random. According to the author, the two stage approach is taken in order to improve computational tractability over the approach of Chen et al (2024).

This paper proposes a creative experimental design which is unlike almost any approach that I am aware of. However, the idea itself suffers from several foundational problems:

## Design Motivation

In the introduction and literature review, the author emphasizes the importance of causal effect estimates which are unbiased and have small variance. What is not made explicitly clear is how the proposed experimental design will actually improve the precision of a causal effect estimate. In other words, how does this proposed method of treatment assignment (i.e. the objective functions, the optimizers, etc) ensure that the variance of some causal estimate will be small? This is the central motivation of the work, and yet it is not clearly articulated in the manuscript. In fact, the experimental design will likely suffer from a significant bias because the treatment has not been randomized.

## Incomplete Proofs

The proofs contained in the appendix are far from complete. Indeed, they are referred to as "Sketch" and "Idea" in the LaTeX rather than "Proof". Let me give a concrete example. In Proposition 1, the "GNN parameter initialization" is part of the randomness being considered, but this is actually not referenced in any of the proofs.

## Computational Complexity

One of the motivations of the design was to avoid an NP-Hard problem. However, it appears that the second stage of the design is precisely to solve an NP-Hard partitioning problem. The author deals with this by giving it to a SAT solver. While this might be practical on certain machines, it doesn't "remove" the NP-Hardness.

## Miscellaneous

- The paper discusses a hypertuning approach to selecting a regularization parameter, which is needed to assign treatment; however, this seems infeasible in an actual experiment, where data is only seen *after* the treatment has been assigned.

- The objective functions for the GNN are not explicitly given, so it is not clear what the GNN is doing.

- Assumption 5.2 begs the question of why a GNN is being used at all. Indeed, an embedding with this property is easy to construct: simply use the identity embedding.
