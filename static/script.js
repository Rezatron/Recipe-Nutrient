// Update the JavaScript to toggle visibility when the button is clicked
var detailButtons = document.querySelectorAll('.see-details-button');

detailButtons.forEach(function (button) {
    button.addEventListener('click', function () {
        var detailsContainer = button.parentElement.querySelector('.details-popup');
        if (detailsContainer) {
            detailsContainer.classList.toggle('active');
        }
    });
});