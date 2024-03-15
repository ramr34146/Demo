// Call the getTheme function when the page loads
function getTheme() {
				fetch('/update-theme-preference/', {
					method: 'GET',
				})
				.then(response => response.json())
				.then(data => {
					if (data.theme === 'theme-light') {
						setTheme(data.theme);
						document.documentElement.setAttribute('class', data.theme);
						// toggleSwitch.checked = (data.theme === 'theme-light');
                        $('#slider').prop('checked', true);
					} else {
						setTheme(data.theme);
                        document.documentElement.setAttribute('class', data.theme);
						// toggleSwitch.checked = (data.theme === 'theme-dark');
                        $('#slider').prop('checked', false);
					}
				})
				.catch(error => {
					console.error('Error while updating theme preference:', error);
				});
			}
			window.addEventListener('load', getTheme);

// function to set a given theme/color-scheme
 function setTheme(themeName) {
    localStorage.setItem('theme', themeName);
    document.documentElement.className = themeName;
}

// function to toggle between light and dark theme
function toggleTheme() {
    var themeUrl = document.getElementById('slider').getAttribute('data-theme-url'); // Get the URL from the data attribute
    if (localStorage.getItem('theme') === 'theme-dark') {
        setTheme('theme-light', themeUrl);
        sendThemeToServer('theme-light', themeUrl);
    } else {
        setTheme('theme-dark', themeUrl);
        sendThemeToServer('theme-dark', themeUrl);
    }
}

// Immediately invoked function to set the theme on initial load
(function () {
    if (localStorage.getItem('theme') === 'theme-dark') {
        setTheme('theme-dark');
        document.getElementById('slider').checked = false;
    } else {
        setTheme('theme-light');
        document.getElementById('slider').checked = true;
    }
})();

function sendThemeToServer(themeName, url) {
    $.ajax({
        url: url,
        method: "POST",
        data: {
            mode: themeName,
        },
        success: function (data) {
        },
        error: function () {
        }
    });
}