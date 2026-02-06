#!/usr/bin/env node
/**
 * WhatsApp Setup Script for Flo
 * Run once to authenticate, then use for reminder output
 */

const { default: makeWASocket, DisconnectReason, useMultiFileAuthState, fetchLatestBaileysVersion } = require('@whiskeysockets/baileys');
const qrcode = require('qrcode-terminal');
const fs = require('fs');
const path = require('path');

const SESSION_PATH = '/home/boss/.openclaw/whatsapp-session';
const CONFIG_PATH = '/home/boss/.openclaw/openclaw.json';

async function setupWhatsApp() {
    console.log('🔧 Setting up WhatsApp for BRUTUS...\n');
    
    // Ensure session directory exists
    if (!fs.existsSync(SESSION_PATH)) {
        fs.mkdirSync(SESSION_PATH, { recursive: true });
    }
    
    const { state, saveCreds } = await useMultiFileAuthState(SESSION_PATH);
    
    const sock = makeWASocket({
        auth: state,
        // QR handling done manually below
    });
    
    sock.ev.on('connection.update', (update) => {
        const { connection, lastDisconnect, qr } = update;
        
        if (qr) {
            console.log('\n📱 QR Code generated! Scan with WhatsApp:');
            console.log('   Open WhatsApp → Settings → Linked Devices → Link a Device\n');
            console.log('   QR Code:\n');
            qrcode.generate(qr, { small: true });
            console.log('\n');
        }
        
        if (connection === 'close') {
            const shouldReconnect = (lastDisconnect?.error)?.output?.statusCode !== DisconnectReason.loggedOut;
            console.log('\n❌ Connection closed:', shouldReconnect ? 'reconnecting...' : 'logged out');
            if (shouldReconnect) {
                setupWhatsApp();
            }
        } else if (connection === 'open') {
            console.log('\n✅ WhatsApp connected!');
            console.log('   Your number:', sock.user.id);
            console.log('   Name:', sock.user.name);
            console.log('\n💾 Session saved to:', SESSION_PATH);
            console.log('   You can now use WhatsApp for reminders.\n');
            
            // Update OpenClaw config
            updateConfig(sock.user.id);
            
            // Send test message
            console.log('📤 Sending test message to yourself...');
            sendTestMessage(sock, sock.user.id);
        }
    });
    
    sock.ev.on('creds.update', saveCreds);
}

function updateConfig(phoneNumber) {
    try {
        const config = JSON.parse(fs.readFileSync(CONFIG_PATH, 'utf8'));
        
        // Add WhatsApp channel
        if (!config.channels) config.channels = {};
        
        config.channels.whatsapp = {
            enabled: true,
            provider: 'baileys',
            sessionPath: SESSION_PATH,
            outputOnly: true,
            defaultTarget: phoneNumber,
            // Mark as output-only (BRUTUS sends, doesn't receive)
            receiveMessages: false
        };
        
        fs.writeFileSync(CONFIG_PATH, JSON.stringify(config, null, 2));
        console.log('✅ OpenClaw config updated with WhatsApp channel\n');
    } catch (e) {
        console.log('⚠️  Could not auto-update config:', e.message);
        console.log('   Add this to your openclaw.json manually:\n');
        console.log(JSON.stringify({
            whatsapp: {
                enabled: true,
                provider: 'baileys',
                sessionPath: SESSION_PATH,
                outputOnly: true,
                defaultTarget: phoneNumber
            }
        }, null, 2));
    }
}

async function sendTestMessage(sock, to) {
    try {
        await sock.sendMessage(to, {
            text: '🦞 BRUTUS here! WhatsApp reminders are now active.\n\nYou\'ll get pings like this for tasks you set.'
        });
        console.log('✅ Test message sent!\n');
    } catch (e) {
        console.log('⚠️  Test message failed:', e.message);
    }
    
    // Keep connection alive for a bit, then exit
    setTimeout(() => {
        console.log('👋 Setup complete. You can close this now.\n');
        process.exit(0);
    }, 3000);
}

// Run
setupWhatsApp().catch(console.error);
