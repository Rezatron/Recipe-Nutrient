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
                print(micro_nutrients_per_serving) #debug
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

         # Pass comparison_to_rni to the template context
        return render_template('index.html', recipes=filtered_recipes, comparison_to_rni=comparison_to_rni)

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
        weight = request.form['weight']
        return redirect(url_for('index', sex=sex, age=age, weight=weight))
    return render_template('form.html')


# Define index route
@app.route('/index', methods=['GET'])
def index():
    global global_rni
    global micro_nutrients_per_serving
    global comparison_to_rni

    sex = request.args.get('sex')
    age = request.args.get('age')
    weight = request.args.get('weight')
    # Initialize comparison_to_rni dictionary
    comparison_to_rni = {}
    print("Accessing the index route")
    if sex and age and weight:
        age = int(age)
        weight = float(weight)

        # Calculate protein RNI
        protein_rni = 0.75 * weight
        
        print("Protein RNI:", protein_rni)

        # Determine age group
        if age >= 11 and age <= 14:
            age_group = "11-14 years"
        elif age >= 15 and age <= 18:
            age_group = "15-18 years"
        elif age >= 19 and age <= 50:
            age_group = "19-50 years"
        else:
            age_group = "50+ years"

        # Determine sex group and retrieve corresponding RNI data
        if sex.lower() == 'male':
            if age_group in rni_data["Micronutrients"]["Males"]:
                global_rni = rni_data["Micronutrients"]["Males"][age_group]

                # Calculate micro-nutrient comparison to RNI
                if global_rni:
                    for nutrient_label, nutrient_value in micro_nutrients_per_serving.items():
                        if nutrient_label in global_rni:
                            comparison_to_rni[nutrient_label] = nutrient_value / global_rni[nutrient_label]
        elif sex.lower() == 'female':
            if age_group in rni_data["Micronutrients"]["Females"]:
                global_rni = rni_data["Micronutrients"]["Females"][age_group]

                # Calculate micro-nutrient comparison to RNI

        # Calculate protein intake from the meal
        protein_intake = micro_nutrients_per_serving.get('Protein', 0)

        # Calculate the percentage of protein RNI compared to the protein intake from the meal
        if protein_intake != 0:  # Avoid division by zero
            protein_rni_percentage = (protein_intake / protein_rni) 
            comparison_to_rni['Protein'] = protein_rni_percentage
        
        # Add protein RNI to comparison_to_rni dictionary
        comparison_to_rni['Protein_RNI'] = protein_rni  # Add this line

        # Pass comparison_to_rni dictionary to the template
        return render_template('index.html', comparison_to_rni=comparison_to_rni)
    else:
        # Handle case where required parameters are missing
        return 'Missing required parameters', 400  # Return an error response with status code 400


if __name__ == '__main__':
    app.run(debug=True)



"""PROTEIN RNI NOTES



"""
