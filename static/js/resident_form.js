// Age auto-calculation script for add_resident.html and edit_resident.html

document.addEventListener('DOMContentLoaded', function() {
    const dobInput = document.getElementById('date_of_birth');
    const ageInput = document.getElementById('age');
    
    if (dobInput && ageInput) {
        // Calculate age when date of birth changes
        dobInput.addEventListener('change', function() {
            calculateAge();
        });
        
        // Also calculate on input (for better UX)
        dobInput.addEventListener('input', function() {
            calculateAge();
        });
        
        function calculateAge() {
            const dobValue = dobInput.value;
            
            if (!dobValue) {
                return; // Don't calculate if no date selected
            }
            
            const dob = new Date(dobValue);
            const today = new Date();
            
            // Calculate age
            let age = today.getFullYear() - dob.getFullYear();
            const monthDiff = today.getMonth() - dob.getMonth();
            
            // Adjust age if birthday hasn't occurred this year
            if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < dob.getDate())) {
                age--;
            }
            
            // Validate age is reasonable
            if (age >= 0 && age <= 150) {
                ageInput.value = age;
            } else if (age < 0) {
                alert('Date of birth cannot be in the future');
                dobInput.value = '';
                ageInput.value = '';
            }
        }
        
        // Calculate age on page load if date is already filled (for edit page)
        if (dobInput.value) {
            calculateAge();
        }
    }
});

// Household toggle function (already in your code)
function toggleNewHousehold(val) {
    var el = document.getElementById('new_household_fields');
    if (val === 'new') {
        el.style.display = 'block';
    } else {
        el.style.display = 'none';
    }
}