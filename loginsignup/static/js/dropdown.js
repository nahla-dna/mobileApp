document.addEventListener('DOMContentLoaded', function() {
    const dropdown = document.querySelector('.dropdown');
    const userIcon = dropdown ? dropdown.querySelector('.user-icon') : null;
    const dropdownMenu = dropdown ? dropdown.querySelector('.dropdown-menu') : null;
    
    if (userIcon && dropdownMenu) {
        // Toggle dropdown when clicking the user icon
        userIcon.addEventListener('click', function(e) {
            e.stopPropagation();
            dropdownMenu.classList.toggle('show');
        });
        
        // Close dropdown when clicking outside
        document.addEventListener('click', function(e) {
            if (!dropdown.contains(e.target)) {
                dropdownMenu.classList.remove('show');
            }
        });
        
        // Prevent dropdown from closing when clicking inside it
        dropdownMenu.addEventListener('click', function(e) {
            e.stopPropagation();
        });
    }
});