// Updated JavaScript to toggle details popup
// Get all "See more details" buttons
var detailButtons = document.querySelectorAll('.see-details-button');

// Add click event listener to each button
detailButtons.forEach(function (button) {
    button.addEventListener('click', function () {
        // Toggle the visibility of details popup
        var detailsPopup = button.closest('.recipe-item').querySelector('.details-popup'); // Get the details popup within the recipe item
        if (detailsPopup) {
            detailsPopup.classList.toggle('active');
        } else {
            console.error("Details popup not found.");
        }
    });
});
