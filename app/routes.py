# app/routes.py
from flask import render_template, request, redirect, url_for
from app import app
from app.forms import SearchForm
from app.ontology import onto
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

def populate_facet_choices(form=None):
    # Initialize counts
    category_counts = {}
    tool_counts = {}
    part_counts = {}

    # Build category hierarchy and initialize counts
    category_hierarchy = build_category_hierarchy(onto.DeviceCategory.instances())

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

    if form:
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
    category_counts[category] = category_counts.get(category, 0) + 1
    # Recursively increment counts for parent categories
    for parent in category.subcategory_of:
        propagate_category_count(parent, category_counts)

def build_category_hierarchy(categories):
    # This is so we get a hierarchical (instead of flat) representation of categories
    child_bank = {
        parent: [category for category in categories if parent in category.subcategory_of]
        for parent in categories
    }

    def build_category_hierarchy_recursive(children, parent):
        if not children:
            return []
        ans = []
        for child in children:
            ans.append([child, build_category_hierarchy_recursive(child_bank[child], child)])
        return ans
    
    root = [category for category in categories if not category.subcategory_of][0]
    ans = build_category_hierarchy_recursive(child_bank[root], root)
    return ans

@app.route('/', methods=['GET', 'POST'])
def index():
    form = SearchForm()
    category_hierarchy, category_counts = populate_facet_choices(form)
    if form.validate_on_submit():
        # Handle form submission from sidebar if needed
        return redirect(url_for('search_results'))
    print(category_counts, category_hierarchy)
    return render_template(
        'index.html',
        title='Homepage',
        form=form,
        category_hierarchy=category_hierarchy,
        category_counts=category_counts
    )

def get_all_subcategories(category):
    """Recursively get all subcategories of a given category."""
    subcategories = set()
    to_visit = [category]

    while to_visit:
        current = to_visit.pop()
        for subcat in onto.DeviceCategory.instances():
            if current in subcat.subcategory_of and subcat not in subcategories:
                subcategories.add(subcat)
                to_visit.append(subcat)
    return subcategories

@app.route('/search_results', methods=['GET', 'POST'])
def search_results():
    form = SearchForm(request.form)

    # Populate form choices before validation
    category_hierarchy, category_counts = populate_facet_choices(form)

    if form.validate_on_submit():
        # Handle POST request with form data
        query = form.query.data.lower().strip() if form.query.data else ''
        selected_categories = form.categories.data if form.categories.data else []
        selected_tools = form.tools.data if form.tools.data else []
        selected_parts = form.parts.data if form.parts.data else []
        logging.info(f"POST Request - Query: '{query}', Categories: {selected_categories}, Tools: {selected_tools}, Parts: {selected_parts}")
    else:
        # Handle GET request or form validation failure
        query = request.args.get('query', '').lower().strip()
        selected_categories = request.args.getlist('categories')
        selected_tools = request.args.getlist('tools')
        selected_parts = request.args.getlist('parts')
        logging.info(f"GET Request - Query: '{query}', Categories: {selected_categories}, Tools: {selected_tools}, Parts: {selected_parts}")

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
                app.logger.warning(f"Category with title '{cat_title}' not found.")

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

@app.route('/categories', methods=['GET', 'POST'])
def categories_home():
    form = SearchForm()
    category_hierarchy, category_counts = populate_facet_choices(form)
    if form.validate_on_submit():
        # Handle form submission from sidebar if needed
        return redirect(url_for('search_results'))
    
    # Find top-level categories (categories without any parent)
    top_categories = [cat for cat in onto.DeviceCategory.instances() if not cat.subcategory_of]
    return render_template(
        'categories.html',
        form=form,
        categories=top_categories,
        parent=None,
        category_hierarchy=category_hierarchy,
        category_counts=category_counts
    )


@app.route('/categories/<category_title>', methods=['GET', 'POST'])
def category_detail(category_title):
    # Normalize the category title for case-insensitive matching
    decoded_title = category_title.lower()
    
    # Perform a case-insensitive search for the category
    category = next(
        (cat for cat in onto.DeviceCategory.instances() if cat.title and cat.title.lower() == decoded_title),
        None
    )
    
    if not category:
        app.logger.error(f"Category with title '{category_title}' not found.")
        return render_template('404.html'), 404

    # **Identify the Parent Category**
    parent_categories = list(category.subcategory_of)
    if parent_categories:
        parent_category = parent_categories[0]  # Assuming single parent for simplicity
        app.logger.info(f"Parent category for '{category.title}' is '{parent_category.title}'")
    else:
        parent_category = None
        app.logger.info(f"Category '{category.title}' has no parent (it's a top-level category).")

    # Initialize the search form and populate facet choices
    form = SearchForm()
    category_hierarchy, category_counts = populate_facet_choices(form)
    
    if form.validate_on_submit():
        # Handle form submission from sidebar if needed
        return redirect(url_for('search_results'))
    
    # **Retrieve Subcategories**
    subcategories = [sub for sub in onto.DeviceCategory.instances() if category in sub.subcategory_of]
    
    if subcategories:
        # **Render Subcategories Page**
        return render_template(
            'categories.html',
            form=form,
            categories=subcategories,
            parent=parent_category,  # Pass the actual parent category
            category_hierarchy=category_hierarchy,
            category_counts=category_counts
        )
    else:
        # **Render Guides Page if No Subcategories Exist**
        all_subcategories = get_all_subcategories(category)
        all_categories = all_subcategories.union({category})
        
        # Find all Items that belong to these categories
        items = [item for item in onto.Item.instances() if any(cat in item.belongs_to_category for cat in all_categories)]
        
        # Find all Procedures linked to these Items via 'part_of'
        procedures = [proc for proc in onto.Procedure.instances() if proc.part_of and proc.part_of[0] in items]
        
        # Debugging Statements
        app.logger.info(f"Found {len(procedures)} procedures for category '{category.title}' and its subcategories.")
        for proc in procedures:
            app.logger.info(f"Procedure: {proc.title}")
        
        return render_template(
            'guides.html',
            form=form,
            procedures=procedures,
            category=category,
            category_hierarchy=category_hierarchy,
            category_counts=category_counts
        )
@app.route('/procedure/<int:guidid>', methods=['GET', 'POST'])
def procedure_detail(guidid):
    # Search for procedure by guidid
    procedure = onto.search_one(guidid=guidid)
    
    if not procedure:
        app.logger.error(f"Procedure with guidid '{guidid}' not found.")
        return render_template('404.html'), 404

    form = SearchForm()
    category_hierarchy, category_counts = populate_facet_choices(form)
    if form.validate_on_submit():
        # Handle form submission from sidebar if needed
        return redirect(url_for('search_results'))
    
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

    # Retrieve the associated category via the 'part_of' relationship
    if procedure.part_of and procedure.part_of[0].belongs_to_category:
        category = procedure.part_of[0].belongs_to_category[0]  # Assuming single category
        app.logger.info(f"Procedure '{procedure.title}' is linked to category '{category.title}'.")
    else:
        category = None  # Handle cases where category is not found
        app.logger.warning(f"Procedure '{procedure.title}' is not linked to any category.")

    return render_template(
        'procedure_detail.html',
        form=form,
        procedure=procedure,
        steps=steps,
        missing_tools=missing_tools,
        hazard_steps=hazard_steps,
        category=category,
        category_hierarchy=category_hierarchy,
        category_counts=category_counts
    )

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

    form = SearchForm()
    category_hierarchy, category_counts = populate_facet_choices(form)
    if form.validate_on_submit():
        # Handle form submission from sidebar if needed
        return redirect(url_for('search_results'))
    
    return render_template(
        'procedures_with_many_steps.html',
        form=form,
        title='Procedures with Many Steps',
        procedures=procedures,
        category_hierarchy=category_hierarchy,
        category_counts=category_counts
    )
