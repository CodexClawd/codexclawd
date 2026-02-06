#!/usr/bin/env node
const { default: makeWASocket, useMultiFileAuthState } = require('@whiskeysockets/baileys');

async function sendTest() {
    const { state, saveCreds } = await useMultiFileAuthState('/home/boss/.openclaw/whatsapp-session');
    const sock = makeWASocket({ auth: state });
    
    sock.ev.on('connection.update', async (update) => {
        if (update.connection === 'open') {
            console.log('Connected! Sending test message...');
            await sock.sendMessage('4917641731790@s.whatsapp.net', {
                text: '🦞 BRUTUS here! WhatsApp reminders are now active.\n\nYou\'ll get pings like this for tasks you set.'
            });
            console.log('Test message sent!');
            process.exit(0);
        }
    });
    
    sock.ev.on('creds.update', saveCreds);
}

sendTest();
