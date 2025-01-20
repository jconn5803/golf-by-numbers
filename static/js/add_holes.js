// Update the table rows dynamically based on the number of holes selected
function updateHoleNumbers(numHoles) {
    const tableBody = document.getElementById('holes_table');
    tableBody.innerHTML = '';  // Clear existing rows

    for (let i = 1; i <= numHoles; i++) {
        const row = `
            <tr>
                <tr>
                <td>${i}</td>
                <td><input type="number" name="distances" class="form-control" required></td>
                <td>
                    <div class="btn-group" role="group" aria-label="Par selection for hole ${i}">
                        <input type="radio" class="btn-check" name="par_${i}" id="par_${i}_3" value="3" autocomplete="off" checked>
                        <label class="btn btn-outline-primary" for="par_${i}_3">3</label>
                        
                        <input type="radio" class="btn-check" name="par_${i}" id="par_${i}_4" value="4" autocomplete="off">
                        <label class="btn btn-outline-primary" for="par_${i}_4">4</label>
                        
                        <input type="radio" class="btn-check" name="par_${i}" id="par_${i}_5" value="5" autocomplete="off">
                        <label class="btn btn-outline-primary" for="par_${i}_5">5</label>
                    </div>
                </td>
            </tr>
        `;
        tableBody.innerHTML += row;
    }
}

// Initialize the table with 18 holes
document.addEventListener('DOMContentLoaded', () => {
    updateHoleNumbers(18);
});