document.addEventListener("DOMContentLoaded", function() {
    // Clear form and reset penalty options
    document.getElementById("clear-button").addEventListener("click", function() {
        document.getElementById("calculator-form").reset();
        document.getElementById("penalty-options").style.display = "none";
        document.getElementById("after_distance").disabled = false;
    });

    // Update labels and handle "In the Hole" logic
    function updateLabels() {
        const unitToggle = document.getElementById("unit-toggle");
        const beforeLie = document.getElementById("before_lie").value;
        const afterLie = document.getElementById("after_lie").value;

        const beforeDistanceLabel = document.getElementById("before-distance-label");
        const afterDistanceLabel = document.getElementById("after-distance-label");
        const afterDistanceInput = document.getElementById("after_distance");

        // Update distance labels based on unit and lie
        if (unitToggle.checked) {
            beforeDistanceLabel.textContent = "Distance to hole before shot (Metres)";
            afterDistanceLabel.textContent = "Distance to hole after shot (Metres)";
        } else {
            beforeDistanceLabel.textContent =
                beforeLie === "Green" ? "Distance to hole before shot (Feet)" : "Distance to hole before shot (Yards)";
            afterDistanceLabel.textContent =
                afterLie === "Green" ? "Distance to hole after shot (Feet)" : "Distance to hole after shot (Yards)";
        }

        // Disable after_distance if "In the Hole" is selected
        if (afterLie === "In the Hole") {
            afterDistanceInput.value = 0;
            afterDistanceInput.disabled = true;
        } else {
            afterDistanceInput.disabled = false;
        }
    }

    // Event listeners for unit toggle and lie changes
    document.getElementById("unit-toggle").addEventListener("change", updateLabels);
    document.getElementById("before_lie").addEventListener("change", updateLabels);
    document.getElementById("after_lie").addEventListener("change", updateLabels);

    // Initial call to set labels
    updateLabels();
});