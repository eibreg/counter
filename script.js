document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const counterValue = document.getElementById('counter-value');
    const lastKeyElement = document.getElementById('last-key');
    const totalPressesElement = document.getElementById('total-presses');
    const resetBtn = document.getElementById('reset-btn');
    const autoClickerBtn = document.getElementById('auto-clicker');
    const soundToggleBtn = document.getElementById('sound-toggle');
    const pressRateElement = document.getElementById('press-rate');
    const sessionTimeElement = document.getElementById('session-time');
    const todayCountElement = document.getElementById('today-count');
    const clickSound = document.getElementById('click-sound');
    
    // Counter state
    let counter = 0;
    let lastKey = 'None';
    let totalPresses = 0;
    let soundEnabled = true;
    let autoClickerInterval = null;
    let sessionStartTime = Date.now();
    let pressTimestamps = [];
    
    // Load data from localStorage
    function loadFromStorage() {
        const savedCounter = localStorage.getItem('keyboardCounter');
        const savedTotal = localStorage.getItem('totalPresses');
        const savedToday = localStorage.getItem('todayCount');
        const savedDate = localStorage.getItem('lastVisitDate');
        
        const today = new Date().toDateString();
        
        if (savedCounter !== null) {
            counter = parseInt(savedCounter);
            updateCounterDisplay();
        }
        
        if (savedTotal !== null) {
            totalPresses = parseInt(savedTotal);
            updateTotalPresses();
        }
        
        // Reset today's count if it's a new day
        if (savedDate === today && savedToday !== null) {
            todayCountElement.textContent = savedToday;
        } else {
            localStorage.setItem('todayCount', '0');
            localStorage.setItem('lastVisitDate', today);
            todayCountElement.textContent = '0';
        }
    }
    
    // Save data to localStorage
    function saveToStorage() {
        localStorage.setItem('keyboardCounter', counter.toString());
        localStorage.setItem('totalPresses', totalPresses.toString());
        
        const today = new Date().toDateString();
        const todayCount = parseInt(todayCountElement.textContent);
        localStorage.setItem('todayCount', todayCount.toString());
        localStorage.setItem('lastVisitDate', today);
    }
    
    // Update counter display with animation
    function updateCounterDisplay() {
        counterValue.textContent = counter;
        counterValue.classList.add('pulse');
        
        // Remove animation class after animation completes
        setTimeout(() => {
            counterValue.classList.remove('pulse');
        }, 300);
    }
    
    // Update last key display
    function updateLastKey(key) {
        lastKey = key;
        lastKeyElement.textContent = key;
        
        // Add a temporary highlight
        lastKeyElement.style.color = '#e74c3c';
        setTimeout(() => {
            lastKeyElement.style.color = '';
        }, 300);
    }
    
    // Update total presses
    function updateTotalPresses() {
        totalPressesElement.textContent = totalPresses;
    }
    
    // Update today's count
    function updateTodayCount() {
        const todayCount = parseInt(todayCountElement.textContent) + 1;
        todayCountElement.textContent = todayCount;
    }
    
    // Update press rate
    function updatePressRate() {
        const now = Date.now();
        const oneMinuteAgo = now - 60000;
        
        // Filter presses from the last minute
        const recentPresses = pressTimestamps.filter(time => time > oneMinuteAgo);
        const rate = recentPresses.length;
        
        pressRateElement.textContent = `${rate}/min`;
    }
    
    // Update session time
    function updateSessionTime() {
        const elapsedSeconds = Math.floor((Date.now() - sessionStartTime) / 1000);
        const minutes = Math.floor(elapsedSeconds / 60);
        const seconds = elapsedSeconds % 60;
        
        sessionTimeElement.textContent = `${minutes > 0 ? `${minutes}m ` : ''}${seconds}s`;
    }
    
    // Increment counter
    function incrementCounter(key) {
        counter++;
        totalPresses++;
        pressTimestamps.push(Date.now());
        
        updateCounterDisplay();
        updateLastKey(key);
        updateTotalPresses();
        updateTodayCount();
        updatePressRate();
        
        // Play sound if enabled
        if (soundEnabled) {
            clickSound.currentTime = 0;
            clickSound.play().catch(e => console.log("Audio play failed:", e));
        }
        
        saveToStorage();
    }
    
    // Reset counter
    function resetCounter() {
        counter = 0;
        updateCounterDisplay();
        updateLastKey('None');
        saveToStorage();
        
        // Add confirmation effect
        resetBtn.innerHTML = '<i class="fas fa-check"></i> Reset!';
        setTimeout(() => {
            resetBtn.innerHTML = '<i class="fas fa-redo"></i> Reset Counter';
        }, 1000);
    }
    
    // Toggle auto-clicker
    function toggleAutoClicker() {
        if (autoClickerInterval) {
            clearInterval(autoClickerInterval);
            autoClickerInterval = null;
            autoClickerBtn.innerHTML = '<i class="fas fa-robot"></i> Auto-click (Press "A")';
        } else {
            autoClickerInterval = setInterval(() => {
                incrementCounter('Auto');
            }, 100);
            autoClickerBtn.innerHTML = '<i class="fas fa-stop"></i> Stop Auto-click';
        }
    }
    
    // Toggle sound
    function toggleSound() {
        soundEnabled = !soundEnabled;
        if (soundEnabled) {
            soundToggleBtn.innerHTML = '<i class="fas fa-volume-up"></i> Sound On';
        } else {
            soundToggleBtn.innerHTML = '<i class="fas fa-volume-mute"></i> Sound Off';
        }
    }
    
    // Initialize the application
    function init() {
        loadFromStorage();
        
        // Add event listeners
        document.addEventListener('keydown', function(event) {
            // Prevent auto-clicker from interfering with key detection
            if (autoClickerInterval && event.key === 'a') {
                return;
            }
            
            // Don't count modifier keys alone
            if (['Shift', 'Control', 'Alt', 'Meta', 'CapsLock', 'Tab'].includes(event.key)) {
                return;
            }
            
            // Increment counter with the pressed key
            incrementCounter(event.key);
        });
        
        resetBtn.addEventListener('click', resetCounter);
        
        autoClickerBtn.addEventListener('click', toggleAutoClicker);
        
        soundToggleBtn.addEventListener('click', toggleSound);
        
        // Also allow starting/stopping auto-clicker with 'a' key
        document.addEventListener('keydown', function(event) {
            if (event.key === 'a' || event.key === 'A') {
                if (!autoClickerInterval) {
                    toggleAutoClicker();
                }
            }
        });
        
        // Update session time every second
        setInterval(updateSessionTime, 1000);
        
        // Update press rate every 5 seconds
        setInterval(updatePressRate, 5000);
        
        // Initial updates
        updateSessionTime();
        updatePressRate();
        
        // Display a welcome message
        console.log('Keyboard Counter initialized. Press any key to start counting!');
    }
    
    // Start the application
    init();
});
