let canvas = document.getElementsById('canvas');
let isDraw = true;
let ctx = canvas.getContext('2d');
let points = [];

canvas.addEventListener('mousedown', setPosition);

document.getElementById('stream').addEventListener('load', prepareCanvas);

document.getElementById('draw').addEventListener('click', () => {
    isDraw = true;
    canvas.style.cursor = 'default';
});

document.getElementById('delete').addEventListener('click', () => {
    isDraw = false;
    canvas.style.cursor = 'no-drop';
});

function deleteSquare(e) {
    fetch("/slot",
        {
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            method: "DELETE",
            body: JSON.stringify({x: e.layerX / ctx.canvas.width, y: e.layerY / ctx.canvas.height})
        // }).then(function (res) { // Do nothing on OK
        }).catch(function (res) {
            console.log(res);
        }
    )
}

function setPosition(e) {
    if (!isDraw) {
        points = [];
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.restore();
        return deleteSquare(e);
    }

    let pos = {x: e.layerX, y: e.layerY};
    if (points.length > 0) {
        ctx.beginPath();
        ctx.lineWidth = 2;
        ctx.lineCap = 'round';
        ctx.strokeStyle = '#5A5AFF';
        ctx.moveTo(points.at(-1).x, points.at(-1).y); // From
        ctx.lineTo(pos.x, pos.y); // To
        ctx.stroke();
    }

    points.push(pos);
    if (points.length === 4) {
        let returnData = [];
        for (let element of points) {
            returnData.push({x: element.x / ctx.canvas.width, y: element.y / ctx.canvas.height});
        }
        fetch("/slot",
            {
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                },
                method: "POST",
                body: JSON.stringify(returnData)
            }).then(function (res) {
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                ctx.restore();
            }).catch(function (res) {
                console.log(res);
            }
        );

        points = [];
    }
}

function prepareCanvas() {
    ctx.canvas.height = document.getElementById('stream').clientHeight;
    ctx.canvas.width = document.getElementById('stream').clientWidth;
    canvas.style.position = "absolute";
    canvas.style.left = "7px";
}
