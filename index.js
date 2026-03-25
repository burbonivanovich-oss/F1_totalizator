#!/usr/bin/env node
/**
 * Node.js wrapper to run Python Telegram bot for bothost.ru
 *
 * bothost.ru auto-detects JavaScript files and runs Node.js by default.
 * This wrapper intercepts the Node.js startup and spawns the Python bot instead.
 */

const { spawn, spawnSync } = require('child_process');
const path = require('path');
const fs = require('fs');

console.log('[F1 Bot Launcher] Starting bot wrapper...\n');

// Check if we're in a bothost.ru environment
const isBothost = process.env.BOTHOST || fs.existsSync('/.dockerenv');

// Try to ensure Python 3 is available
function ensurePython() {
  try {
    spawnSync('python3', ['--version'], { stdio: 'pipe', timeout: 5000 });
    console.log('[F1 Bot Launcher] ✓ Python3 found');
    return true;
  } catch (e) {
    console.log('[F1 Bot Launcher] ✗ Python3 not found\n');

    // Try to install Python
    console.log('[F1 Bot Launcher] Attempting to install Python3...\n');

    try {
      // Try apt-get (Debian/Ubuntu)
      console.log('[F1 Bot Launcher] Trying apt-get...');
      spawnSync('apt-get', ['update'], { stdio: 'pipe', timeout: 60000 });
      spawnSync('apt-get', ['install', '-y', 'python3', 'python3-pip'], { stdio: 'pipe', timeout: 120000 });
      console.log('[F1 Bot Launcher] ✓ Python3 installed successfully\n');
      return true;
    } catch (aptError) {
      console.log('[F1 Bot Launcher] apt-get failed\n');

      try {
        // Try apk (Alpine)
        console.log('[F1 Bot Launcher] Trying apk...');
        spawnSync('apk', ['add', '--no-cache', 'python3', 'py3-pip'], { stdio: 'pipe', timeout: 60000 });
        console.log('[F1 Bot Launcher] ✓ Python3 installed successfully\n');
        return true;
      } catch (apkError) {
        console.log('[F1 Bot Launcher] apk failed\n');
        return false;
      }
    }
  }
}

if (!ensurePython()) {
  console.error(`
╔════════════════════════════════════════════════════════════════╗
║                    ⚠️  CONFIGURATION REQUIRED                   ║
╚════════════════════════════════════════════════════════════════╝

Python 3 is required to run this bot, but it's not available in
your current container and cannot be auto-installed.

This usually means bothost.ru is using a Node.js container by
default, but this is a Python project.

🔧 HOW TO FIX:

1. Log in to your bothost.ru account
2. Go to your bot settings / configuration
3. Look for "Runtime", "Language", or "Environment" settings
4. Change from "Node.js" to "Python" or "Docker"
5. If available, select "Python 3.11" or use custom Dockerfile
6. Restart your bot

📝 ALTERNATIVE:

If bothost.ru dashboard doesn't show Python option:
- The platform may require manual configuration
- Contact bothost.ru support or consult their documentation
- This repository has a Dockerfile (FROM python:3.11-slim) that
  should be used as custom runtime

═══════════════════════════════════════════════════════════════════
`);
  process.exit(1);
}

// Install pip packages if requirements.txt exists
try {
  if (fs.existsSync(path.join(__dirname, 'requirements.txt'))) {
    console.log('[F1 Bot Launcher] Installing Python dependencies...');
    spawnSync('pip3', ['install', '-r', 'requirements.txt'], {
      cwd: __dirname,
      stdio: 'pipe',
      timeout: 120000
    });
    console.log('[F1 Bot Launcher] ✓ Dependencies installed\n');
  }
} catch (e) {
  console.warn('[F1 Bot Launcher] Warning: Could not install dependencies\n');
}

// Now spawn the Python bot
console.log('[F1 Bot Launcher] Starting Python bot...\n');
const pythonProcess = spawn('python3', [path.join(__dirname, 'bot.py')], {
  stdio: 'inherit',
  cwd: __dirname,
  shell: true  // Use shell to properly resolve python3 from PATH
});

pythonProcess.on('error', (err) => {
  if (err.code === 'ENOENT') {
    console.error(`
╔════════════════════════════════════════════════════════════════╗
║                  ❌ PYTHON3 NOT FOUND                           ║
╚════════════════════════════════════════════════════════════════╝

Cannot find python3 executable. This container doesn't have Python
installed or it's not in the PATH.

${isBothost ? 'bothost.ru detected - see instructions above.' : 'Please ensure Python 3 is installed on your system.'}
`);
  } else {
    console.error(`[F1 Bot Launcher] ✗ Failed to start bot: ${err.message}`);
  }
  process.exit(1);
});

pythonProcess.on('exit', (code) => {
  if (code !== 0) {
    console.error(`\n[F1 Bot Launcher] ✗ Bot exited with code ${code}`);
  } else {
    console.log('\n[F1 Bot Launcher] ✓ Bot stopped normally');
  }
  process.exit(code || 0);
});

// Handle termination signals gracefully
process.on('SIGINT', () => {
  console.log('[F1 Bot Launcher] Received SIGINT, stopping bot...');
  pythonProcess.kill('SIGINT');
});

process.on('SIGTERM', () => {
  console.log('[F1 Bot Launcher] Received SIGTERM, stopping bot...');
  pythonProcess.kill('SIGTERM');
});
