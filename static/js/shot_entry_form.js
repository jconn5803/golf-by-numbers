 /********************************************
     *    1) ADD SHOT
     ********************************************/
 function addShot(holeNumber, par) {
    const shotsContainer = document.getElementById(`hole_${holeNumber}_shots`);

    // Preserve existing form data
    const form = document.getElementById('add-shots-form');
    const formData = new FormData(form);

    // Compute the next shot label based on total .shot-card count
    const newShotNumber = getNextShotNumber(holeNumber);

    // Count existing shots for the hole
    const existingShots = shotsContainer.querySelectorAll(
        `[id^="hole_${holeNumber}_shot_"][id$="_distance"]`
    );
    const newShotNum = existingShots.length + 1;

    // Decide what the preselected lie should be
    let preselectedLie = 'Fairway';
    if (existingShots.length > 0) {
        if (existingShots.length > par - 3) { 
            // If we are beyond the usual "in regulation" shot, 
            // we'll default to Green next time
            preselectedLie = 'Green';         
        }
    }

    // Based on preselectedLie, decide whether to show feet or yards initially
    const distanceLabel = (preselectedLie === 'Green') 
        ? 'Distance (feet):' 
        : 'Distance (yards):';

    // Build the HTML string for the new shot
    const newShotHTML = `
        <div class="shot-card" id="hole_${holeNumber}_shot_${newShotNum}">
            <h5>Shot #${newShotNumber}</h5>
            <div class="mb-3">
                <label 
                    for="hole_${holeNumber}_shot_${newShotNum}_distance" 
                    class="form-label"
                >
                    ${distanceLabel}
                </label>
                <input 
                    type="number" 
                    class="form-control" 
                    name="hole_${holeNumber}_shot_${newShotNum}_distance" 
                    id="hole_${holeNumber}_shot_${newShotNum}_distance" 
                    required
                >
            </div>
            <div class="mb-3">
                <label 
                    for="hole_${holeNumber}_shot_${newShotNum}_lie" 
                    class="form-label"
                >
                    Lie:
                </label>
                <select 
                    class="form-select" 
                    name="hole_${holeNumber}_shot_${newShotNum}_lie" 
                    id="hole_${holeNumber}_shot_${newShotNum}_lie" 
                    required 
                    onchange="updateDistanceLabel(${holeNumber}, ${newShotNum}); 
                            updateMissDirection(${holeNumber}, ${newShotNum}, ${par});"
                >
                    <option value="Tee"      ${preselectedLie === 'Tee'     ? 'selected' : ''}>Tee</option>
                    <option value="Fairway"  ${preselectedLie === 'Fairway' ? 'selected' : ''}>Fairway</option>
                    <option value="Rough"    ${preselectedLie === 'Rough'   ? 'selected' : ''}>Rough</option>
                    <option value="Bunker"   ${preselectedLie === 'Bunker'  ? 'selected' : ''}>Bunker</option>
                    <option value="Recovery" ${preselectedLie === 'Recovery'? 'selected' : ''}>Recovery</option>
                    <option value="Green"    ${preselectedLie === 'Green'   ? 'selected' : ''}>Green</option>
                </select>
            </div>
            <div class="form-check form-check-inline">
                <input 
                    type="checkbox" 
                    class="form-check-input" 
                    name="hole_${holeNumber}_shot_${newShotNum}_out_of_bounds" 
                    id="hole_${holeNumber}_shot_${newShotNum}_out_of_bounds" 
                    value="1"
                    onchange="addDummyShot(${holeNumber}, ${newShotNum}, 'OOB', ${par})"
                >
                <label 
                    class="form-check-label" 
                    for="hole_${holeNumber}_shot_${newShotNum}_out_of_bounds"
                >
                    Out of Bounds
                </label>
            </div>
            <div class="form-check form-check-inline">
                <input 
                    type="checkbox" 
                    class="form-check-input" 
                    name="hole_${holeNumber}_shot_${newShotNum}_hazard" 
                    id="hole_${holeNumber}_shot_${newShotNum}_hazard" 
                    value="1"
                    onchange="addDummyShot(${holeNumber}, ${newShotNum}, 'hazard', ${par})"
                >
                <label 
                    class="form-check-label" 
                    for="hole_${holeNumber}_shot_${newShotNum}_hazard"
                >
                    Hazard/Unplayable
                </label>
            </div>
            <button 
                type="button" 
                class="btn btn-danger btn-sm remove-shot-btn" 
                onclick="removeShot(${holeNumber}, ${newShotNum})"
            >
                Remove Shot
            </button>
        </div>
    `;

    // Insert the newShotHTML into the page
    shotsContainer.insertAdjacentHTML('beforeend', newShotHTML);

    // Restore the previously entered form data
    for (const [key, value] of formData.entries()) {
        const input = document.querySelector(`[name="${key}"]`);
        if (input) {
            input.value = value;
        }
    }

    // Update the remove-shot buttons so only the last shot has it visible
    updateRemoveShotButtons(holeNumber);

    // Optionally call updateMissDirection if needed
    updateMissDirection(holeNumber, newShotNum, par);
}

/********************************************
 *    2) REMOVE SHOT
 ********************************************/
function removeShot(holeNumber, shotNumber) {
    const shotElement = document.getElementById(`hole_${holeNumber}_shot_${shotNumber}`);
    if (shotElement) {
        shotElement.remove();
        // After removing, re-check which shot is last and show/hide remove buttons
        updateRemoveShotButtons(holeNumber);
    }
}

/********************************************
 *    3) UPDATE THE "MISS DIRECTION" UI
 ********************************************/
function updateMissDirection(holeNumber, shotNumber, par) {
    console.log(`updateMissDirection called with: holeNumber=${holeNumber}, shotNumber=${shotNumber}, par=${par}`);

    const lieElement = document.getElementById(`hole_${holeNumber}_shot_${shotNumber}_lie`);
    const previousLieElement = document.getElementById(`hole_${holeNumber}_shot_${shotNumber - 1}_lie`);
    const previousShotContainer = document.getElementById(`hole_${holeNumber}_shot_${shotNumber - 1}`);
    if (!lieElement || !previousLieElement || !previousShotContainer) {
        console.error("Missing lie element or previous shot container.");
        return;
    }

    // 1) Determine the current UI type (if any)
    let currentUI = "none";
    const existingMissDirection = document.getElementById(`hole_${holeNumber}_shot_${shotNumber - 1}_miss_direction`);
    if (existingMissDirection) {
        // If there's a radio group present, it's the L/R UI.
        if (existingMissDirection.querySelectorAll('input[type="radio"][name*="_miss_direction"]').length === 2) {
            currentUI = "leftright";
        } 
        // Otherwise, if there's a compass container, it's the compass UI.
        else if (existingMissDirection.querySelector('.compass-container')) {
            currentUI = "compass";
        }
    }
    console.log("Current UI type:", currentUI);

    // 2) Determine the new UI type
    let newUI = "none";
    // For a non-par 3 Tee shot that missed Fairway/Green => use "leftright" UI.
    if (previousLieElement.value === "Tee" && par !== 3 && lieElement.value !== "Fairway" && lieElement.value !== "Green") {
        newUI = "leftright";
    } 
    // For an approach or par-3 tee shot => "compass" UI.
    else if (
        (lieElement.value !== "Green" && previousLieElement.value !== "Recovery" && previousLieElement.value !== "Tee") ||
        (lieElement.value !== "Green" && par === 3)
    ) {
        newUI = "compass";
    }
    console.log("New UI type:", newUI);

    // 3) If UI type has not changed, do not re-render
    if (currentUI === newUI) {
        console.log(`UI type remains "${newUI}". Retaining existing selection.`);
        return;
    }

    // 4) Preserve current form data so we don't lose any values.
    const form = document.getElementById('add-shots-form');
    const formData = new FormData(form);

    // 5) Remove any existing miss-direction UI in the previous shot.
    if (existingMissDirection) {
        existingMissDirection.remove();
    }

    // 6) Insert the new UI
    if (newUI === "leftright") {
        const lrSelector = `
            <div class="mb-3" id="hole_${holeNumber}_shot_${shotNumber - 1}_miss_direction">
                <label class="form-label">Miss Direction:</label>
                <div class="btn-group" role="group">
                    <input 
                        type="radio" 
                        class="btn-check" 
                        name="hole_${holeNumber}_shot_${shotNumber - 1}_miss_direction" 
                        id="hole_${holeNumber}_shot_${shotNumber - 1}_left" 
                        value="Left" 
                        required
                    >
                    <label class="btn btn-outline-secondary" for="hole_${holeNumber}_shot_${shotNumber - 1}_left">L</label>
    
                    <input 
                        type="radio" 
                        class="btn-check" 
                        name="hole_${holeNumber}_shot_${shotNumber - 1}_miss_direction" 
                        id="hole_${holeNumber}_shot_${shotNumber - 1}_right" 
                        value="Right" 
                        required
                    >
                    <label class="btn btn-outline-secondary" for="hole_${holeNumber}_shot_${shotNumber - 1}_right">R</label>
                </div>
            </div>
        `;
        previousShotContainer.insertAdjacentHTML('beforeend', lrSelector);
    } else if (newUI === "compass") {
        const compassSelector = `
            <div class="mb-3" id="hole_${holeNumber}_shot_${shotNumber - 1}_miss_direction">
                <label class="form-label">Miss Direction:</label>
                <div class="compass-container">
                    <div class="compass-buttons">
                        <button type="button" class="compass-btn" data-direction="Long">Long</button>
                        <button type="button" class="compass-btn" data-direction="Long Right">Long Right</button>
                        <button type="button" class="compass-btn" data-direction="Right">Right</button>
                        <button type="button" class="compass-btn" data-direction="Short Right">Short Right</button>
                        <button type="button" class="compass-btn" data-direction="Short">Short</button>
                        <button type="button" class="compass-btn" data-direction="Short Left">Short Left</button>
                        <button type="button" class="compass-btn" data-direction="Left">Left</button>
                        <button type="button" class="compass-btn" data-direction="Long Left">Long Left</button>
                    </div>
                </div>
                <input 
                    type="hidden" 
                    name="hole_${holeNumber}_shot_${shotNumber - 1}_miss_direction" 
                    id="hole_${holeNumber}_shot_${shotNumber - 1}_miss_direction_input" 
                    required
                >
            </div>
        `;
        previousShotContainer.insertAdjacentHTML('beforeend', compassSelector);
    }
}

// Event delegation for compass buttons
document.addEventListener('click', function(event) {
    if (event.target.classList.contains('compass-btn')) {
        event.preventDefault();

        // Find the closest compass-container element.
        const compassContainer = event.target.closest('.compass-container');
        if (!compassContainer) return;
        // Remove the "selected" class from all compass buttons in this container.
        const allCompassBtns = compassContainer.querySelectorAll('.compass-btn');
        allCompassBtns.forEach(btn => btn.classList.remove('selected'));
        // Add the "selected" class to the clicked button.
        event.target.classList.add('selected');

        // Update the hidden input field.
        const parentDiv = compassContainer.parentElement;
        const hiddenInput = parentDiv.querySelector(`input[type="hidden"][name*="_miss_direction"]`);
        if (hiddenInput) {
            hiddenInput.value = event.target.dataset.direction;
            console.log("Updated hidden input value:", hiddenInput.value);
        }
    }
});

/********************************************
 *    4) ADD DUMMY SHOT FOR PENALTIES
 ********************************************/
function addDummyShot(holeNumber, shotNumber, penaltyType, par) {
    const dummyShotId = `hole_dummy_${holeNumber}_shot_${shotNumber}_dummy_${penaltyType.toLowerCase()}`;
    const nextShotId = `hole_${holeNumber}_shot_${shotNumber + 1}`;
    const existingDummyShot = document.getElementById(dummyShotId);
    const existingNextShot = document.getElementById(nextShotId);

    // Get the values of the current shot
    const currentDistance = document.getElementById(`hole_${holeNumber}_shot_${shotNumber}_distance`).value;
    const currentLie = document.getElementById(`hole_${holeNumber}_shot_${shotNumber}_lie`).value;
    
    const penaltyCheckbox = document.getElementById(
        `hole_${holeNumber}_shot_${shotNumber}_${penaltyType === "OOB" ? "out_of_bounds" : "hazard"}`
    );

    // ID for a potential miss-direction element
    const directionSelectorId = `hole_${holeNumber}_shot_${shotNumber}_miss_direction`;
    const existingDirectionSelector = document.getElementById(directionSelectorId);

    // If the checkbox is checked, there's no existing direction UI, current lie is "Tee", and par == 3 => show compass
    // Else if par != 3 => show L/R
    if (
        penaltyCheckbox.checked && 
        !existingDirectionSelector && 
        currentLie === "Tee"
      ) {
          const currentShotElement = document.getElementById(
            `hole_${holeNumber}_shot_${shotNumber}`
          );
  
          let directionSelectorHTML = "";
  
          if (par === 3) {
              // Show compass if it's a par-3
              directionSelectorHTML = `
                <div class="mb-3" id="${directionSelectorId}">
                    <label class="form-label">Miss Direction:</label>
                    <div class="compass-container">
                        <div class="compass-buttons">
                            <button type="button" class="compass-btn" data-direction="Long">Long</button>
                            <button type="button" class="compass-btn" data-direction="Long Right">Long Right</button>
                            <button type="button" class="compass-btn" data-direction="Right">Right</button>
                            <button type="button" class="compass-btn" data-direction="Short Right">Short Right</button>
                            <button type="button" class="compass-btn" data-direction="Short">Short</button>
                            <button type="button" class="compass-btn" data-direction="Short Left">Short Left</button>
                            <button type="button" class="compass-btn" data-direction="Left">Left</button>
                            <button type="button" class="compass-btn" data-direction="Long Left">Long Left</button>
                        </div>
                    </div>
                    <input 
                        type="hidden" 
                        name="hole_${holeNumber}_shot_${shotNumber}_miss_direction" 
                        id="${directionSelectorId}_input" 
                        required
                    >
                </div>
              `;
          } else {
              // Default to left/right if par != 3
              directionSelectorHTML = `
                <div class="mb-3" id="${directionSelectorId}">
                    <label class="form-label">Miss Direction:</label>
                    <div class="btn-group" role="group">
                        <input 
                            type="radio" 
                            class="btn-check" 
                            name="hole_${holeNumber}_shot_${shotNumber}_miss_direction" 
                            id="${directionSelectorId}_left" 
                            value="Left" 
                            required
                        >
                        <label class="btn btn-outline-secondary" for="${directionSelectorId}_left">L</label>
  
                        <input 
                            type="radio" 
                            class="btn-check" 
                            name="hole_${holeNumber}_shot_${shotNumber}_miss_direction" 
                            id="${directionSelectorId}_right" 
                            value="Right" 
                            required
                        >
                        <label class="btn btn-outline-secondary" for="${directionSelectorId}_right">R</label>
                    </div>
                </div>
              `;
          }
        currentShotElement.insertAdjacentHTML("beforeend", directionSelectorHTML);
    }
    // If the checkbox is unchecked and lrSelector exists, remove it
    else if (!penaltyCheckbox.checked && existingDirectionSelector) {
        existingLrSelector.remove();
    }

    // If the checkbox is checked and no dummy shot exists, create both dummy and new shot
    if (penaltyCheckbox.checked && !existingDummyShot) {
        const shotsContainer = document.getElementById(`hole_${holeNumber}_shots`);
        const penaltyShotNumber = getNextShotNumber(holeNumber);

        // Create dummy shot HTML
        const dummyShotHTML = `
            <div class="shot-card" id="${dummyShotId}">
                <h5>Shot #${penaltyShotNumber}</h5>
                <div class="mb-3">
                    <label for="${dummyShotId}_distance" class="form-label">Distance (yards):</label>
                    <input 
                        type="text" 
                        class="form-control" 
                        name="${dummyShotId}_distance" 
                        id="${dummyShotId}_distance" 
                        value="Penalty" 
                        readonly
                    >
                </div>
                <div class="mb-3">
                    <label for="${dummyShotId}_lie" class="form-label">Lie:</label>
                    <input 
                        type="text" 
                        class="form-control" 
                        name="${dummyShotId}_lie" 
                        id="${dummyShotId}_lie" 
                        value="Penalty" 
                        readonly
                    >
                </div>
            </div>
        `;

        // Create new shot HTML with prefilled distance and lie
        const replacementShotNumber = getNextShotNumber(holeNumber) + 1;
        const nextShotHTML = `
            <div class="shot-card" id="${nextShotId}">
                <h5>Shot #${replacementShotNumber}</h5>
                <div class="mb-3">
                    <label for="hole_${holeNumber}_shot_${shotNumber + 1}_distance" class="form-label">Distance (yards):</label>
                    <input 
                        type="number" 
                        class="form-control" 
                        name="hole_${holeNumber}_shot_${shotNumber + 1}_distance" 
                        id="hole_${holeNumber}_shot_${shotNumber + 1}_distance" 
                        value="${currentDistance}" 
                        required
                    >
                </div>
                <div class="mb-3">
                    <label for="hole_${holeNumber}_shot_${shotNumber + 1}_lie" class="form-label">Lie:</label>
                    <select 
                        class="form-select" 
                        name="hole_${holeNumber}_shot_${shotNumber + 1}_lie" 
                        id="hole_${holeNumber}_shot_${shotNumber + 1}_lie" 
                        required
                    >
                        <option value="Tee" ${currentLie === "Tee" ? "selected" : ""}>Tee</option>
                        <option value="Fairway" ${currentLie === "Fairway" ? "selected" : ""}>Fairway</option>
                        <option value="Rough" ${currentLie === "Rough" ? "selected" : ""}>Rough</option>
                        <option value="Bunker" ${currentLie === "Bunker" ? "selected" : ""}>Bunker</option>
                        <option value="Recovery" ${currentLie === "Recovery" ? "selected" : ""}>Recovery</option>
                        <option value="Green" ${currentLie === "Green" ? "selected" : ""}>Green</option>
                    </select>
                </div>
                <div class="form-check form-check-inline">
                    <input 
                        type="checkbox" 
                        class="form-check-input" 
                        name="hole_${holeNumber}_shot_${shotNumber + 1}_out_of_bounds" 
                        id="hole_${holeNumber}_shot_${shotNumber + 1}_out_of_bounds" 
                        value="1"
                        onchange="addDummyShot(${holeNumber}, ${shotNumber + 1}, 'OOB', ${par})"
                    >
                    <label for="hole_${holeNumber}_shot_${shotNumber + 1}_out_of_bounds" class="form-check-label">Out of Bounds</label>
                </div>
                <div class="form-check form-check-inline">
                    <input 
                        type="checkbox" 
                        class="form-check-input" 
                        name="hole_${holeNumber}_shot_${shotNumber + 1}_hazard" 
                        id="hole_${holeNumber}_shot_${shotNumber + 1}_hazard" 
                        value="1"
                        onchange="addDummyShot(${holeNumber}, ${shotNumber + 1}, 'hazard', ${par})"
                    >
                    <label for="hole_${holeNumber}_shot_${shotNumber + 1}_hazard" class="form-check-label">Hazard/Unplayable</label>
                </div>
                <button 
                    type="button" 
                    class="btn btn-danger btn-sm remove-shot-btn" 
                    onclick="removeShot(${holeNumber}, ${shotNumber + 1})"
                >
                    Remove Shot
                </button>
            </div>
        `;

        // Insert the dummy shot and the new shot below the current shot
        const currentShotElement = document.getElementById(`hole_${holeNumber}_shot_${shotNumber}`);
        currentShotElement.insertAdjacentHTML("afterend", dummyShotHTML);
        document.getElementById(dummyShotId).insertAdjacentHTML("afterend", nextShotHTML);

        updateRemoveShotButtons(holeNumber);
    } 
    // If the checkbox is unchecked, remove both the dummy and the new shot
    else if (!penaltyCheckbox.checked) {
        if (existingDummyShot) existingDummyShot.remove();
        if (existingNextShot) existingNextShot.remove();
        updateRemoveShotButtons(holeNumber);
    }
}

/********************************************
 *    5) UPDATE DISTANCE LABEL
 ********************************************/
function updateDistanceLabel(holeNumber, shotNumber) {
    const lieSelect = document.getElementById(`hole_${holeNumber}_shot_${shotNumber}_lie`);
    if (!lieSelect) return;  // safety check

    const distanceLabel = document.querySelector(
        `label[for="hole_${holeNumber}_shot_${shotNumber}_distance"]`
    );
    if (!distanceLabel) return;  // safety check

    if (lieSelect.value === "Green") {
        distanceLabel.textContent = "Distance (feet):";
    } else {
        distanceLabel.textContent = "Distance (yards):";
    }
}

/********************************************
 *    6) GET NEXT SHOT NUMBER
 ********************************************/
function getNextShotNumber(holeNumber) {
    const shotsContainer = document.getElementById(`hole_${holeNumber}_shots`);
    const shotCards = shotsContainer.querySelectorAll(".shot-card");
    return shotCards.length + 1;
}

/********************************************
 *    7) UPDATE REMOVE-SHOT BUTTONS
 ********************************************/
// Hides the "Remove Shot" button for all shots except the last shot in each hole.
function updateRemoveShotButtons(holeNumber) {
    const shotsContainer = document.getElementById(`hole_${holeNumber}_shots`);
    const shotCards = shotsContainer.querySelectorAll(".shot-card");

    shotCards.forEach((card, index) => {
        // Grab the removeShot button on this card
        const removeBtn = card.querySelector(".remove-shot-btn");

        // Grab all form controls (inputs, selects, checkboxes, etc.)
        // excluding the remove-shot button if you want to handle it separately
        const formElements = card.querySelectorAll(`
            input[type="number"],
            input[type="checkbox"],
            select
        `);

        if (index === shotCards.length - 1) {
            // This is the last (newest) shot card
            // -> ENABLE all form controls
            formElements.forEach(el => el.disabled = false);

            // Show remove button
            if (removeBtn) {
                removeBtn.style.display = "inline-block";
                removeBtn.disabled = false;
            }
        } else {
            // This is NOT the last shot card
            // -> DISABLE all form controls
            formElements.forEach(el => el.disabled = true);

            // Hide remove button (or disable it)
            if (removeBtn) {
                removeBtn.style.display = "none";
                // Alternatively: removeBtn.disabled = true;
            }
        }
    });
}

function removeShot(holeNumber, shotNumber) {
    // 1) Identify the shot card to remove
    const shotElement = document.getElementById(`hole_${holeNumber}_shot_${shotNumber}`);
    if (!shotElement) return;

    // 2) Check for a preceding dummy shot card
    const shotsContainer = document.getElementById(`hole_${holeNumber}_shots`);
    const previousShotCard = shotElement.previousElementSibling;  // the DOM sibling above it
    if (previousShotCard && previousShotCard.id.startsWith(`hole_dummy_${holeNumber}_shot_`)) {
        // Example dummy ID: hole_dummy_1_shot_3_dummy_oob
        // We'll parse out the "3" (originalShotNumber) from the ID:
        const match = previousShotCard.id.match(
            new RegExp(`^hole_dummy_${holeNumber}_shot_(\\d+)_dummy_.*$`)
        );
        if (match) {
            const originalShotNumber = match[1];

            // 2a) Remove the dummy shot card
            previousShotCard.remove();

            // 2b) Uncheck penalty boxes in the original shot that triggered the dummy
            const originalShotCard = document.getElementById(
                `hole_${holeNumber}_shot_${originalShotNumber}`
            );
            if (originalShotCard) {
                const outOfBoundsCheckbox = originalShotCard.querySelector(
                    `#hole_${holeNumber}_shot_${originalShotNumber}_out_of_bounds`
                );
                const hazardCheckbox = originalShotCard.querySelector(
                    `#hole_${holeNumber}_shot_${originalShotNumber}_hazard`
                );

                if (outOfBoundsCheckbox) outOfBoundsCheckbox.checked = false;
                if (hazardCheckbox) hazardCheckbox.checked = false;
            }
        }
    }

    // 3) Remove the current shot card
    shotElement.remove();

    // 4) Re-check which shot is now last, show/hide remove buttons
    updateRemoveShotButtons(holeNumber);
}