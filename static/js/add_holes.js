// Update the table rows dynamically based on the number of holes selected
function updateHoleNumbers(numHoles) {
    const tableBody = document.getElementById('holes_table');
    tableBody.innerHTML = '';  // Clear existing rows

    for (let i = 1; i <= numHoles; i++) {
        const row = `
            <tr>
                <td>${i}</td>
                <td><input type="number" name="distances" class="form-control" required></td>
                <td>
                    <select name="pars" class="form-select" required>
                        <option value="3">Par 3</option>
                        <option value="4">Par 4</option>
                        <option value="5">Par 5</option>
                    </select>
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