#!/usr/bin/env node
const { default: makeWASocket, useMultiFileAuthState } = require('@whiskeysockets/baileys');

async function connect() {
    const { state, saveCreds } = await useMultiFileAuthState('/home/boss/.openclaw/whatsapp-session');
    const sock = makeWASocket({ auth: state });
    
    sock.ev.on('connection.update', (update) => {
        const { connection, qr } = update;
        if (qr) {
            console.log('New QR needed - scan with phone');
        }
        if (connection === 'open') {
            console.log('✅ CONNECTED! WhatsApp is ready.');
            console.log('Number:', sock.user.id);
            sock.sendMessage(sock.user.id, { text: '🦞 BRUTUS here! WhatsApp reminders active.' });
            setTimeout(() => process.exit(0), 3000);
        }
        if (connection === 'close') {
            console.log('❌ Connection closed');
        }
    });
    
    sock.ev.on('creds.update', saveCreds);
}

connect();
