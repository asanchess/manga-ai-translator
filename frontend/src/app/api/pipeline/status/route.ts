import { NextResponse } from 'next/server';

export async function GET() {
  try {
    const res = await fetch('http://localhost:8000/api/pipeline/status', {
      signal: AbortSignal.timeout(1000)
    });
    if (res.ok) {
      const data = await res.json();
      return NextResponse.json(data);
    }
  } catch {
    // Local backend is not reachable
  }

  return NextResponse.json({
    status: 'idle',
    current_agent: 'Готов к работе',
    progress: 100,
    current_page: 0,
    total_pages: 0,
    logs: ['[System] Система готова к переводу глав.']
  });
}
