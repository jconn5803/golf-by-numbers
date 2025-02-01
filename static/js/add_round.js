document.getElementById('course').addEventListener('change', function () {
    const courseID = this.value;

    // Fetch tees for the selected course
    fetch(`/get_tees/${courseID}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            const teeSelect = document.getElementById('tee');
            teeSelect.innerHTML = '<option value="" disabled selected>Choose a tee...</option>';
            data.forEach(tee => {
                const option = document.createElement('option');
                option.value = tee.teeID;
                option.textContent = tee.name;
                teeSelect.appendChild(option);
            });

            // Show the "Add Tee" button
            const addTeeButton = document.getElementById('add-tee-button');
            addTeeButton.style.display = 'inline-block';
            addTeeButton.href = `/add_tee/${courseID}`;
        })
        .catch(error => {
            console.error("Error fetching tees:", error);
        });
});
