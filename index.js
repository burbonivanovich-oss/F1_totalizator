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

console.log('[F1 Bot Launcher v4] Starting bot wrapper...\n');

// Check if we're in a bothost.ru environment
const isBothost = process.env.BOTHOST || fs.existsSync('/.dockerenv');

// Try to ensure Python 3 is available
function ensurePython() {
  // Check if Python3 is already available
  try {
    const checkResult = spawnSync('python3', ['--version'], {
      stdio: 'pipe',
      timeout: 5000,
      encoding: 'utf-8'
    });

    if (checkResult.error) {
      throw checkResult.error;
    }
    if (checkResult.status !== 0 && checkResult.status !== null) {
      throw new Error(`python3 --version exited with code ${checkResult.status}`);
    }

    console.log('[F1 Bot Launcher] ✓ Python3 found');
    return true;
  } catch (e) {
    console.log('[F1 Bot Launcher] ✗ Python3 not found\n');
    console.log('[F1 Bot Launcher] Attempting to install Python3...\n');

    // Try apt-get (Debian/Ubuntu)
    try {
      console.log('[F1 Bot Launcher] Trying apt-get update...');
      const updateResult = spawnSync('apt-get', ['update'], {
        stdio: 'pipe',
        timeout: 60000
      });

      if (updateResult.error || (updateResult.status !== 0 && updateResult.status !== null)) {
        throw new Error('apt-get update failed');
      }

      console.log('[F1 Bot Launcher] Trying apt-get install...');
      const installResult = spawnSync('apt-get', ['install', '-y', 'python3', 'python3-pip'], {
        stdio: 'pipe',
        timeout: 120000
      });

      if (installResult.error || (installResult.status !== 0 && installResult.status !== null)) {
        throw new Error('apt-get install failed');
      }

      console.log('[F1 Bot Launcher] ✓ Python3 installed via apt-get\n');
      return true;
    } catch (aptError) {
      console.log(`[F1 Bot Launcher] apt-get failed: ${aptError.message}\n`);

      // Try apk (Alpine)
      try {
        console.log('[F1 Bot Launcher] Trying apk add...');
        const apkResult = spawnSync('apk', ['add', '--no-cache', 'python3', 'py3-pip'], {
          stdio: 'pipe',
          timeout: 60000
        });

        if (apkResult.error || (apkResult.status !== 0 && apkResult.status !== null)) {
          throw new Error('apk add failed');
        }

        console.log('[F1 Bot Launcher] ✓ Python3 installed via apk\n');
        return true;
      } catch (apkError) {
        console.log(`[F1 Bot Launcher] apk failed: ${apkError.message}\n`);
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
    // Use python3 -m pip instead of pip3 to ensure same Python version
    const pipResult = spawnSync('python3', ['-m', 'pip', 'install', '--user', '-r', 'requirements.txt'], {
      cwd: __dirname,
      stdio: 'inherit',
      timeout: 300000
    });

    if (pipResult.error || (pipResult.status !== 0 && pipResult.status !== null)) {
      console.warn(`[F1 Bot Launcher] Warning: pip install failed with status ${pipResult.status}\n`);
      // Try with --break-system-packages flag (needed on newer Python/Debian)
      console.log('[F1 Bot Launcher] Retrying with --break-system-packages...');
      const pipResult2 = spawnSync('python3', ['-m', 'pip', 'install', '--break-system-packages', '-r', 'requirements.txt'], {
        cwd: __dirname,
        stdio: 'inherit',
        timeout: 300000
      });
      if (pipResult2.error || (pipResult2.status !== 0 && pipResult2.status !== null)) {
        console.warn(`[F1 Bot Launcher] Warning: pip install retry also failed with status ${pipResult2.status}\n`);
      } else {
        console.log('[F1 Bot Launcher] ✓ Dependencies installed (with --break-system-packages)\n');
      }
    } else {
      console.log('[F1 Bot Launcher] ✓ Dependencies installed\n');
    }
  }
} catch (e) {
  console.warn(`[F1 Bot Launcher] Warning: Could not install dependencies: ${e.message}\n`);
}

// Now spawn the Python bot
console.log('[F1 Bot Launcher] Starting Python bot...\n');
// Embed PYTHONPATH directly in the shell command to ensure it reaches Python
// regardless of how the platform handles env vars passed to spawn.
const botPath = path.join(__dirname, 'bot.py');
const pythonProcess = spawn(
  `PYTHONPATH="${__dirname}" python3 "${botPath}"`,
  [],
  {
    stdio: 'inherit',
    cwd: __dirname,
    shell: true,
  }
);

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
