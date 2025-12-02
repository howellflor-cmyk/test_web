// Toggle new-household fields and initialize state

document.addEventListener('DOMContentLoaded', function () {
    var sel = document.getElementById('household_select');
    var newFields = document.getElementById('new_household_fields');

    function toggleNewHousehold(val) {
        if (!newFields) return;
        if (val === 'new') {
            newFields.style.display = 'block';
            newFields.setAttribute('aria-hidden', 'false');
        } else {
            newFields.style.display = 'none';
            newFields.setAttribute('aria-hidden', 'true');
        }
    }

    if (sel) {
        // initialize based on current value (useful after validation or browser restore)
        toggleNewHousehold(sel.value);

        // attach change listener
        sel.addEventListener('change', function (e) {
            toggleNewHousehold(e.target.value);
        });
    }
});