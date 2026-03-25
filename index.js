#!/usr/bin/env node
/**
 * Node.js wrapper to run Python Telegram bot.
 * Created to prevent bothost.ru from directly executing webapp.js as Node.js.
 */

const { spawn, spawnSync } = require('child_process');
const path = require('path');

// Try to ensure Python 3 is available
function ensurePython() {
  try {
    spawnSync('python3', ['--version'], { stdio: 'pipe', timeout: 5000 });
    return true;
  } catch (e) {
    // Python not found, try to install
    console.log('Python3 not found. Attempting to install...');

    try {
      // Try apt-get (Debian/Ubuntu)
      console.log('Trying apt-get...');
      spawnSync('apt-get', ['update'], { stdio: 'inherit', timeout: 60000 });
      spawnSync('apt-get', ['install', '-y', 'python3', 'python3-pip'], { stdio: 'inherit', timeout: 120000 });
      console.log('✓ Python3 installed via apt-get');
      return true;
    } catch (aptError) {
      try {
        // Try apk (Alpine)
        console.log('apt-get failed. Trying apk...');
        spawnSync('apk', ['add', '--no-cache', 'python3', 'py3-pip'], { stdio: 'inherit', timeout: 60000 });
        console.log('✓ Python3 installed via apk');
        return true;
      } catch (apkError) {
        console.error('✗ Could not install Python3. Neither apt-get nor apk available.');
        return false;
      }
    }
  }
}

if (!ensurePython()) {
  console.error('\n❌ Python 3 is required but not available and could not be installed.');
  console.error('Please configure bothost.ru to use the custom Python Dockerfile.');
  process.exit(1);
}

// Now spawn the Python bot
const pythonProcess = spawn('python3', [path.join(__dirname, 'bot.py')], {
  stdio: 'inherit',
  cwd: __dirname,
  shell: false
});

pythonProcess.on('error', (err) => {
  console.error('Failed to start Python bot:', err.message);
  process.exit(1);
});

pythonProcess.on('exit', (code) => {
  process.exit(code || 0);
});

// Handle termination signals
process.on('SIGINT', () => {
  pythonProcess.kill('SIGINT');
});

process.on('SIGTERM', () => {
  pythonProcess.kill('SIGTERM');
});
