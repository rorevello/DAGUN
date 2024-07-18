import streamlit as st
from neo4j import GraphDatabase

uri = ""
username = ""
password = ""

driver = GraphDatabase.driver(uri, auth=(username, password))

def create_user(tx, name, annotation):
    tx.run("CREATE (u:User {name: $name, annotation: $annotation})", name=name, annotation=annotation)
  
def create_user_handler(name, annotation):
    with driver.session() as session:
        session.write_transaction(create_user, name, annotation)
    st.success(f"User {name} created successfully.")

def fetch_users(tx):
    result = tx.run("MATCH (u:User) RETURN u.name AS name")
    return [record["name"] for record in result]

def get_all_users():
    with driver.session() as session:
        users = session.read_transaction(fetch_users)
    return users

def create_relationship(tx, name1, name2, relationship_type):
    query = """
    MATCH (a:User {name: $name1}), (b:User {name: $name2})
    CREATE (a)-[r:%s]->(b)
    """ % relationship_type
    tx.run(query, name1=name1, name2=name2)

def create_relationship_handler(name1, name2, relationship_type):
    with driver.session() as session:
        user1_exists = session.run("MATCH (u:User {name: $name}) RETURN u", name=name1).single() is not None
        user2_exists = session.run("MATCH (u:User {name: $name}) RETURN u", name=name2).single() is not None
        
        if not user1_exists or not user2_exists:
            st.error("One or both users do not exist.")
            return
        
        session.write_transaction(create_relationship, name1, name2, relationship_type)
    st.success(f"Relationship {relationship_type} created successfully between {name1} and {name2}.")

st.title("User and Relationship Management with Neo4j")

option = st.selectbox(
    "What do you want to do?",
    ("Create User", "Create Relationship")
)


if option == "Create User":
    st.header("Create")
    name = st.text_input("User Name")
    annotation = st.text_area("Annotation")
    
    if st.button("Create User"):
        create_user_handler(name, annotation)

elif option == "Create Relationship":
    st.header("Create")
    users = get_all_users()
    
    if users:
        name1 = st.selectbox("First User Name", users)
        name2 = st.selectbox("Second User Name", users)
        relationship_type = st.text_input("Relationship Type")
        
        if st.button("Create "):
            create_relationship_handler(name1, name2, relationship_type)
    else:
        st.warning("No users available ")
