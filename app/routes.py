# app/routes.py
from flask import render_template, request
from app import app
from app.ontology import onto

@app.route('/')
@app.route('/index')
def index():
    # Retrieve all Procedure instances
    procedures = onto.Procedure.instances()
    return render_template('index.html', title='Homepage', procedures=procedures)

@app.route('/search_results')
def search_results():
    query = request.args.get('query', '').lower().strip()
    matching_procedures = []

    print(f"Search Query: {query}")
    
    for procedure in onto.Procedure.instances():
        procedure_title = procedure.has_title[0] if procedure.has_title and len(procedure.has_title) > 0 else '[No Title]'
        item_title = ''
        if procedure.part_of and len(procedure.part_of) > 0:
            item_title = procedure.part_of[0].has_title[0] if procedure.part_of[0].has_title else '[No Item]'
        
        print(f"Checking Procedure: '{procedure_title}', Item: '{item_title}'")

        combined_title = f"{procedure_title} {item_title}".lower()
        print(f"Combined Title: '{combined_title}'")

        if query in combined_title:
            print(f"Match Found: '{combined_title}'")
            matching_procedures.append(procedure)

    if not matching_procedures:
        print("No matching procedures found.")
    
    return render_template('searchpage.html', title='Search Results', query=query, procedures=matching_procedures)

@app.route('/procedure/<procedure_id>')
def procedure_detail(procedure_id):
    # Get the Procedure instance
    procedure = onto.search_one(iri="*" + procedure_id)
    if not procedure:
        return render_template('404.html'), 404

    # Gather data
    steps = sorted(procedure.consists_of, key=lambda s: s.has_order[0])

    # Identify tools used in steps but missing in procedure's toolbox
    tools_in_toolbox = set(procedure.uses_tool)
    tools_used_in_steps = set()
    for step in steps:
        tools_used_in_steps.update(step.uses_tool)

    missing_tools = tools_used_in_steps - tools_in_toolbox

    # Identify steps with potential hazards
    hazard_steps = []
    hazard_keywords = ['careful', 'dangerous']
    for step in steps:
        description = step.has_description[0].lower()
        if any(keyword in description for keyword in hazard_keywords):
            hazard_steps.append(step)

    return render_template('procedure_detail.html', procedure=procedure, steps=steps, missing_tools=missing_tools, hazard_steps=hazard_steps)

@app.route('/procedures_with_many_steps')
def procedures_with_many_steps():
    from rdflib import Graph, Namespace
    from rdflib.namespace import RDF

    # Export ontology to an RDFLib graph
    graph = onto.world.as_rdflib_graph()
    ifixit_ns = Namespace("http://example.org/ifixit.owl#")
    graph.bind("ifixit", ifixit_ns)

    query = """
    PREFIX ifixit: <http://example.org/ifixit.owl#>
    SELECT ?procedure ?title (COUNT(?step) AS ?num_steps)
    WHERE {
      ?procedure rdf:type ifixit:Procedure .
      ?procedure ifixit:consists_of ?step .
      ?procedure ifixit:has_title ?title .
    }
    GROUP BY ?procedure ?title
    HAVING (COUNT(?step) > 6)
    """

    results = graph.query(query)

    procedures = []
    for row in results:
        procedure_iri = str(row.procedure)
        procedure_id = procedure_iri.split('#')[-1]
        title = row.title.toPython()
        num_steps = int(row.num_steps)
        procedures.append({'id': procedure_id, 'title': title, 'num_steps': num_steps})

    return render_template('procedures_with_many_steps.html', title='Procedures with Many Steps', procedures=procedures)
