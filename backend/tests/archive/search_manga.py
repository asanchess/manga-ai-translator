import urllib.request
import re
from bs4 import BeautifulSoup
import json

url = 'https://mangakatana.com/?search=The+Ultimate+of+All+Ages'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    html = urllib.request.urlopen(req).read().decode()
    soup = BeautifulSoup(html, 'html.parser')
    manga_link = None
    for a in soup.find_all('a'):
        if 'The Ultimate of All Ages' in a.text and 'manga' in a.get('href', ''):
            manga_link = a['href']
            break
    print(f"Manga Link: {manga_link}")
    
    if manga_link:
        html2 = urllib.request.urlopen(urllib.request.Request(manga_link, headers={'User-Agent': 'Mozilla/5.0'})).read().decode()
        soup2 = BeautifulSoup(html2, 'html.parser')
        chapters = []
        for div in soup2.find_all('div', class_='chapter'):
            a = div.find('a')
            if a:
                chapters.append({
                    'title': a.text.strip(),
                    'link': a['href']
                })
        print(f"Found {len(chapters)} chapters.")
        if chapters:
            print("First chapter:", chapters[-1])
            print("Latest chapter:", chapters[0])
            # Find chapter 531
            for c in chapters:
                if '531' in c['title']:
                    print("Found Chapter 531:", c)
except Exception as e:
    print("Error:", e)
