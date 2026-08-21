import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export async function GET() {
  try {
    const indexPath = path.join(process.cwd(), 'public', 'manga', 'chapters_index.json');
    if (fs.existsSync(indexPath)) {
      const data = JSON.parse(fs.readFileSync(indexPath, 'utf-8'));
      const mangas = Object.keys(data).map(m => ({
        name: m,
        chapters: data[m].chapters.map((c: any) => c.number)
      }));
      return NextResponse.json({ mangas });
    }
  } catch (err) {
    console.error('Error in /api/studio/mangas route:', err);
  }

  return NextResponse.json({ mangas: [{ name: 'The_Ultimate_of_All_Ages', chapters: ['531', '532', '533', '534', '535', '536', '537', '538', '539', '540', '541', '542'] }] });
}
