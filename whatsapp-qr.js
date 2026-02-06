#!/usr/bin/env node
/**
 * WhatsApp QR Code Generator - Saves QR as image
 */

const { default: makeWASocket, useMultiFileAuthState } = require('@whiskeysockets/baileys');
const QRCode = require('qrcode');
const fs = require('fs');

const SESSION_PATH = '/home/boss/.openclaw/whatsapp-session';

async function generateQR() {
    console.log('🔧 Generating WhatsApp QR Code...\n');
    
    if (!fs.existsSync(SESSION_PATH)) {
        fs.mkdirSync(SESSION_PATH, { recursive: true });
    }
    
    const { state, saveCreds } = await useMultiFileAuthState(SESSION_PATH);
    
    const sock = makeWASocket({ auth: state });
    
    sock.ev.on('connection.update', async (update) => {
        const { qr, connection } = update;
        
        if (qr) {
            console.log('📱 QR Code received!');
            
            // Save as PNG
            const qrPath = '/home/boss/.openclaw/workspace/whatsapp-qr.png';
            await QRCode.toFile(qrPath, qr, { width: 400 });
            console.log('💾 QR Code saved to:', qrPath);
            
            // Also output text version
            console.log('\nText QR Code (if image fails):');
            const qrText = await QRCode.toString(qr, { type: 'terminal', small: true });
            console.log(qrText);
            
            console.log('\n⏳ Scan with WhatsApp → Settings → Linked Devices → Link a Device');
            console.log('   You have 60 seconds!\n');
        }
        
        if (connection === 'open') {
            console.log('✅ Connected! WhatsApp is ready.');
            console.log('   Your number:', sock.user.id);
            process.exit(0);
        }
    });
    
    sock.ev.on('creds.update', saveCreds);
}

generateQR().catch(console.error);
