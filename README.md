
# DAGUN: Directed Acyclic Graph between Users in Neo4j

## Description

DAGUN is a web application built using Streamlit and Neo4j, designed to manage and visualize relationships between users. This application allows you to create users with various properties, establish relationships between them, and visualize these relationships through an interactive graph.

## Features

- **User Management**: Create users with custom properties.
- **Relationship Management**: Establish relationships between users.
- **Graph Visualization**: Visualize user relationships in an interactive graph.
- **Network Statistics**: Display statistics about the user network, including the most connected user.

## Prerequisites

- **Neo4j Database**: Ensure you have access to a Neo4j database. If you don't have one, you can set it up using the official Neo4j Docker image.
- **Streamlit**: Install Streamlit for running the web application.

## Getting Started

### Neo4j Setup

1. **Pull the Neo4j Docker Image**:
    ```bash
    docker pull neo4j:latest
    ```

2. **Run the Neo4j Docker Container**:
    ```bash
    docker run -d --name neo4j -p7474:7474 -p7687:7687 -d neo4j:latest
    ```

3. **Access Neo4j**:
    - Open your web browser and navigate to `http://localhost:7474`.
    - Set your username and password for the database.

### Configuration

1. **Update Connection Parameters**:
    - Open the script and set the `uri`, `username`, and `password` variables with your Neo4j connection details:
    ```python
    uri = "bolt://localhost:7687"
    username = "your-username"
    password = "your-password"
    ```

### Install Dependencies

```bash
pip install streamlit neo4j pyvis
```

### Run the Application

```bash
streamlit run main.py
```

## Application Structure

### Main Sections

1. **User Management**:
    - **Create User**: Allows you to create a new user with a name, annotation, and custom properties.
    - **Create Relationship**: Establishes a relationship between two existing users.

2. **Graph Statistics**:
    - **User Details and Graph**: Displays detailed information about a selected user and visualizes their relationships.
    - **Network Statistics**: Shows overall network statistics, including the total number of users and the most connected user.

## License

This project is licensed under the MIT License.
