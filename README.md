# Nutrient-Rich Recipes Web Application

Welcome to the Nutrient-Rich Recipes Web Application! This application is designed to help users discover recipes that prioritize easiness while also being aware of the nutritional content. Recipes are sorted based on the least amount of missing ingredients first, ensuring a convenient cooking experience with nutrient-rich options.

## Purpose

The primary goal of this application is to provide users with easy-to-follow recipes that are nutritionally balanced. I wanted to prioritize the user's easiness. By sorting recipes based on the least amount of missing ingredients, the app ensures that users can find recipes that are both convenient and packed with essential nutrients.

## Recommended Nutrient Intake (RNI) Groups

The application categorizes users into Recommended Nutrient Intake (RNI) groups based on their sex, age, and weight. This information is collected through a form at the start of the application to determine the user's correct RNI group. Recipes are then compared against the RNI values specific to the user's group to provide personalized nutritional insights.

## Protein RNI Calculation

The application calculates the Recommended Nutrient Intake (RNI) for protein based on the user's weight. The formula used is:

Protein RNI = User's weight * 0.75

This calculated value represents the recommended daily intake of protein for the user. The application then compares this value to the protein content of the food to determine the percentage of the RNI fulfilled by the food.

**Note:** To use the Edamam API for recipe data, you'll need to sign up for an API key and ID on the Edamam website. Visit Edamam's website to sign up and obtain your credentials.

## How it Works

- **Home Page:** Upon accessing the application, users are prompted to fill out a form with their sex, age, and weight. This information is used to determine the user's RNI group.
  
- **Recipe Search:** Users can enter ingredients and optional filters such as meal type, diet label, health label, and glycemic index to search for recipes.
  
- **Recipe Results:** After submitting the search criteria, recipes are displayed based on the least amount of missing ingredients. Each recipe includes nutritional information and a comparison to the user's RNI group, including the percentage of the RNI fulfilled for protein.

## Additional Features

- **Ease of Use:** The application prioritizes easiness by sorting recipes with the least amount of missing ingredients first, ensuring a hassle-free cooking experience.
  
- **Nutrient Awareness:** Users can explore recipes that are not only easy to make but also nutritionally balanced, with a focus on essential vitamins, minerals, and other nutrients.

## Contributing

Contributions to this project are welcome! If you encounter any issues, have suggestions for improvements, or would like to contribute new features, please feel free to submit a pull request or open an issue on GitHub.

## Download and Use

To use this application, follow these steps:

1. Clone the repository to your local machine.
2. Sign up for an API key and ID on the Edamam website.
3. Replace the placeholders in the code with your API key and ID.
4. Run the application locally or deploy it to a web server.
5. Access the application through your web browser and start exploring recipes!

## Troubleshooting and Solutions

In this section, I document common errors and challenges encountered during development and how they were resolved.

- **Issue with Protein RNI Comparison:** Protein RNI comparison was not rendering after the second search of ingredients. It was discovered that the form data was not being lost, but only the "rni_comparison" dict was being rendered. To resolve this, a separate function for RNI comparison was created, and the data was passed onto the template.

- **Issue with Micro Nutrient Per Serving:** The micro_nutrient_per_serving was not iterating over each recipe; instead, it was looping only one recipe and copying the information to the rest. To fix this, micro_nutrients_per_serving was initialized INSIDE the loop of recipes being fetched. Once initialized, micronutrients were calculated and stored in a dictionary, then rendered to the template.

- **Sorting Recipes by Least Amount of Missing Ingredient Lines:** To ensure recipes are sorted correctly, a check was implemented to track whether sorting by the least amount of missing ingredient lines had started. This check ensures accurate sorting based on recipe ingredients.

## Improvements

- Change style of nutrient breakdown to standard nutrient facts label
- Use cookies to save user's information
- Create function to save and combine recipes to count nutrients for the whole day
- Implement macronutrient RNI
- Add filters to find recipes rich in specific nutrients
- dont show nutrients if they are 0
- fix groups (carbs - fibre/sugars....fats - trans/mono/saturated)
