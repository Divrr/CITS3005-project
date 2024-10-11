# app/routes.py
from flask import render_template, request
from app import app
from app.forms import SearchForm
from app.ontology import onto

def populate_facet_choices(form, selected_categories=None, selected_tools=None, selected_parts=None):
    # Initialize counts
    category_counts = {}
    tool_counts = {}
    part_counts = {}

    # Build a mapping of category titles to category instances
    categories_by_title = {cat.title: cat for cat in onto.DeviceCategory.instances() if cat.title}

    # Build category hierarchy and initialize counts
    category_hierarchy = build_category_hierarchy(categories_by_title)

    # Calculate counts
    for procedure in onto.Procedure.instances():
        # Categories
        item = procedure.part_of[0] if procedure.part_of else None
        if item and item.belongs_to_category:
            for category in item.belongs_to_category:
                # Increment counts for the category and all its ancestors
                propagate_category_count(category, category_counts)
        # Tools
        for tool in procedure.uses_tool:
            tool_title = tool.title
            tool_counts[tool_title] = tool_counts.get(tool_title, 0) + 1
        # Parts
        parts_in_procedure = set(part for step in procedure.consists_of for part in step.involves_part)
        for part in parts_in_procedure:
            part_title = part.title
            part_counts[part_title] = part_counts.get(part_title, 0) + 1

    # Populate categories with counts
    form.categories.choices = [
        (cat.title, f"{cat.title} ({category_counts.get(cat.title, 0)})")
        for cat in onto.DeviceCategory.instances() if cat.title
    ]

    # Populate tools with counts
    form.tools.choices = [
        (tool.title, f"{tool.title} ({tool_counts.get(tool.title, 0)})")
        for tool in onto.Tool.instances() if tool.title
    ]

    # Populate parts with counts
    form.parts.choices = [
        (part.title, f"{part.title} ({part_counts.get(part.title, 0)})")
        for part in onto.Part.instances() if part.title
    ]

    return category_hierarchy, category_counts

def propagate_category_count(category, category_counts):
    # Increment count for the category
    category_counts[category.title] = category_counts.get(category.title, 0) + 1
    # Recursively increment counts for parent categories
    for parent in category.subcategory_of:
        propagate_category_count(parent, category_counts)

def build_category_hierarchy(categories_by_title):
    # Initialize hierarchy
    hierarchy = {}

    # Build parent-child relationships
    for category in categories_by_title.values():
        category_title = category.title
        parent_titles = [parent.title for parent in category.subcategory_of]
        if not parent_titles:
            # Top-level category
            if category_title not in hierarchy:
                hierarchy[category_title] = {'category': category, 'subcategories': {}}
        else:
            for parent_title in parent_titles:
                parent = categories_by_title.get(parent_title)
                if parent:
                    if parent_title not in hierarchy:
                        hierarchy[parent_title] = {'category': parent, 'subcategories': {}}
                    if 'subcategories' not in hierarchy[parent_title]:
                        hierarchy[parent_title]['subcategories'] = {}
                    hierarchy[parent_title]['subcategories'][category_title] = {'category': category, 'subcategories': {}}

    return hierarchy

@app.route('/', methods=['GET', 'POST'])
def index():
    form = SearchForm()
    category_hierarchy, category_counts = populate_facet_choices(form)
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
    form = SearchForm(request.form)

    # Update form choices with counts and get category hierarchy
    category_hierarchy, category_counts = populate_facet_choices(form)

    if form.validate_on_submit():
        # Form was submitted via POST and is valid
        query = form.query.data.lower().strip() if form.query.data else ''
        selected_categories = form.categories.data if form.categories.data else []
        selected_tools = form.tools.data if form.tools.data else []
        selected_parts = form.parts.data if form.parts.data else []
    else:
        # Handle GET request or form validation failed
        query = request.args.get('query', '').lower().strip()
        selected_categories = request.args.getlist('categories')
        selected_tools = request.args.getlist('tools')
        selected_parts = request.args.getlist('parts')

    # Build a set of all selected category titles and their subcategories
    all_selected_category_titles = set()

    if selected_categories:
        for cat_title in selected_categories:
            category = onto.search_one(title=cat_title)
            if category:
                subcategories = get_all_subcategories(category)
                # Collect titles of all subcategories
                for subcat in subcategories:
                    all_selected_category_titles.add(subcat.title.lower())
            else:
                print(f"Category with title '{cat_title}' not found.")

    matching_procedures = []

    for procedure in onto.Procedure.instances():
        # Filter by query
        if query and (not procedure.title or query not in procedure.title.lower()):
            continue

        # Filter by categories
        if selected_categories:
            item = procedure.part_of[0] if procedure.part_of else None
            if not item or not item.belongs_to_category:
                continue

            item_category_titles = {category.title.lower() for category in item.belongs_to_category}
            if not item_category_titles.intersection(all_selected_category_titles):
                continue

        # Filter by tools
        if selected_tools:
            procedure_tool_titles = set(tool.title for tool in procedure.uses_tool)
            if not set(selected_tools).issubset(procedure_tool_titles):
                continue

        # Filter by parts
        if selected_parts:
            # Extract parts involved in each step of the procedure
            parts_in_procedure = set(part.title for step in procedure.consists_of for part in step.involves_part)
            if not set(selected_parts).issubset(parts_in_procedure):
                continue

        matching_procedures.append(procedure)

    return render_template(
        'searchpage.html',
        title='Search',
        form=form,
        procedures=matching_procedures,
        query=query,
        category_hierarchy=category_hierarchy,
        category_counts=category_counts
    )

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
