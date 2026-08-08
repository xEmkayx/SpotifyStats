window.dash_clientside = Object.assign({}, window.dash_clientside, {
    theme: {
        detect: function(pathname) {
            const isDark = window.matchMedia &&
                window.matchMedia('(prefers-color-scheme: dark)').matches;
            return isDark ? 'dark' : 'light';
        }
    }
});