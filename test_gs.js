const { JSDOM } = require('jsdom');
const dom = new JSDOM(`
<!DOCTYPE html>
<html>
<body>
    <div class="grid-stack">
        <div class="grid-stack-item" gs-x="10" gs-y="0" gs-w="30" gs-h="10"><div class="grid-stack-item-content">A</div></div>
        <div class="grid-stack-item" gs-x="50" gs-y="0" gs-w="40" gs-h="10"><div class="grid-stack-item-content">B</div></div>
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
        window.nodes = grid.engine.nodes.map(n => ({x: n.x, y: n.y, w: n.w, h: n.h}));
    </script>
</body>
</html>
`, { runScripts: "dangerously", resources: "usable" });

setTimeout(() => {
    console.log(dom.window.nodes);
}, 2000);
