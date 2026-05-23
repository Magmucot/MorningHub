const { JSDOM } = require('jsdom');
const dom = new JSDOM(`
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/gridstack@11.1.1/dist/gridstack.min.css"/>
</head>
<body>
    <div class="grid-stack">
        <div class="grid-stack-item" gs-x="10" gs-y="0" gs-w="30" gs-h="10"><div class="grid-stack-item-content">A</div></div>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/gridstack@11.1.1/dist/gridstack-all.js"></script>
    <script>
        let grid = GridStack.init({
            column: 120,
            cellHeight: 10,
            margin: 0,
            disableOneColumnMode: true,
            float: true
        });
        window.styles = document.querySelectorAll('style').length;
        window.styleContent = document.querySelectorAll('style')[0] ? document.querySelectorAll('style')[0].innerHTML.substring(0, 200) : 'none';
        window.itemStyles = document.querySelector('.grid-stack-item').getAttribute('style');
    </script>
</body>
</html>
`, { runScripts: "dangerously", resources: "usable" });

setTimeout(() => {
    console.log("Styles injected:", dom.window.styles);
    console.log("Style content:", dom.window.styleContent);
    console.log("Item styles:", dom.window.itemStyles);
}, 2000);
