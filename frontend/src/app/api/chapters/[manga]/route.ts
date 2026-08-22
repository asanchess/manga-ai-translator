import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export async function GET(
  request: Request,
  context: { params: Promise<{ manga: string }> }
) {
  const { manga } = await context.params;
  const cleanManga = manga.replace(/ /g, '_');
  
  // 1. Direct filesystem inspection of public/manga/{manga}
  try {
    const mangaDir = path.join(process.cwd(), 'public', 'manga', cleanManga);
    if (fs.existsSync(mangaDir) && fs.statSync(mangaDir).isDirectory()) {
      const chapterFolders = fs.readdirSync(mangaDir).filter(f => f.startsWith('chapter_') && fs.statSync(path.join(mangaDir, f)).isDirectory());
      
      const chapters = chapterFolders.map(chFolder => {
        const chNum = chFolder.replace('chapter_', '');
        const chPath = path.join(mangaDir, chFolder);
        
        const versions: {
          v1_original: string[];
          v2_cleaned: string[];
          v3_translated: string[];
        } = {
          v1_original: [],
          v2_cleaned: [],
          v3_translated: []
        };
        
        // Check v1 / v1_original
        const v1Dir = fs.existsSync(path.join(chPath, 'v1')) ? path.join(chPath, 'v1') : path.join(chPath, 'v1_original');
        if (fs.existsSync(v1Dir)) {
          const files = fs.readdirSync(v1Dir).filter(f => (f.endsWith('.webp') || f.endsWith('.png') || f.endsWith('.jpg')) && !f.endsWith('.ocr.json'));
          files.sort();
          const sub = fs.existsSync(path.join(chPath, 'v1')) ? 'v1' : 'v1_original';
          versions.v1_original = files.map(f => `/manga/${cleanManga}/${chFolder}/${sub}/${f}`);
        }
        
        // Check v2 / v2_cleaned
        const v2Dir = fs.existsSync(path.join(chPath, 'v2')) ? path.join(chPath, 'v2') : path.join(chPath, 'v2_cleaned');
        if (fs.existsSync(v2Dir)) {
          const files = fs.readdirSync(v2Dir).filter(f => (f.endsWith('.webp') || f.endsWith('.png') || f.endsWith('.jpg')) && !f.endsWith('.ocr.json'));
          files.sort();
          const sub = fs.existsSync(path.join(chPath, 'v2')) ? 'v2' : 'v2_cleaned';
          versions.v2_cleaned = files.map(f => `/manga/${cleanManga}/${chFolder}/${sub}/${f}`);
        }
        
        // Check v3 / v3_translated
        const v3Dir = fs.existsSync(path.join(chPath, 'v3')) ? path.join(chPath, 'v3') : path.join(chPath, 'v3_translated');
        if (fs.existsSync(v3Dir)) {
          const files = fs.readdirSync(v3Dir).filter(f => (f.endsWith('.webp') || f.endsWith('.png') || f.endsWith('.jpg')) && !f.endsWith('.ocr.json'));
          files.sort();
          const sub = fs.existsSync(path.join(chPath, 'v3')) ? 'v3' : 'v3_translated';
          versions.v3_translated = files.map(f => `/manga/${cleanManga}/${chFolder}/${sub}/${f}`);
        }
        
        return {
          number: chNum,
          versions
        };
      });
      
      chapters.sort((a, b) => {
        const numA = parseInt(a.number, 10);
        const numB = parseInt(b.number, 10);
        if (!isNaN(numA) && !isNaN(numB)) return numA - numB;
        return a.number.localeCompare(b.number);
      });
      
      if (chapters.length > 0) {
        return NextResponse.json({
          manga: cleanManga,
          chapters
        });
      }
    }
  } catch (err) {
    console.error('Error scanning public/manga directory:', err);
  }

  // 2. Fallback: try proxying to localhost:8000 if backend is active
  try {
    const res = await fetch(`http://localhost:8000/api/chapters/${cleanManga}`, {
      next: { revalidate: 0 },
      signal: AbortSignal.timeout(1500)
    });
    if (res.ok) {
      const data = await res.json();
      return NextResponse.json(data);
    }
  } catch {
    // Backend not running on localhost
  }

  return NextResponse.json({ error: 'Manga not found', manga: cleanManga, chapters: [] }, { status: 404 });
}
