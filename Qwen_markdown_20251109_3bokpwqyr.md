# SWORMS Lite - Lightweight Multi-Agent System

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://python.org)
[![Docker](https://img.shields.io/badge/Docker-Supported-blue.svg)](https://docker.com)

## 🚀 Overview

SWORMS Lite is a lightweight implementation of the advanced SWORMS collective intelligence system. It provides a simplified multi-agent communication and coordination framework designed for rapid deployment and testing of collective intelligence concepts.

### Key Features
- **Lightweight Architecture**: Minimal resource usage with high performance
- **Multi-Agent Communication**: Advanced message passing between agents
- **Real-time Coordination**: Dynamic task assignment and load balancing
- **Modular Design**: Easy to extend and customize
- **Container Ready**: Full Docker support for easy deployment

## 🏗️ Architecture

The system consists of:
- **Communication Hub**: Central message routing and coordination
- **Agents**: Individual processing units with specific capabilities
- **Coordinator**: System-level orchestration and task management
- **Message System**: Asynchronous communication with various protocols

## 🛠️ Requirements

- Python 3.8+
- Docker (optional, for containerized deployment)
- 512MB+ RAM recommended

## 📦 Installation

### Quick Start with Docker
```bash
# Clone the repository
git clone https://github.com/yourusername/sworms-lite.git
cd sworms-lite

# Build and run with Docker
docker-compose up -d

# Access the system
docker logs sworms-lite-main