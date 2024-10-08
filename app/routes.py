# app/routes.py
from flask import render_template, request
from app import app
from app.forms import SearchForm
from app.ontology import onto

def populate_facet_choices(form):
    # Populate categories
    form.categories.choices = [
        (cat.title, cat.title) for cat in onto.DeviceCategory.instances() if cat.title
    ]
    # Populate tools
    form.tools.choices = [
        (tool.name, tool.title) for tool in onto.Tool.instances() if tool.title
    ]
    # Populate parts
    form.parts.choices = [
        (part.name, part.title) for part in onto.Part.instances() if part.title
    ]

@app.route('/', methods=['GET', 'POST'])
def index():
    form = SearchForm()
    populate_facet_choices(form)
    if form.validate_on_submit():
        # Pass form data to the search_results route
        return search_results()
    return render_template('index.html', title='Homepage', form=form)

def get_all_subcategories(category):
    subcategories = set()
    to_visit = [category]
    
    while to_visit:
        current = to_visit.pop()
        subcategories.add(current)
        # Find categories where 'subcategory_of' is current
        for cat in onto.DeviceCategory.instances():
            if current in cat.subcategory_of:
                if cat not in subcategories:
                    to_visit.append(cat)
    return subcategories


@app.route('/search_results', methods=['GET', 'POST'])
def search_results():
    form = SearchForm()
    populate_facet_choices(form)

    if form.validate_on_submit():
        # Form was submitted via POST
        query = form.query.data.lower().strip() if form.query.data else ''
        selected_categories = form.categories.data if form.categories.data else []
        selected_tools = form.tools.data if form.tools.data else []
        selected_parts = form.parts.data if form.parts.data else []
    else:
        # Form was not submitted or is invalid, handle GET request
        query = request.args.get('query', '').lower().strip()
        selected_categories = request.args.getlist('categories')
        selected_tools = request.args.getlist('tools')
        selected_parts = request.args.getlist('parts')

    # Initialize all_selected_category_names
    all_selected_category_titles = set()

    # Build a set of all selected category names
    if selected_categories:
        for cat_title in selected_categories:
            category = onto.search_one(title=cat_title)
            if category:
                subcategories = get_all_subcategories(category)
                # Collect names of all subcategories
                for subcat in subcategories:
                    all_selected_category_titles.add(subcat.title.lower())
            else:
                print(f"Category with name '{cat_title}' not found.")
    else:
        # If no categories are selected, we can include all categories or leave it empty
        pass  # We'll leave it empty here

    matching_procedures = []

    for procedure in onto.Procedure.instances():
        is_match = True

        # Filter by query
        if query:
            procedure_title = procedure.title.lower() if procedure.title else ''
            if query not in procedure_title:
                is_match = False

        # Filter by categories
        if is_match and selected_categories:
            item = procedure.part_of[0] if procedure.part_of else None
            if item and item.belongs_to_category:
                item_category_names = [cat.title.lower() for cat in item.belongs_to_category]
                if not any(name in all_selected_category_titles for name in item_category_names):
                    is_match = False
            else:
                is_match = False
        # If no categories are selected, skip category filtering

        # Filter by tools
        if is_match and selected_tools:
            procedure_tool_names = [tool.name for tool in procedure.uses_tool]
            if not set(selected_tools).issubset(set(procedure_tool_names)):
                is_match = False

        # Filter by parts
        if is_match and selected_parts:
            parts_in_procedure = []
            for step in procedure.consists_of:
                parts_in_procedure.extend([part.name for part in step.involves_part])
            if not set(selected_parts).issubset(set(parts_in_procedure)):
                is_match = False

        if is_match:
            matching_procedures.append(procedure)

    return render_template('searchpage.html', title='Search', form=form, procedures=matching_procedures, query=query)

@app.route('/procedure/<procedure_id>')
def procedure_detail(procedure_id):
    # Get the Procedure instance
    procedure = onto.search_one(iri="*" + procedure_id)
    if not procedure:
        return render_template('404.html'), 404

    # Gather data
    steps = sorted(procedure.consists_of, key=lambda s: s.order)

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
        description = step.description.lower()
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
      ?procedure ifixit:title ?title .
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
