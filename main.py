import streamlit as st
from neo4j import GraphDatabase
from pyvis.network import Network
import streamlit.components.v1 as components

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
    try:
        with driver.session() as session:
            session.write_transaction(create_user, name, annotation, properties)
        st.success(f"User {name} created successfully.")
    except Exception as e:
        st.exception(f"Failed to create user {name}: {e}")

def fetch_users(tx):
    result = tx.run("MATCH (u:User) RETURN u.name AS name")
    return [record["name"] for record in result]

def get_all_users():
    try:
        with driver.session() as session:
            users = session.read_transaction(fetch_users)
        return users
    except Exception as e:
        st.exception(f"Failed to fetch users: {e}")
        return []

def fetch_property_names(tx):
    result = tx.run("MATCH (u:User) UNWIND keys(u) AS property RETURN DISTINCT property")
    return [record["property"] for record in result]

def get_all_property_names():
    try:
        with driver.session() as session:
            property_names = session.read_transaction(fetch_property_names)
        return property_names
    except Exception as e:
        st.exception(f"Failed to fetch property names: {e}")
        return []

def create_relationship(tx, name1, name2, relationship_type):
    query = """
    MATCH (a:User {name: $name1}), (b:User {name: $name2})
    CREATE (a)-[r:%s {type: $type}]->(b)
    """ % relationship_type
    tx.run(query, name1=name1, name2=name2, type=relationship_type)

def create_relationship_handler(name1, name2, relationship_type):
    try:
        with driver.session() as session:
            user1_exists = session.run("MATCH (u:User {name: $name}) RETURN u", name=name1).single() is not None
            user2_exists = session.run("MATCH (u:User {name: $name}) RETURN u", name=name2).single() is not None
            
            if not user1_exists or not user2_exists:
                st.error("One or both users do not exist.")
                return
            
            session.write_transaction(create_relationship, name1, name2, relationship_type)
        st.success(f"Relationship {relationship_type} created successfully between {name1} and {name2}.")
    except Exception as e:
        st.exception(f"Failed to create relationship {relationship_type} between {name1} and {name2}: {e}")

def fetch_user_details(tx, name):
    query = "MATCH (u:User {name: $name}) RETURN u"
    result = tx.run(query, name=name)
    return result.single()["u"]

def get_user_details(name):
    try:
        with driver.session() as session:
            user_details = session.read_transaction(fetch_user_details, name)
        return user_details
    except Exception as e:
        st.exception(f"Failed to fetch details for user {name}: {e}")
        return None

def fetch_user_graph(tx, name):
    query = """
    MATCH (u:User {name: $name})-[r*1..3]-(connected)
    RETURN u, connected, r
    """
    result = tx.run(query, name=name)
    nodes = set()
    edges = set()
    for record in result:
        u = record["u"]
        connected = record["connected"]
        rels = record["r"]
        nodes.add((u.id, u["name"]))
        nodes.add((connected.id, connected["name"]))
        for rel in rels:
            edges.add((u.id, connected.id, type(rel).__name__))
    return nodes, edges

def get_user_graph(name):
    try:
        with driver.session() as session:
            nodes, edges = session.read_transaction(fetch_user_graph, name)
        return nodes, edges
    except Exception as e:
        st.exception(f"Failed to fetch graph for user {name}: {e}")
        return set(), set()

def plot_user_graph(nodes, edges):
    if not nodes or not edges:
        st.warning("No connections found for this user.")
        return
    
    net = Network(height='750px', width='100%')

    for node_id, node_name in nodes:
        net.add_node(node_id, label=node_name)

    for edge in edges:
        src, dst, relationship_type = edge
        net.add_edge(src, dst, title=relationship_type, label=relationship_type)

    net.set_options(
        """
            "var options ="{
                "nodes": { 
                    "color": {
                        "hover": {
                            "border": "rgba(231,44,233,1)"
                        }
                    },
                    "shape": "dot"
                },
                "edges": {
                    "arrowStrikethrough": false,
                    "color": {
                        "highlight": "rgb(255, 0, 0)",
                        "hover": "rgba(128,25,132,1)",
                        "inherit": false
                    },
                    "smooth": {
                        "type": "vertical",
                        "forceDirection": "none"
                    }
                },
                "physics": {
                    "barnesHut": {
                        "gravitationalConstant": -80000,
                        "springLength": 250,
                        "springConstant": 0.001
                    },
                    "minVelocity": 0.75
                }
            }"""
    )

    net_html = net.generate_html()

    components.html(net_html, height=750, width=750)

def fetch_network_stats(tx):
    num_properties_query = "MATCH (p:Property) RETURN count(p) AS num_properties"
    num_users_query = "MATCH (u:User) RETURN count(u) AS num_users"
    most_connected_user_query = """
    MATCH (u:User)-[r]->()
    RETURN u.name AS name, count(r) AS num_rels
    ORDER BY num_rels DESC
    LIMIT 1
    """
    
    num_properties = tx.run(num_properties_query).single()["num_properties"]
    num_users = tx.run(num_users_query).single()["num_users"]
    most_connected_user = tx.run(most_connected_user_query).single()
    
    return num_properties, num_users, most_connected_user["name"], most_connected_user["num_rels"]

def get_network_stats():
    try:
        with driver.session() as session:
            num_properties, num_users, most_connected_user, num_rels = session.read_transaction(fetch_network_stats)
        return num_properties, num_users, most_connected_user, num_rels
    except Exception as e:
        st.exception(f"Failed to fetch network statistics: {e}")
        return 0, 0, None, 0

st.title("DAGUN: Directed Acyclic Graph between Users in Neo4j")

page = st.sidebar.selectbox(
    "Choose a page",
    ("User Management", "Graph Statistics")
)

if page == "User Management":
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
            if property_name == "Enter new property...":
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
            if st.button("Create Relationship") and len(relationship_type) != 0:
                    create_relationship_handler(name1, name2, relationship_type)
            
        else:
            st.warning("No users available to create a relationship.")

elif page == "Graph Statistics":
    st.header("Graph Statistics")
    users = get_all_users()
    
    if users:
        selected_user = st.selectbox("Select a User", users)
        
        if st.button("Show Details"):
            user_details = get_user_details(selected_user)
            if user_details:
                with st.container():
                    st.subheader(f"Details for {selected_user}")
                    st.markdown(f"**Name:** {user_details['name']}")
                    st.markdown(f"**Annotation:** {user_details['annotation']}")
                    
                    st.markdown("**Properties:**")
                    for key, value in user_details.items():
                        if key not in ['name', 'annotation']:
                            st.markdown(f"- **{key}:** {value}")

                nodes, edges = get_user_graph(selected_user)
                plot_user_graph(nodes, edges)
            else:
                st.warning(f"No details found for user {selected_user}.")
    else:
        st.warning("No users available.")
    
    st.subheader("Network Statistics")
    num_properties, num_users, most_connected_user, num_rels = get_network_stats()
    st.write(f"Total number of users: {num_users}")
    if most_connected_user:
        st.write(f"Most connected user: {most_connected_user} with {num_rels} relationships")
    else:
        st.write("No relationships found in the network.")
