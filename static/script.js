// Wait for the DOM content to be fully loaded
document.addEventListener('DOMContentLoaded', function () {
    // Declare overlay variable outside of the event listener
    var overlay = document.querySelector('.popup-overlay');

    // Get all "See more details" buttons
    var detailButtons = document.querySelectorAll('.see-details-button');

    // Add click event listener to each button
    detailButtons.forEach(function (button) {
        button.addEventListener('click', function () {
            // Toggle the visibility of details popup
            var detailsPopup = button.closest('.recipe-item').querySelector('.details-popup'); // Get the details popup within the recipe item
            if (detailsPopup) {
                detailsPopup.classList.toggle('active');
                overlay.classList.toggle('active'); // Toggle overlay visibility

                // Get the close button after it's added to the DOM
                var closeButton = detailsPopup.querySelector('.close-button');
                if (closeButton) {
                    closeButton.addEventListener('click', function () {
                        closePopup();
                    });
                } else {
                    console.error("Close button not found. Waiting for it to be added to the DOM...");
                }
            } else {
                console.error("Details popup not found.");
            }
        });
    });

    // Function to close popup
    function closePopup() {
        var activePopups = document.querySelectorAll('.details-popup.active');
        activePopups.forEach(function (popup) {
            popup.classList.remove('active');
            overlay.classList.remove('active');
        });
    }
});