# Decentralized Swarm Intelligence via Graph Neural Networks (`swarm-gnn`)

This branch contains the experimental codebase, simulation scripts, and architectural models for **Graph Neural Network (GNN)-guided decentralized multi-agent swarm control**. 

---

## Overview
Traditional centralized swarm controllers scale poorly with the number of agents and lack resilience against node dropouts. This project implements a **message-passing GNN framework** where individual agents operate on localized topological graphs—making navigation, formation control, and obstacle avoidance fully decentralized, scalable, and robust to dynamic environments.

---

## Repository Structure

```text
├── models/             # GNN architecture definitions (PyTorch Geometric / PyTorch)
├── policies/           # Decentralized control policies & decentralized inference loops
├── environments/       # Simulation and training environments (Gymnasium / custom physics)
├── scripts/            # Training, evaluation, and visualization scripts
└── checkpoints/        # Pre-trained model weights
