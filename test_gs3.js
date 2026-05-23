const { JSDOM } = require('jsdom');
const dom = new JSDOM(`
<!DOCTYPE html>
<html>
<body>
    <div class="grid-stack">
        <div class="grid-stack-item" gs-x="10" gs-w="30"></div>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/gridstack@11.1.1/dist/gridstack-all.js"></script>
    <script>
        let grid = GridStack.init({ column: 120 });
        window.gridClasses = document.querySelector('.grid-stack').className;
    </script>
</body>
</html>
`, { runScripts: "dangerously", resources: "usable" });

setTimeout(() => {
    console.log("Grid classes:", dom.window.gridClasses);
}, 2000);
