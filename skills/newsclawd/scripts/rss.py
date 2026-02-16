#!/usr/bin/env python3
"""NewsClawd - RSS feed monitor"""
import sys
import json
import re
from datetime import datetime
from urllib.request import urlopen
from xml.etree import ElementTree as ET

def parse_feed(url, keywords=None, max_items=5):
    """Parse RSS/Atom feed and filter by keywords"""
    try:
        with urlopen(url, timeout=30) as response:
            data = response.read()
        
        root = ET.fromstring(data)
        
        # Handle RSS 2.0 and Atom
        items = []
        channel = root.find('channel') if root.tag == 'rss' else root
        
        for item in channel.findall('.//item') if channel is not None else root.findall('.//{http://www.w3.org/2005/Atom}entry'):
            title = item.find('title')
            title_text = title.text if title is not None else ''
            
            link = item.find('link')
            link_text = link.text if link is not None else ''
            if link_text == '' and link is not None:
                link_text = link.get('href', '')
            
            desc = item.find('description') or item.find('.//{http://www.w3.org/2005/Atom}summary')
            desc_text = desc.text if desc is not None else ''
            
            # Check keywords
            if keywords:
                text = f"{title_text} {desc_text}".lower()
                if not any(kw.lower() in text for kw in keywords):
                    continue
            
            items.append({
                'title': title_text,
                'link': link_text,
                'description': desc_text[:200] + '...' if len(desc_text) > 200 else desc_text
            })
            
            if len(items) >= max_items:
                break
        
        return items
    except Exception as e:
        return {'error': str(e)}

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', required=True)
    parser.add_argument('--keywords', help='Comma-separated keywords')
    parser.add_argument('--max', type=int, default=5)
    args = parser.parse_args()
    
    keywords = [k.strip() for k in args.keywords.split(',')] if args.keywords else None
    items = parse_feed(args.url, keywords, args.max)
    
    if isinstance(items, dict) and 'error' in items:
        print(f"❌ Error: {items['error']}", file=sys.stderr)
        sys.exit(1)
    
    if not items:
        print("📭 No matching items found")
        sys.exit(0)
    
    print(f"📰 Found {len(items)} items:\n")
    for item in items:
        print(f"🔹 {item['title']}")
        if item['link']:
            print(f"   {item['link']}")
        if item['description']:
            print(f"   {item['description'][:150]}...")
        print()

if __name__ == '__main__':
    main()
