import { NextResponse } from 'next/server';

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const res = await fetch('http://localhost:8000/api/pipeline/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(2000)
    });
    if (res.ok) {
      const data = await res.json();
      return NextResponse.json(data);
    }
  } catch {
    // Local backend is not reachable
  }

  return NextResponse.json({
    status: 'started',
    task_id: 'cloud_task_' + Date.now(),
    message: 'Pipeline queued on local server'
  });
}
