problems with protein rni comparison... seems to not be rendering after the second search of ingredients... 
rni comparison for other nutrients work but not protein... the form data is not being lost... or is it that only the "rni_comparison" dict is being rendered?
when protein rni comparison was in index it was being calculated after form submission.. moved to fetch recipe 
SOLVED: created separate function for rni comparison to be calculated. then passed onto template.


ISSUE: micro_nutrient_per_serving not iterating over each recipe (only loops 1 recipe then copies n pastes the info to the rest of the recipes)
SOLVED: initialise micro_nutrients_per_serving INSIDE loop of recipes being fetched 
        once initalised, micronutrients are calculated and stored in dict then rendered to template




SORT BY LEAST AMOUNT OF MISSING INGREDIENT LINES
started?YES
set(x['recipe']['ingredientLines']) - set(ingredients.split(',')):              ###### ingredient lines from recipe (-) user's input ingredients
len(...)                                                                        ###### counts the above

