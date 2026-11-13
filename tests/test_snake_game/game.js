// Game variables
const canvas = document.getElementById('game-canvas');
const ctx = canvas.getContext('2d');
const scoreElement = document.getElementById('score');

// Game settings
const gridSize = 20;
const tileCount = canvas.width / gridSize;

// Snake
let snake = [
    {x: 10, y: 10}
];
let velocityX = 0;
let velocityY = 0;

// Food
let foodX = 5;
let foodY = 5;

// Score
let score = 0;

// Game loop
function gameLoop() {
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Move snake
    const head = {x: snake[0].x + velocityX, y: snake[0].y + velocityY};
    snake.unshift(head);

    // Check collision with food
    if (head.x === foodX && head.y === foodY) {
        score++;
        scoreElement.textContent = `Score: ${score}`;
        generateFood();
    } else {
        snake.pop();
    }

    // Draw snake
    snake.forEach((segment, index) => {
        ctx.fillStyle = index === 0 ? '#0284c7' : '#1e40af';
        ctx.fillRect(segment.x * gridSize, segment.y * gridSize, gridSize - 2, gridSize - 2);
    });

    // Draw food
    ctx.fillStyle = '#ec4899';
    ctx.fillRect(foodX * gridSize, foodY * gridSize, gridSize - 2, gridSize - 2);

    // Check collision with walls
    if (head.x < 0 || head.x >= tileCount || head.y < 0 || head.y >= tileCount) {
        resetGame();
    }

    // Check collision with self
    for (let i = 1; i < snake.length; i++) {
        if (head.x === snake[i].x && head.y === snake[i].y) {
            resetGame();
        }
    }
}

// Generate food
function generateFood() {
    foodX = Math.floor(Math.random() * tileCount);
    foodY = Math.floor(Math.random() * tileCount);

    // Make sure food doesn't spawn on snake
    for (let segment of snake) {
        if (foodX === segment.x && foodY === segment.y) {
            generateFood();
            return;
        }
    }
}

// Reset game
function resetGame() {
    snake = [{x: 10, y: 10}];
    velocityX = 0;
    velocityY = 0;
    score = 0;
    scoreElement.textContent = `Score: ${score}`;
    generateFood();
}

// Keyboard controls
document.addEventListener('keydown', (e) => {
    switch(e.key) {
        case 'ArrowUp':
            if (velocityY !== 1) {
                velocityX = 0;
                velocityY = -1;
            }
            break;
        case 'ArrowDown':
            if (velocityY !== -1) {
                velocityX = 0;
                velocityY = 1;
            }
            break;
        case 'ArrowLeft':
            if (velocityX !== 1) {
                velocityX = -1;
                velocityY = 0;
            }
            break;
        case 'ArrowRight':
            if (velocityX !== -1) {
                velocityX = 1;
                velocityY = 0;
            }
            break;
    }
});

// Start game
generateFood();
setInterval(gameLoop, 100);