"""def estimate_servings(ingredient_weights, total_calories, standard_calories_per_serving=500, standard_weight_per_serving=200):
    # Calculate total weight of ingredients
    total_weight = sum(ingredient_weights)
    
    # Estimate servings based on calories
    servings_by_calories = total_calories / standard_calories_per_serving
    
    # Estimate servings based on weight
    servings_by_weight = total_weight / standard_weight_per_serving
    
    # Average the estimates from both methods
    estimated_servings = (servings_by_calories + servings_by_weight) / 2
    
    return estimated_servings"""