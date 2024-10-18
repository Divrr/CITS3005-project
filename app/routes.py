# app/routes.py
from flask import render_template, request, redirect, url_for
from app import app
from app.forms import SearchForm
from app.ontology import onto
import logging
from app.helper import populate_facet_choices, get_all_subcategories, select_all_selected_category_titles, find_all_matching_procedures

# Configure logging
logging.basicConfig(level=logging.INFO)

@app.route('/', methods=['GET', 'POST'])
def index():
    form = SearchForm()

    category_hierarchy, category_counts = populate_facet_choices(form)

    if form.validate_on_submit():
        return redirect(url_for('search_results'))
    
    return render_template(
        'index.html',
        title='Homepage',
        form=form,
        category_hierarchy=category_hierarchy,
        category_counts=category_counts
    )

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

    selected_categories = select_all_selected_category_titles(selected_categories) # finds all subcategories of selected categories
    matching_procedures = find_all_matching_procedures(query, selected_categories, selected_tools, selected_parts)

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
        return redirect(url_for('search_results'))
    
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

    parent_category = category.subcategory_of[0] if category.subcategory_of else None
    app.logger.info(f"Parent category for '{category.title}' is '{parent_category}'")

    # initialise the search form and populate facet choices
    form = SearchForm()
    category_hierarchy, category_counts = populate_facet_choices(form)
    
    if form.validate_on_submit():
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
    procedure = onto.search_one(guidid=guidid)

    if not procedure:
        app.logger.error(f"Procedure with guidid '{guidid}' not found.")
        return render_template('404.html'), 404

    form = SearchForm()
    category_hierarchy, category_counts = populate_facet_choices(form)
    
    if form.validate_on_submit():
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
