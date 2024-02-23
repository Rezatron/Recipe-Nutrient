from flask import Flask, jsonify, request, render_template, url_for, redirect
import requests
import time
from urllib.parse import quote
from utils import clean_micro_nutrients
from units import nutrient_units
from rni import rni_data

app = Flask(__name__)

# Define the RNI data globally
global_rni = None

SEARCH_LIMIT = 1  # Maximum number of searches allowed within the time window
TIME_WINDOW = 5  # Time window in seconds (e.g., 60 seconds = 1 minute)

# Define a dictionary to store search counts for each IP address
search_counts = {}

# Initialize an empty dictionary for micro_nutrients_per_serving
micro_nutrients_per_serving = {}

# Initialize an empty dictionary for comparison_to_rni
comparison_to_rni = {}

# Function to check if a request exceeds the rate limit
def exceeds_rate_limit(ip_address):
    current_time = time.time()
    if ip_address not in search_counts:
        search_counts[ip_address] = [(current_time, 1)]
        return False
    else:
        search_counts[ip_address] = [(t, c) for t, c in search_counts[ip_address] if current_time - t <= TIME_WINDOW]
        total_searches = sum(count for _, count in search_counts[ip_address])
        return total_searches >= SEARCH_LIMIT

# Define route to fetch recipes based on ingredients
@app.route('/recipes', methods=['GET'])
def fetch_recipes():
    global micro_nutrients_per_serving
    
    ingredients = request.args.get('ingredients')

    # Check if ingredients are provided
    if not ingredients:
        return jsonify({'error': 'Ingredients not provided'}), 400   
    
    # Get the client's IP address
    client_ip = request.remote_addr
    
    # Check if the request exceeds the rate limit
    if exceeds_rate_limit(client_ip):
        return jsonify({'error': 'Rate limit exceeded. Please try again later.'}), 429
    
    # Make the API request to Edamam
    edamam_app_id = 'a076d143'
    edamam_api_key = '3f29819ff208a35c258fee650e32878f'
    encoded_ingredients = quote(ingredients)
    edamam_url = f'https://api.edamam.com/api/recipes/v2?type=public&q={ingredients}&app_id={edamam_app_id}&app_key={edamam_api_key}'
    max_recipes_to_show = 1  # Define the maximum number of recipes to show

    try:
        edamam_response = requests.get(edamam_url)
        if edamam_response.status_code == 200:
            edamam_recipes = edamam_response.json()
            filtered_recipes = []
            for hit in edamam_recipes['hits'][:max_recipes_to_show]:
                recipe = hit['recipe']
                label = recipe['label']
                ingredient_lines = recipe['ingredientLines']
                health_labels = recipe.get('healthLabels', [])
                url = recipe.get('url')
                image = recipe.get('image')
                calories = recipe.get('calories')
                micro_nutrients = recipe.get('totalNutrients', {})
                yield_value = recipe.get('yield', None)

                # Iterate through micro_nutrients and add units dynamically
                for nutrient_label, nutrient_data in micro_nutrients.items():
                    if 'unit' in nutrient_data:
                        nutrient_units[nutrient_label] = nutrient_data['unit']

                # Clean up the micro-nutrients data
                cleaned_micro_nutrients = clean_micro_nutrients(micro_nutrients)
                
                # Calculate values per serving
                calories_per_serving = calories / yield_value
                micro_nutrients_per_serving = {label: value / yield_value for label, value in cleaned_micro_nutrients.items()}  

                # Divide micro_nutrients_per_serving by global_rni if available
                if global_rni:
                    for nutrient_label, nutrient_value in micro_nutrients_per_serving.items():
                        if nutrient_label in global_rni:
                            comparison_to_rni[nutrient_label] = nutrient_value / global_rni[nutrient_label]
                            print("Comparison to RNI for", nutrient_label, ":", comparison_to_rni[nutrient_label])  # Print comparison to RNI for debugging

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
                    'yield': yield_value,
                })

            return render_template('index.html', recipes=filtered_recipes)
        else:
            return jsonify({'error': f'Failed to fetch recipes from Edamam. Status code: {edamam_response.status_code}'}), edamam_response.status_code
    except requests.RequestException as e:
        return jsonify({'error': f'Network Error: {e}'}), 500


# Define route to handle individual recipe requests
@app.route('/recipe/<recipe_id>', methods=['GET'])
def get_recipe(recipe_id):
    edamam_url = f'https://api.edamam.com/api/recipes/v2/{recipe_id}'
    params = {
        'type': 'public',
        'app_id': 'a076d143',
        'app_key': '3f29819ff208a35c258fee650e32878f'
    }

    try:
        response = requests.get(edamam_url, params=params)
        data = response.json()

        if response.status_code == 200:
            recipe_info = data['recipe']
            return jsonify(recipe_info)
        else:
            error_message = data['error'][0]['message']
            return jsonify({'error': error_message}), response.status_code
    except requests.RequestException as e:
        return jsonify({'error': f'Network Error: {e}'}), 500

@app.route('/', methods=['GET', 'POST'])
def form():
    if request.method == 'POST':
        sex = request.form['sex']
        age = request.form['age']
        return redirect(url_for('index', sex=sex, age=age))
    return render_template('form.html')


# Define index route
@app.route('/index', methods=['GET'])
def index():
    global global_rni
    global micro_nutrients_per_serving
    global comparison_to_rni
    
    sex = request.args.get('sex')
    age = request.args.get('age')

    if sex and age:
        age = int(age)
        if age >= 11 and age <= 14:
            age_group = "11-14 years"
        elif age >= 15 and age <= 18:
            age_group = "15-18 years"
        elif age >= 19 and age <= 50:
            age_group = "19-50 years"
        else:
            age_group = "50+ years"

        if sex.lower() == 'male':
            if age_group in rni_data["Micronutrients"]["Males"]:
                global_rni = rni_data["Micronutrients"]["Males"][age_group]
                print("global_rni set for Male ({} years):".format(age), global_rni)  # Print global_rni for debugging

                # Divide micro_nutrients_per_serving by global_rni if available
                if global_rni:
                    for nutrient_label, nutrient_value in micro_nutrients_per_serving.items():
                        if nutrient_label in global_rni:
                            comparison_to_rni[nutrient_label] = nutrient_value / global_rni[nutrient_label]
                            print("Comparison to RNI for", nutrient_label, ":", comparison_to_rni[nutrient_label])  # Print comparison to RNI for debugging
        elif sex.lower() == 'female':
            if age_group in rni_data["Micronutrients"]["Females"]:
                global_rni = rni_data["Micronutrients"]["Females"][age_group]
                print("global_rni set for Female ({} years):".format(age), global_rni)  # Print global_rni for debugging

                # Divide micro_nutrients_per_serving by global_rni if available
                if global_rni:
                    for nutrient_label, nutrient_value in micro_nutrients_per_serving.items():
                        if nutrient_label in global_rni:
                            try:
                                print("Nutrient value:", nutrient_value)
                                print("Global RNI value:", global_rni[nutrient_label])
                                # Calculate the percentage
                                percentage = nutrient_value / global_rni[nutrient_label] * 100
                                comparison_to_rni[nutrient_label] = f"{percentage:.2f}%"  # Format as percentage with 2 decimal places
                                print("Comparison to RNI for", nutrient_label, ":", comparison_to_rni[nutrient_label])  # Print comparison to RNI for debugging
                            except Exception as e:
                                print("Error calculating percentage for", nutrient_label, ":", e)



    return render_template('index.html', comparison_to_rni=comparison_to_rni)

if __name__ == '__main__':
    app.run(debug=True)
