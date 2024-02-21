from flask import Flask, Blueprint, jsonify, request, render_template, url_for,redirect
import requests
import time
from urllib.parse import quote
from utils import clean_micro_nutrients
from units import nutrient_units

app = Flask(__name__)


SEARCH_LIMIT = 1  # Maximum number of searches allowed within the time window
TIME_WINDOW = 5  # Time window in seconds (e.g., 60 seconds = 1 minute)

# Define a dictionary to store search counts for each IP address
search_counts = {}

# Function to check if a request exceeds the rate limit
def exceeds_rate_limit(ip_address):
    current_time = time.time()
    #print(f"Current time: {current_time}")

    if ip_address not in search_counts:
        search_counts[ip_address] = [(current_time, 1)]
        return False
    else:
        # Remove old entries from the search counts list
        search_counts[ip_address] = [(t, c) for t, c in search_counts[ip_address] if current_time - t <= TIME_WINDOW]
        print(f"Search counts for {ip_address}: {search_counts[ip_address]}")
        
        # Calculate the total number of searches within the time window
        total_searches = sum(count for _, count in search_counts[ip_address])
        print(f"Total searches for {ip_address} within time window: {total_searches}")
        
        return total_searches >= SEARCH_LIMIT

# Define a route to fetch recipes based on ingredients
@app.route('/recipes', methods=['GET'])
def fetch_recipes():
    # Extract ingredients from the query parameters
    ingredients = request.args.get('ingredients')

    
    # Check if ingredients are provided
    if not ingredients:
        # Debugging: Print a message to indicate that ingredients are not provided
        print("Error: Ingredients not provided")
        return jsonify({'error': 'Ingredients not provided'}), 400   
    
    # Get the client's IP address
    client_ip = request.remote_addr
    # Debugging: Print the client's IP address
    #print("Client IP:", client_ip)
    
    # Check if the request exceeds the rate limit
    if exceeds_rate_limit(client_ip):
        # Debugging: Print a message to indicate that the rate limit is exceeded
        print("Error: Rate limit exceeded")
        return jsonify({'error': 'Rate limit exceeded. Please try again later.'}), 429
    
    # Make the API request
    edamam_app_id = 'a076d143'
    edamam_api_key = '3f29819ff208a35c258fee650e32878f'
    # Properly encode the ingredients string
    encoded_ingredients = quote(ingredients)
    # Construct the API request URL with the encoded ingredients
    edamam_url = f'https://api.edamam.com/api/recipes/v2?type=public&q={ingredients}&app_id={edamam_app_id}&app_key={edamam_api_key}'
    #print(edamam_url)

    # Debugging: Print the Edamam API URL
    #print("Edamam API URL:", edamam_url)

    max_recipes_to_show = 1

    try:
        # Make the API request
        edamam_response = requests.get(edamam_url)
        # Check if the request was successful
        if edamam_response.status_code == 200:
            # Parse the JSON response
            edamam_recipes = edamam_response.json()
            # Extract relevant details for each recipe
            filtered_recipes = []
            for hit in edamam_recipes['hits'][:max_recipes_to_show]:
                recipe = hit['recipe']
                label = recipe['label']
                ingredient_lines = recipe['ingredientLines']
                health_labels = recipe.get('healthLabels', [])  # Extract health labels (if available)
                url = recipe.get('url')  # Extract the URL for the recipe
                image = recipe.get('image')  # Extract the image URL for the recipe
                calories = recipe.get('calories')  # Extract the calories for the recipe
                micro_nutrients = recipe.get('totalNutrients', {})  # Extract total nutrients
                yield_value = recipe.get('yield', None)
                # testing for bugs
                #print("Micro-nutrients (before division):", micro_nutrients)  
                # Extracting the four types of fats
                fatty_acids_fams = micro_nutrients.get('FAMS', {}).get('quantity', 0)
                fatty_acids_fapu = micro_nutrients.get('FAPU', {}).get('quantity', 0)
                fatty_acids_fasat = micro_nutrients.get('FASAT', {}).get('quantity', 0)
                fatty_acids_fatrn = micro_nutrients.get('FATRN', {}).get('quantity', 0)

                # Iterate through micro_nutrients and add units dynamically
                for nutrient_label, nutrient_data in micro_nutrients.items():
                    if 'unit' in nutrient_data:
                        nutrient_units[nutrient_label] = nutrient_data['unit']
                # Clean up the micro-nutrients data
                cleaned_micro_nutrients = clean_micro_nutrients(micro_nutrients)
                
                # Calculate values per serving
                calories_per_serving = calories / yield_value
                micro_nutrients_per_serving = {label: value / yield_value for label, value in cleaned_micro_nutrients.items()}  
                # Append extracted details to the filtered_recipes list
                filtered_recipes.append({
                    'label': label,
                    'ingredient_lines': ingredient_lines,
                    'ingredients': ingredients,
                    'url': url,
                    'image': image,
                    'calories_per_serving': calories_per_serving,
                    'micro_nutrients_per_serving': micro_nutrients_per_serving,
                    'nutrient_units': nutrient_units,
                    'fatty_acids_fams': fatty_acids_fams,
                    'fatty_acids_fapu': fatty_acids_fapu,
                    'fatty_acids_fasat': fatty_acids_fasat,
                    'fatty_acids_fatrn': fatty_acids_fatrn, 
                    'yield': yield_value,  # Add the yield value to the response
                     
                    # Add more details as needed
                })
            return render_template('index.html', recipes=filtered_recipes)
        else:
            # Handle unsuccessful request
            return jsonify({'error': f'Failed to fetch recipes from Edamam. Status code: {edamam_response.status_code}'}), edamam_response.status_code
    except requests.RequestException as e:
        # Handle network errors
        return jsonify({'error': f'Network Error: {e}'}), 500







#/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////// 
#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
    

# Define route to handle individual recipe requests
@app.route('/recipe/<recipe_id>', methods=['GET'])
def get_recipe(recipe_id):
    # Construct the URL for the specific recipe endpoint
    edamam_url = f'https://api.edamam.com/api/recipes/v2/{recipe_id}'

    # Parameters for the request
    params = {
        'type': 'public',  # Specify the type of recipes to search for
        'app_id': 'a076d143',
        'app_key': '3f29819ff208a35c258fee650e32878f'
    }

    try:
        # Make the API request
        response = requests.get(edamam_url, params=params)
        data = response.json()

        if response.status_code == 200:
            # Extract the recipe information from the response
            recipe_info = data['recipe']
            return jsonify(recipe_info)
        else:
            # Handle unsuccessful request
            error_message = data['error'][0]['message']
            return jsonify({'error': error_message}), response.status_code
    except requests.RequestException as e:
        # Handle network errors
        return jsonify({'error': f'Network Error: {e}'}), 500


#/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////// 
#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
    
"""@app.route('/', methods=['GET', 'POST'])
def form():
    if request.method == 'POST':
        # Get sex and age from the form
        sex = request.form.get('sex')
        age = request.form.get('age')
        # Redirect to the page where you input ingredients
        return redirect(url_for('index', _anchor="content"))
    # If it's a GET request, render the form template
    return render_template('form.html')    """

# Define form route
@app.route('/', methods=['GET', 'POST'])
def form():
    if request.method == 'POST':
        # Get form data
        sex = request.form['sex']
        age = request.form['age']

        # check for bugs
        print("Sex:", sex)
        print("Age:", age)

        # Redirect to index page with parameters
        return redirect(url_for('index', sex=sex, age=age))
    return render_template('form.html')


# Define index route
@app.route('/index')
def index():
    return render_template('index.html')






if __name__ == '__main__':
    app.run(debug=True)