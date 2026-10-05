import streamlit as st

st.set_page_config(page_title="Gà Con Qua Đường - Crossy Road Clone", layout="centered")

st.markdown("<h1 style='text-align: center;'>🐔 Gà Con Qua Đường 🚧</h1>", unsafe_allow_html=True)
st.write("Sử dụng các phím mũi tên **Lên / Xuống / Trái / Phải** (hoặc **W, A, S, D**) trên bàn phím để điều khiển chú gà băng qua đường an toàn và tránh các chướng ngại vật khối!")

# Bắt đầu chuỗi mã nguồn game
game_code = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body {
            margin: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            background-color: #f0f0f0;
            font-family: Arial, sans-serif;
            overflow: hidden;
        }
        canvas {
            border: 4px solid #333;
            background-color: #87ee87;
            box-shadow: 0px 10px 20px rgba(0,0,0,0.3);
        }
        #ui {
            position: absolute;
            top: 20px;
            font-size: 24px;
            font-weight: bold;
            color: #333;
            text-shadow: 1px 1px 2px white;
        }
    </style>
</head>
<body>
    <div id="ui">Điểm: <span id="score">0</span></div>
    <canvas id="gameCanvas" width="500" height="600"></canvas>

    <script>
        const canvas = document.getElementById("gameCanvas");
        const ctx = canvas.getContext("2d");
        const scoreEl = document.getElementById("score");

        // Âm thanh giả lập bằng Web Audio API
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        
        function playJumpSound() {
            let osc = audioCtx.createOscillator();
            let gain = audioCtx.createGain();
            osc.connect(gain);
            gain.connect(audioCtx.destination);
            osc.type = 'sine';
            osc.frequency.setValueAtTime(150, audioCtx.currentTime);
            osc.frequency.exponentialRampToValueAtTime(400, audioCtx.currentTime + 0.15);
            gain.gain.setValueAtTime(0.3, audioCtx.currentTime);
            gain.gain.linearRampToValueAtTime(0.01, audioCtx.currentTime + 0.15);
            osc.start();
            osc.stop(audioCtx.currentTime + 0.15);
        }

        function playCrashSound() {
            let osc = audioCtx.createOscillator();
            let gain = audioCtx.createGain();
            osc.connect(gain);
            gain.connect(audioCtx.destination);
            osc.type = 'sawtooth';
            osc.frequency.setValueAtTime(300, audioCtx.currentTime);
            osc.frequency.linearRampToValueAtTime(60, audioCtx.currentTime + 0.4);
            gain.gain.setValueAtTime(0.5, audioCtx.currentTime);
            gain.gain.linearRampToValueAtTime(0.01, audioCtx.currentTime + 0.4);
            osc.start();
            osc.stop(audioCtx.currentTime + 0.4);
        }

        let isMusicPlaying = false;
        function startBackgroundMusic() {
            if (isMusicPlaying) return;
            isMusicPlaying = true;
            setInterval(() => {
                let now = audioCtx.currentTime;
                playNote(261.63, now, 0.2); 
                playNote(329.63, now + 0.25, 0.2); 
                playNote(392.00, now + 0.5, 0.2); 
                playNote(329.63, now + 0.75, 0.2); 
            }, 1000);
        }

        function playNote(freq, startTime, duration) {
            let osc = audioCtx.createOscillator();
            let gain = audioCtx.createGain();
            osc.connect(gain);
            gain.connect(audioCtx.destination);
            osc.type = 'triangle';
            osc.frequency.setValueAtTime(freq, startTime);
            gain.gain.setValueAtTime(0.05, startTime);
            gain.gain.linearRampToValueAtTime(0, startTime + duration);
            osc.start(startTime);
            osc.stop(startTime + duration);
        }

        const grid = 50;
        let score = 0;

        let player = {
            x: 5 * grid,
            y: 11 * grid,
            w: 35,
            h: 35,
            color: '#ffffff'
        };

        let lanes = [
            { y: 1 * grid, speed: -2, color: '#444', obstacles: [{x: 100, w: 70}, {x: 350, w: 70}], type: 'car', carColor: '#3498db' },
            { y: 2 * grid, speed: 3, color: '#555', obstacles: [{x: 50, w: 90}, {x: 280, w: 90}], type: 'truck', carColor: '#e67e22' },
            { y: 4 * grid, speed: -1.5, color: '#333', obstacles: [{x: 0, w: 60}, {x: 200, w: 60}, {x: 400, w: 60}], type: 'car', carColor: '#9b59b6' },
            { y: 6 * grid, speed: 2.5, color: '#2980b9', obstacles: [{x: 20, w: 100}, {x: 250, w: 100}], type: 'log', carColor: '#8e44ad' },
            { y: 7 * grid, speed: -2, color: '#2980b9', obstacles: [{x: 80, w: 120}, {x: 320, w: 120}], type: 'log', carColor: '#e74c3c' },
            { y: 9 * grid, speed: 1.8, color: '#444', obstacles: [{x: 150, w: 70}, {x: 400, w: 70}], type: 'car', carColor: '#f1c40f' }
        ];

        let trees = [
            {x: 0, y: 10*grid}, {x: 2*grid, y: 10*grid}, {x: 7*grid, y: 10*grid},
            {x: 1*grid, y: 5*grid}, {x: 6*grid, y: 5*grid},
            {x: 3*grid, y: 0}, {x: 8*grid, y: 0}
        ];

        function draw3DBlock(x, y, w, h, baseColor, shadowColor, depth=6) {
            ctx.fillStyle = shadowColor;
            ctx.fillRect(x, y + depth, w, h);
            ctx.fillStyle = baseColor;
            ctx.fillRect(x, y, w, h);
        }

        function drawPlayer() {
            let padX = (grid - player.w) / 2;
            let padY = (grid - player.h) / 2;
            let px = player.x + padX;
            let py = player.y + padY;

            draw3DBlock(px, py, player.w, player.h, '#FFFFFF', '#DCDCDC', 5);
            ctx.fillStyle = '#E74C3C';
            ctx.fillRect(px + 12, py - 4, 10, 6);
            ctx.fillStyle = '#F1C40F';
            ctx.fillRect(px + player.w - 4, py + 12, 6, 6);
            ctx.fillStyle = '#000000';
            ctx.fillRect(px + player.w - 10, py + 6, 4, 4);
        }

        function drawTrees() {
            trees.forEach(t => {
                ctx.fillStyle = '#8B4513';
                ctx.fillRect(t.x + 20, t.y + 30, 10, 20);
                draw3DBlock(t.x + 10, t.y + 5, 30, 30, '#2ECC71', '#27AE60', 5);
            });
        }

        function update() {
            lanes.forEach(lane => {
                lane.obstacles.forEach(obs => {
                    obs.x += lane.speed;
                    if (lane.speed > 0 && obs.x > canvas.width) obs.x = -obs.w;
                    if (lane.speed < 0 && obs.x < -obs.w) obs.x = canvas.width;

                    let padX = (grid - player.w) / 2;
                    let padY = (grid - player.h) / 2;
                    let px = player.x + padX;
                    let py = player.y + padY;

                    if (py < lane.y + grid && py + player.h > lane.y) {
                        if (px < obs.x + obs.w && px + player.w > obs.x) {
                            playCrashSound();
                            alert("Bùm! Chú gà đã va chạm chướng ngại vật. Điểm của bạn: " + score);
                            resetGame();
                        }
                    }
                });
            });
        }

        function resetGame() {
            player.x = 5 * grid;
            player.y = 11 * grid;
            score = 0;
            scoreEl.innerText = score;
        }

        function render() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            ctx.fillStyle = '#27ae60';
            ctx.fillRect(0, 11*grid, canvas.width, grid);
            ctx.fillRect(0, 10*grid, canvas.width, grid);
            ctx.fillRect(0, 8*grid, canvas.width, grid);
            ctx.fillRect(0, 5*grid, canvas.width, grid);
            ctx.fillRect(0, 3*grid, canvas.width, grid);
            ctx.fillRect(0, 0, canvas.width, grid);

            lanes.forEach(lane => {
                ctx.fillStyle = lane.color;
                ctx.fillRect(0, lane.y, canvas.width, grid);

                if(lane.color === '#444' || lane.color === '#555'){
                    ctx.strokeStyle = '#fff';
                    ctx.beginPath();
                    ctx.moveTo(0, lane.y + grid/2);
                    ctx.lineTo(canvas.width, lane.y + grid/2);
                    ctx.stroke();
                }

                lane.obstacles.forEach(obs => {
                    if (lane.color === '#2980b9') {
                        draw3DBlock(obs.x, lane.y + 5, obs.w, grid - 10, '#D35400', '#A04000', 6);
                    } else {
                        draw3DBlock(obs.x, lane.y + 6, obs.w, grid - 12, lane.carColor, '#2c3e50', 6);
                        ctx.fillStyle = '#E0F7FA';
                        if(lane.speed > 0) {
                            ctx.fillRect(obs.x + obs.w - 15, lane.y + 10, 10, grid - 20);
                        } else {
                            ctx.fillRect(obs.x + 5, lane.y + 10, 10, grid - 20);
                        }
                    }
                });
            });

            drawTrees();
            drawPlayer();
        }

        function gameLoop() {
            update();
            render();
            requestAnimationFrame(gameLoop);
        }

        window.addEventListener("keydown", e => {
            if (audioCtx.state === 'suspended') {
                audioCtx.resume();
            }
            startBackgroundMusic();

            let oldY = player.y;
            switch(e.key.toLowerCase()) {
                case "arrowup":
                case "w":
                    player.y -= grid;
                    playJumpSound();
                    break;
                case "arrowdown":
                case "s":
                    if (player.y + grid < canvas.height) player.y += grid;
                    playJumpSound();
                    break;
                case "arrowleft":
                case "a":
                    if (player.x - grid >= 0) player.x -= grid;
                    playJumpSound();
