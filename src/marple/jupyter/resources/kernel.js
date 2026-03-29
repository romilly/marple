// Language bar injection for classic Jupyter Notebook
// Uses Adám Brudzewsky's lb.js for live backtick-to-glyph translation
define(['base/js/namespace'], function(Jupyter) {
    return {
        onload: function() {
            var script = document.createElement('script');
            script.src = 'https://abrudz.github.io/lb/lb.js';
            document.body.appendChild(script);
        }
    };
});
