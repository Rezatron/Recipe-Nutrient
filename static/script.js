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
});