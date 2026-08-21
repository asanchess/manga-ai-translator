import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export async function GET(
  request: Request,
  context: { params: Promise<{ manga: string }> }
) {
  const { manga } = await context.params;
  
  // 1. Try reading from chapters_index.json in public/manga
  try {
    const indexPath = path.join(process.cwd(), 'public', 'manga', 'chapters_index.json');
    if (fs.existsSync(indexPath)) {
      const data = JSON.parse(fs.readFileSync(indexPath, 'utf-8'));
      if (data[manga]) {
        return NextResponse.json(data[manga]);
      }
    }
  } catch (err) {
    console.error('Error reading chapters_index.json:', err);
  }

  // 2. Fallback: try proxying to localhost:8000 if backend is active
  try {
    const res = await fetch(`http://localhost:8000/api/chapters/${manga}`, {
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

  return NextResponse.json({ error: 'Manga not found', manga, chapters: [] }, { status: 404 });
}
