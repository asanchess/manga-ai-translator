import { streamText, tool } from 'ai';
import { createOpenAI } from '@ai-sdk/openai';
import { z } from 'zod';

// We use the @ai-sdk/openai provider to connect to our local Ollama server, 
// because Ollama is compatible with the OpenAI API protocol.
const localOllama = createOpenAI({
  baseURL: 'http://localhost:11434/v1',
  apiKey: 'ollama', // API key is ignored by Ollama but required by the client
});

export const maxDuration = 30;

export async function POST(req: Request) {
  const { messages } = await req.json();

  const result = await streamText({
    model: localOllama('llama3'), 
    messages,
    system: `You are an AI Manga Assistant integrated into the manga reader platform. 
    You have access to 100+ manga sources via the "deploy_manga_chapter" tool.
    When a user asks you to find and download a chapter, you must call the tool, provide the manga title and chapter, and then tell the user you have started the process.
    Be helpful and concise. Keep responses short. Reply in Russian.`,
    tools: {
      deploy_manga_chapter: tool({
        description: 'Deploy a specific manga chapter to the local website by triggering the backend scraper and pipeline.',
        parameters: z.object({
          manga_title: z.string().describe('The name of the manga (e.g. "The Ultimate of All Ages").'),
          chapter_number: z.number().describe('The chapter number to download and deploy.'),
        }),
        execute: async ({ manga_title, chapter_number }) => {
          // Send request to our Python backend to start parsing and translation pipeline
          try {
            const backendRes = await fetch('http://localhost:8000/api/deploy', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ manga: manga_title, chapter: chapter_number }),
            });
            if (backendRes.ok) {
              return `✅ Процесс загрузки и перевода главы ${chapter_number} для манги "${manga_title}" успешно запущен на бэкенде!`;
            } else {
              return `❌ Ошибка бэкенда при попытке запустить деплой главы ${chapter_number}.`;
            }
          } catch (e) {
            console.error(e);
            return `❌ Не удалось связаться с локальным Manga API. Убедитесь, что сервер на порту 8000 запущен.`;
          }
        },
      }),
    },
  });

  return result.toDataStreamResponse();
}
