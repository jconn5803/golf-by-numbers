document.addEventListener("DOMContentLoaded", function () {
    const penaltyCheckbox = document.getElementById("penalty");
    const penaltyOptions = document.getElementById("penalty-options");

    function togglePenaltyOptions() {
        if (penaltyCheckbox.checked) {
            penaltyOptions.style.display = "block"; // Show penalty options
        } else {
            penaltyOptions.style.display = "none"; // Hide penalty options
            // Uncheck any penalty sub-options when hiding
            document.getElementById("oob").checked = false;
            document.getElementById("hazard").checked = false;
        }
    }

    // Attach event listener to checkbox
    penaltyCheckbox.addEventListener("change", togglePenaltyOptions);

});
