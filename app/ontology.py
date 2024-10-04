# app/ontology.py
from owlready2 import get_ontology, sync_reasoner

# Load your ontology
ontology_path = "ifixit_ontology.owl"
onto = get_ontology(ontology_path).load()

# Run the reasoner
with onto:
    sync_reasoner()

print(f"Ontology loaded with {len(list(onto.Procedure.instances()))} procedures.")

for procedure in onto.Procedure.instances():
    if procedure.has_title and "macbook" in procedure.has_title[0].lower():
        print(f"Procedure found: {procedure.has_title[0]}")
