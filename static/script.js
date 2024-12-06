// Wait for the DOM content to be fully loaded
document.addEventListener('DOMContentLoaded', function () {
    var overlay = document.querySelector('.popup-overlay');
    var detailButtons = document.querySelectorAll('.see-details-button');

    detailButtons.forEach(function (button) {
        button.addEventListener('click', function () {
            var detailsPopup = button.closest('.recipe-item').querySelector('.details-popup');
            if (detailsPopup) {
                detailsPopup.classList.toggle('active');
                overlay.classList.toggle('active');

                var closeButton = detailsPopup.querySelector('.close-button');
                if (closeButton) {
                    closeButton.addEventListener('click', function () {
                        closePopup();
                    });
                } else {
                    console.error("Close button not found.");
                }
            } else {
                console.error("Details popup not found.");
            }
        });
    });

    function closePopup() {
        var activePopups = document.querySelectorAll('.details-popup.active');
        activePopups.forEach(function (popup) {
            popup.classList.remove('active');
        });
        overlay.classList.remove('active');
    }

    document.querySelectorAll('.save-recipe-btn').forEach(function (button) {
        button.addEventListener('click', function (event) {
            event.preventDefault(); // Prevent the default form submission
            // Retrieve the recipe data from the button's data attribute
            let recipeData = JSON.parse(this.getAttribute('data-recipe'));

            // Send the AJAX request
            fetch('/save_recipe', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('input[name="csrf_token"]').value  // CSRF token for Flask-WTF
                },
                body: JSON.stringify({ recipe_data: recipeData })
            })
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.success) {
                        alert(data.message || 'Recipe saved successfully!');
                    } else {
                        alert('Error saving recipe: ' + (data.error || 'Unknown error'));
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('Failed to save recipe.');
                });
        });
    });
});