import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export async function GET() {
  try {
    const indexPath = path.join(process.cwd(), 'public', 'manga', 'chapters_index.json');
    if (fs.existsSync(indexPath)) {
      const raw = fs.readFileSync(indexPath, 'utf-8');
      const data = JSON.parse(raw);
      const mangasObj = data.mangas || (data.chapters ? { [data.title || 'Manga']: data } : data);
      
      const mangas = Object.keys(mangasObj)
        .filter((k) => k !== 'title' && k !== 'last_synced')
        .map((m) => {
          const entry = mangasObj[m];
          const rawChapters = entry?.chapters || [];
          const chapters = rawChapters.map((c: any) =>
            String(c.chapter || c.number || c.folder?.replace('chapter_', '') || c)
          );
          return {
            name: m,
            title: entry?.title || m.replace(/_/g, ' '),
            chapters,
            chapters_meta: rawChapters,
            total_chapters: entry?.total_chapters || chapters.length
          };
        });

      if (mangas.length > 0) {
        return NextResponse.json({ mangas });
      }
    }
  } catch (err) {
    console.error('Error in /api/studio/mangas route:', err);
  }

  return NextResponse.json({
    mangas: [
      {
        name: 'The_Ultimate_of_All_Ages',
        title: 'The Ultimate of All Ages',
        chapters: ['531', '532', '533', '534', '535', '536', '537', '538', '539', '540', '541', '542'],
        total_chapters: 12
      }
    ]
  });
}

