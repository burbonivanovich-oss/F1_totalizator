#!/usr/bin/env node
/**
 * Node.js wrapper to run Python Telegram bot.
 * Created to prevent bothost.ru from directly executing webapp.js as Node.js.
 */

const { spawn } = require('child_process');
const path = require('path');

const pythonProcess = spawn('python3', [path.join(__dirname, 'bot.py')], {
  stdio: 'inherit',
  cwd: __dirname,
  shell: true
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
