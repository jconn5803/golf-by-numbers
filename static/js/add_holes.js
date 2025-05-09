// Update the table rows dynamically based on the number of holes selected
function updateHoleNumbers(numHoles) {
    const tableBody = document.getElementById('holes_table');
    tableBody.innerHTML = ''; // Clear existing rows
  
    for (let i = 1; i <= numHoles; i++) {
      const row = `
        <tr>
          <td>${i}</td>
          <td>
            <input 
              type="number" 
              name="distances" 
              class="form-control custom-form-input"
              required
            >
          </td>
          <td>
            <div class="btn-group custom-radio-group" role="group" aria-label="Par selection for hole ${i}">
              <input 
                type="radio"
                class="btn-check"
                name="par_${i}"
                id="par_${i}_3"
                value="3"
                autocomplete="off"
              >
              <label class="btn btn-outline-accent" for="par_${i}_3">3</label>
  
              <!-- Set par=4 as the default with "checked" -->
              <input 
                type="radio"
                class="btn-check"
                name="par_${i}"
                id="par_${i}_4"
                value="4"
                autocomplete="off"
                checked
              >
              <label class="btn btn-outline-accent" for="par_${i}_4">4</label>
              
              <input 
                type="radio"
                class="btn-check"
                name="par_${i}"
                id="par_${i}_5"
                value="5"
                autocomplete="off"
              >
              <label class="btn btn-outline-accent" for="par_${i}_5">5</label>
            </div>
          </td>
        </tr>
      `;
      tableBody.innerHTML += row;
    }
  }
  
  
  document.addEventListener('DOMContentLoaded', () => {
    // Default to 18 holes on page load
    updateHoleNumbers(18);
  
    // Listen for changes to the 9/18 radio buttons
    const holeRadios = document.querySelectorAll('input[name="num_holes"]');
    holeRadios.forEach(radio => {
      radio.addEventListener('change', function() {
        // Parse the numeric value (9 or 18)
        const numHoles = parseInt(this.value, 10);
        updateHoleNumbers(numHoles);
      });
    });
  });



  // ——————————————
// Intercept the “Save Holes” click
// ——————————————
document.addEventListener('DOMContentLoaded', () => {
  const holesForm = document.querySelector('form[action$="/add_holes"]');
  const modalEl  = document.getElementById('holesConfirmationModal');
  const modal    = new bootstrap.Modal(modalEl);

  holesForm.addEventListener('submit', e => {
    e.preventDefault();

    // 1) Number of holes (9 or 18)
    const numHoles = parseInt(
      document.querySelector('input[name="num_holes"]:checked').value, 10
    );

    // 2) Sum total distance
    let totalDistance = 0;
    document.querySelectorAll('#holes_table input[name="distances"]').forEach(input => {
      const v = parseInt(input.value, 10);
      if (!isNaN(v)) totalDistance += v;
    });

    // 3) Sum total par
    let totalPar = 0;
    for (let i = 1; i <= numHoles; i++) {
      const sel = document.querySelector(`input[name="par_${i}"]:checked`);
      if (sel) totalPar += parseInt(sel.value, 10);
    }

    // 4) Fill the modal fields
    document.getElementById('confirm-num-holes').textContent        = numHoles;
    document.getElementById('confirm-total-distance').textContent   = totalDistance;
    document.getElementById('confirm-total-par').textContent        = totalPar;

    // 5) Show the modal
    modal.show();
  });

  // When the user confirms in the modal…
  document.getElementById('confirm-holes-submit').addEventListener('click', () => {
    modal.hide();
    holesForm.submit();
  });
});
