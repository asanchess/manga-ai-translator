'use client';

import { useChat } from 'ai/react';
import { useState, useRef, useEffect } from 'react';

export default function AssistantChat() {
  const [isOpen, setIsOpen] = useState(false);
  const { messages, input, handleInputChange, handleSubmit, isLoading } = useChat();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="fixed bottom-4 right-4 z-50">
      {/* Chat Window */}
      {isOpen && (
        <div className="bg-white text-black w-80 h-[500px] mb-4 rounded-xl shadow-2xl flex flex-col overflow-hidden border border-gray-200">
          <div className="bg-blue-600 text-white p-4 font-bold flex justify-between items-center">
            <span>Manga Assistant AI</span>
            <button onClick={() => setIsOpen(false)} className="hover:text-gray-200">✕</button>
          </div>
          
          <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-3 bg-gray-50">
            {messages.length === 0 && (
              <div className="text-gray-500 text-sm text-center mt-10">
                Привет! Я могу скачать и перевести для вас мангу с сотни сайтов. Напишите, например: "Скачай главу 15 The Ultimate of All Ages".
              </div>
            )}
            
            {messages.map(m => (
              <div key={m.id} className={`flex flex-col ${m.role === 'user' ? 'items-end' : 'items-start'}`}>
                <div className={`px-4 py-2 rounded-2xl max-w-[85%] ${
                  m.role === 'user' 
                    ? 'bg-blue-600 text-white rounded-br-none' 
                    : 'bg-white text-gray-800 border border-gray-200 rounded-bl-none shadow-sm'
                }`}>
                  {m.content}
                </div>
              </div>
            ))}
            
            {isLoading && (
              <div className="flex items-start">
                <div className="px-4 py-2 bg-white text-gray-800 border border-gray-200 rounded-2xl rounded-bl-none shadow-sm flex gap-1 items-center">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '150ms'}}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '300ms'}}></div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <form onSubmit={handleSubmit} className="p-3 bg-white border-t border-gray-200">
            <div className="flex gap-2">
              <input
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={input}
                placeholder="Спроси меня о манге..."
                onChange={handleInputChange}
              />
              <button 
                type="submit" 
                disabled={isLoading || !input.trim()}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg font-medium disabled:opacity-50 hover:bg-blue-700 transition"
              >
                Отправить
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Floating Button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="w-14 h-14 bg-blue-600 hover:bg-blue-700 text-white rounded-full shadow-lg flex items-center justify-center transition-transform hover:scale-110"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
          </svg>
        </button>
      )}
    </div>
  );
}
