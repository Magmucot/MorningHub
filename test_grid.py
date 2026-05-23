from flask import Flask
app = Flask(__name__)
@app.route("/")
def index():
    return """
    <html>
    <head>
        <script src="https://cdn.jsdelivr.net/npm/gridstack@11.1.1/dist/gridstack-all.js"></script>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/gridstack@11.1.1/dist/gridstack.min.css"/>
    </head>
    <body>
        <div class="grid-stack" data-free="true">
            <div class="grid-stack-item" gs-x="10" gs-y="0" gs-w="30" gs-h="10"><div class="grid-stack-item-content" style="background: red;">A</div></div>
            <div class="grid-stack-item" gs-x="50" gs-y="0" gs-w="40" gs-h="10"><div class="grid-stack-item-content" style="background: blue;">B</div></div>
        </div>
        <script>
            let grid = GridStack.init({
                column: 120,
                cellHeight: 10,
                margin: 0,
                disableOneColumnMode: true,
                float: true
            });
            console.log("Grid nodes:", grid.engine.nodes.map(n => ({x: n.x, y: n.y, w: n.w, h: n.h})));
            document.body.innerHTML += "<div id='out'>" + JSON.stringify(grid.engine.nodes.map(n => ({x: n.x, y: n.y, w: n.w, h: n.h}))) + "</div>";
        </script>
    </body>
    </html>
    """
if __name__ == "__main__":
    app.run(port=5005)
