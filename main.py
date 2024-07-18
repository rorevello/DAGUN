import streamlit as st
from neo4j import GraphDatabase

uri = ""
username = ""
password = ""

driver = GraphDatabase.driver(uri, auth=(username, password))
def create_user(tx, name, annotation, properties):
    tx.run("CREATE (u:User {name: $name, annotation: $annotation})", name=name, annotation=annotation)
    for prop_name, prop_value in properties.items():
        query = f"""
        MATCH (u:User {{name: $name}})
        MERGE (p:Property {{name: $prop_value}})
        CREATE (u)-[:{prop_name}]->(p)
        """
        tx.run(query, name=name, prop_name=prop_name, prop_value=prop_value)

def create_user_handler(name, annotation, properties):
    with driver.session() as session:
        session.write_transaction(create_user, name, annotation, properties)
    st.success(f"User {name} created successfully.")

def fetch_users(tx):
    result = tx.run("MATCH (u:User) RETURN u.name AS name")
    return [record["name"] for record in result]

def get_all_users():
    with driver.session() as session:
        users = session.read_transaction(fetch_users)
    return users

def fetch_property_names(tx):
    result = tx.run("MATCH (u:User) UNWIND keys(u) AS property RETURN DISTINCT property")
    return [record["property"] for record in result]

def get_all_property_names():
    with driver.session() as session:
        property_names = session.read_transaction(fetch_property_names)
    return property_names
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

st.title("DAGUN: Directed Acyclic Graph between Users in Neo4j")

option = st.selectbox(
    "What do you want to do?",
    ("Create User", "Create Relationship")
)

if option == "Create User":
    st.header("Create User")
    name = st.text_input("User Name")
    annotation = st.text_area("Annotation")
    
    properties = {}
    all_property_names = get_all_property_names()
    
    st.subheader("Add Properties")
    property_counter = 0  
    if 'property_list' not in st.session_state:
        st.session_state.property_list = []

    add_property = st.button("Add a Property")
    
    if add_property:
        st.session_state.property_list.append({"name": "", "value": ""})

    for i, prop in enumerate(st.session_state.property_list):
        property_name = st.selectbox("Property Name", all_property_names + ["Enter new property..."], key=f"property_name_{i}")
        if property_name == "New":
            property_name = st.text_input("Enter new property name", key=f"new_property_name_{i}")
        
        property_value = st.text_input(f"Value for {property_name}", key=f"property_value_{i}")
        
        st.session_state.property_list[i] = {"name": property_name, "value": property_value}
    
    if st.button("Create User"):
        for prop in st.session_state.property_list:
            if prop["name"] and prop["value"]:
                properties[prop["name"]] = prop["value"]
        create_user_handler(name, annotation, properties)
        st.session_state.property_list = []  
elif option == "Create Relationship":
    st.header("Create Relationship")
    users = get_all_users()
    
    if users:
        name1 = st.selectbox("First User Name", users)
        name2 = st.selectbox("Second User Name", users)
        relationship_type = st.text_input("Relationship Type")
        
        if st.button("Create Relationship"):
            create_relationship_handler(name1, name2, relationship_type)
    else:
        st.warning("No users ")
