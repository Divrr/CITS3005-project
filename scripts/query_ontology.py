from owlready2 import *
from rdflib import Graph, Namespace
from rdflib.namespace import RDF, RDFS, OWL, XSD

onto = get_ontology("ifixit_ontology.owl").load()

# Export ontology to an RDFLib graph
graph = onto.world.as_rdflib_graph()

ifixit_ns = Namespace("http://example.org/ifixit.owl#")
graph.bind("ifixit", ifixit_ns)
graph.serialize(destination="ifixit_knowledge_graph.ttl", format="turtle")

# Query 1: Procedures with more than 6 steps
query1 = """
PREFIX ifixit: <http://example.org/ifixit.owl#>
SELECT ?procedure ?title (COUNT(?step) AS ?num_steps)
WHERE {
  ?procedure rdf:type ifixit:Procedure .
  ?procedure ifixit:consists_of ?step .
  ?procedure ifixit:title ?title .
}
GROUP BY ?procedure ?title
HAVING (COUNT(?step) > 6)
"""

print("Procedures with more than 6 steps:")
results1 = graph.query(query1)
for row in results1:
    procedure_iri = row.procedure
    title = row.title
    num_steps = row.num_steps
    print(f"- {title} ({procedure_iri}) has {num_steps} steps")

print("\n" + "="*50 + "\n")

# Query 2: Items with more than 10 procedures
query2 = """
PREFIX ifixit: <http://example.org/ifixit.owl#>
SELECT ?item ?title (COUNT(?procedure) AS ?num_procedures)
WHERE {
  ?procedure rdf:type ifixit:Procedure .
  ?procedure ifixit:part_of ?item .
  ?item ifixit:title ?title .
}
GROUP BY ?item ?title
HAVING (COUNT(?procedure) > 10)
"""

print("Items with more than 10 procedures:")
results2 = graph.query(query2)
for row in results2:
    item_iri = row.item
    title = row.title
    num_procedures = row.num_procedures
    print(f"- {title} ({item_iri}) has {num_procedures} procedures")

print("\n" + "="*50 + "\n")

# Query 3: Procedures with tools not used in steps
query3 = """
PREFIX ifixit: <http://example.org/ifixit.owl#>
SELECT DISTINCT ?procedure ?title ?tool_title
WHERE {
  ?procedure rdf:type ifixit:Procedure .
  ?procedure ifixit:uses_tool ?tool .
  ?procedure ifixit:title ?title .
  ?tool ifixit:title ?tool_title .
  FILTER NOT EXISTS {
    ?procedure ifixit:consists_of ?step .
    ?step ifixit:uses_tool ?tool .
  }
}
"""

print("Procedures with tools not used in steps:")
results3 = graph.query(query3)
for row in results3:
    procedure_iri = row.procedure
    procedure_title = row.title
    tool_title = row.tool_title
    print(f"- Procedure '{procedure_title}' ({procedure_iri}) includes tool '{tool_title}' not used in any step")

print("\n" + "="*50 + "\n")

# Query 4: Steps with potential hazards
query4 = """
PREFIX ifixit: <http://example.org/ifixit.owl#>
SELECT ?procedure ?proc_title ?step ?step_order ?description
WHERE {
  ?procedure rdf:type ifixit:Procedure .
  ?procedure ifixit:consists_of ?step .
  ?procedure ifixit:title ?proc_title .
  ?step ifixit:order ?step_order .
  ?step ifixit:description ?description .
  FILTER (regex(?description, "careful|dangerous", "i"))
}
ORDER BY ?procedure ?step_order
"""

print("Steps with potential hazards (containing 'careful' or 'dangerous'):")
results4 = graph.query(query4)
for row in results4:
    procedure_title = row.proc_title
    step_order = row.step_order
    description = row.description
    print(f"- Procedure '{procedure_title}', Step {step_order}: {description}")

