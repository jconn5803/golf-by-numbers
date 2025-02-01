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
  