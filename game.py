import streamlit as st

st.set_page_config(page_title="Gà Con Qua Đường - Crossy Road Clone", layout="centered")

st.markdown("<h1 style='text-align: center;'>🐔 Gà Con Qua Đường 🚧</h1>", unsafe_allow_html=True)
st.write("Sử dụng các phím mũi tên **Lên / Xuống / Trái / Phải** (hoặc **W, A, S, D**) trên bàn phím để điều khiển chú gà băng qua đường an toàn và tránh các chướng ngại vật khối!")

# Nhúng mã nguồn Game (HTML5 Canvas + JS) trực tiếp vào Streamlit
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

        // Âm thanh giả lập bằng Web Audio API (Không lo lỗi thiếu tệp âm thanh)
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

        // Nhạc nền đơn giản lặp lại tuần hoàn
        let isMusicPlaying = false;
        function startBackgroundMusic() {
            if (isMusicPlaying) return;
            isMusicPlaying = true;
            setInterval(() => {
                let now = audioCtx.currentTime;
                // Chuỗi nốt nhạc lặp lại vui tai
                playNote(261.63, now, 0.2); // C4
                playNote(329.63, now + 0.25, 0.2); // E4
                playNote(392.00, now + 0.5, 0.2); // G4
                playNote(329.63, now + 0.75, 0.2); // E4
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

        // Khởi tạo các Thực thể (Vẽ bằng hình khối 2.5D đổ bóng)
        const grid = 50;
        let score = 0;

        let player = {
            x: 5 * grid,
            y: 11 * grid,
            w: 35,
            h: 35,
            color: '#ffffff' // Gà màu trắng chân đỏ mào đỏ
        };

        // Danh sách các làn đường và xe cộ (Chướng ngại vật)
        let lanes = [
            { y: 1 * grid, speed: -2, color: '#444', obstacles: [{x: 100, w: 70}, {x: 350, w: 70}], type: 'car', carColor: '#3498db' },
            { y: 2 * grid, speed: 3, color: '#555', obstacles: [{x: 50, w: 90}, {x: 280, w: 90}], type: 'truck', carColor: '#e67e22' },
            { y: 4 * grid, speed: -1.5, color: '#333', obstacles: [{x: 0, w: 60}, {x: 200, w: 60}, {x: 400, w: 60}], type: 'car', carColor: '#9b59b6' },
            { y: 6 * grid, speed: 2.5, color: '#2980b9', obstacles: [{x: 20, w: 100}, {x: 250, w: 100}], type: 'log', carColor: '#8e44ad' }, // Sông cây gỗ
            { y: 7 * grid, speed: -2, color: '#2980b9', obstacles: [{x: 80, w: 120}, {x: 320, w: 120}], type: 'log', carColor: '#e74c3c' },
            { y: 9 * grid, speed: 1.8, color: '#444', obstacles: [{x: 150, w: 70}, {x: 400, w: 70}], type: 'car', carColor: '#f1c40f' }
        ];

        // Môi trường cỏ và cây cối tĩnh hình khối
        let trees = [
            {x: 0, y: 10*grid}, {x: 2*grid, y: 10*grid}, {x: 7*grid, y: 10*grid},
            {x: 1*grid, y: 5*grid}, {x: 6*grid, y: 5*grid},
            {x: 3*grid, y: 0}, {x: 8*grid, y: 0}
        ];

        // Vẽ Khối Hộp có hiệu ứng 3D giả lập (Đổ 2 màu sáng tối)
        function draw3DBlock(x, y, w, h, baseColor, shadowColor, depth=6) {
            // Phần bóng / Mặt bên
            ctx.fillStyle = shadowColor;
            ctx.fillRect(x, y + depth, w, h);
            // Phần mặt trên sáng hơn
            ctx.fillStyle = baseColor;
            ctx.fillRect(x, y, w, h);
        }

        function drawPlayer() {
            let padX = (grid - player.w) / 2;
            let padY = (grid - player.h) / 2;
            let px = player.x + padX;
            let py = player.y + padY;

            // Thân gà (Khối trắng)
            draw3DBlock(px, py, player.w, player.h, '#FFFFFF', '#DCDCDC', 5);
            // Mào gà (Khối đỏ nhỏ trên đầu)
            ctx.fillStyle = '#E74C3C';
            ctx.fillRect(px + 12, py - 4, 10, 6);
            // Mỏ vàng
            ctx.fillStyle = '#F1C40F';
            ctx.fillRect(px + player.w - 4, py + 12, 6, 6);
            // Mắt đen
            ctx.fillStyle = '#000000';
            ctx.fillRect(px + player.w - 10, py + 6, 4, 4);
        }

        function drawTrees() {
            trees.forEach(t => {
                // Thân cây gỗ nâu
                ctx.fillStyle = '#8B4513';
                ctx.fillRect(t.x + 20, t.y + 30, 10, 20);
                // Lá cây khối vuông xanh lá
                draw3DBlock(t.x + 10, t.y + 5, 30, 30, '#2ECC71', '#27AE60', 5);
            });
        }

        function update() {
            // Cập nhật vị trí chướng ngại vật
            lanes.forEach(lane => {
                lane.obstacles.forEach(obs => {
                    obs.x += lane.speed;
                    // Lặp lại màn hình khi đi ra ngoài cạnh biên
                    if (lane.speed > 0 && obs.x > canvas.width) obs.x = -obs.w;
                    if (lane.speed < 0 && obs.x < -obs.w) obs.x = canvas.width;

                    // Kiểm tra va chạm hộp (AABB Collision)
                    let padX = (grid - player.w) / 2;
                    let padY = (grid - player.h) / 2;
                    let px = player.x + padX;
                    let py = player.y + padY;

                    if (py < lane.y + grid && py + player.h > lane.y) {
                        if (px < obs.x + obs.w && px + player.w > obs.x) {
                            // Xử lý va chạm
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

            // Vẽ nền cho các làn cỏ tĩnh
            ctx.fillStyle = '#27ae60'; // Vỉa hè cỏ đậm
            ctx.fillRect(0, 11*grid, canvas.width, grid);
            ctx.fillRect(0, 10*grid, canvas.width, grid);
            ctx.fillRect(0, 8*grid, canvas.width, grid);
            ctx.fillRect(0, 5*grid, canvas.width, grid);
            ctx.fillRect(0, 3*grid, canvas.width, grid);
            ctx.fillRect(0, 0, canvas.width, grid);

            // Vẽ làn đường xe chạy hoặc sông nước
            lanes.forEach(lane => {
                ctx.fillStyle = lane.color;
                ctx.fillRect(0, lane.y, canvas.width, grid);

                // Vẽ vạch kẻ đường đứt đoạn nếu là đường nhựa
                if(lane.color === '#444' || lane.color === '#555'){
                    ctx.strokeStyle = '#fff';
                    ctx.setLineDash([15, 15]);
                    ctx.beginPath();
                    ctx.moveTo(0, lane.y + grid/2);
                    ctx.lineTo(canvas.width, lane.y + grid/2);
                    ctx.stroke();
                }

                // Vẽ các khối xe cộ ô tô / xe tải / khúc gỗ
                lane.obstacles.forEach(obs => {
                    if (lane.color === '#2980b9') { // Khúc gỗ trôi sông
                        draw3DBlock(obs.x, lane.y + 5, obs.w, grid - 10, '#D35400', '#A04000', 6);
                    } else { // Ô tô khối hộp kiểu Voxel
                        draw3DBlock(obs.x, lane.y + 6, obs.w, grid - 12, lane.carColor, '#2c3e50', 6);
                        // Kính xe vuông phía trước
