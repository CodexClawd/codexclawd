#!/usr/bin/env node
const { default: makeWASocket, useMultiFileAuthState } = require('@whiskeysockets/baileys');

async function pairWithCode() {
    console.log('🔧 WhatsApp Pairing with Code\n');
    
    const { state, saveCreds } = await useMultiFileAuthState('/home/boss/.openclaw/whatsapp-session');
    
    // Your phone number (German format without +)
    const phoneNumber = '4917641731790';  // Update this if needed
    
    const sock = makeWASocket({ 
        auth: state,
        printQRInTerminal: false
    });
    
    sock.ev.on('connection.update', async (update) => {
        const { connection, qr } = update;
        
        if (qr) {
            console.log('📱 QR Code available, but trying pairing code...\n');
            
            // Request pairing code
            try {
                const code = await sock.requestPairingCode(phoneNumber);
                console.log('═══════════════════════════════════════');
                console.log('  📲 PAIRING CODE:', code);
                console.log('═══════════════════════════════════════\n');
                console.log('To use this code:');
                console.log('1. Open WhatsApp on your phone');
                console.log('2. Settings → Linked Devices → Link a Device');
                console.log('3. Tap "Link with phone number instead"');
                console.log('4. Enter this code:', code);
                console.log('\n⏳ Waiting for connection...\n');
            } catch (e) {
                console.log('❌ Pairing code failed, use QR code instead');
            }
        }
        
        if (connection === 'open') {
            console.log('✅ CONNECTED! WhatsApp is ready.');
            console.log('Your number:', sock.user.id);
            
            // Send test message
            await sock.sendMessage(sock.user.id, {
                text: '🦞 BRUTUS here! WhatsApp reminders are now active.'
            });
            console.log('Test message sent!');
            
            setTimeout(() => {
                console.log('\n👋 Setup complete!');
                process.exit(0);
            }, 3000);
        }
        
        if (connection === 'close') {
            console.log('❌ Connection closed');
        }
    });
    
    sock.ev.on('creds.update', saveCreds);
}

pairWithCode().catch(console.error);
