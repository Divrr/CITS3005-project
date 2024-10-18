# app/ontology.py
from owlready2 import get_ontology, sync_reasoner

ontology_path = "ifixit_ontology.owl"
onto = get_ontology(ontology_path).load()

with onto:
    sync_reasoner()

print(f"Ontology loaded with {len(list(onto.Procedure.instances()))} procedures.")