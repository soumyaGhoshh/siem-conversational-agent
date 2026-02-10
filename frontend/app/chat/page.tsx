'use client';

import { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import { ProtectedRoute } from '@/components/protected-route';
import { ChatSidebar } from '@/components/chat-sidebar';
import { ChatMessages } from '@/components/chat-messages';
import { ChatInput } from '@/components/chat-input';
import { ChatResponseTabs } from '@/components/chat-response-tabs';
import { apiClient } from '@/lib/api-client';
import { useAppStore } from '@/lib/store';
import type { ChatResponse } from '@/lib/types';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  response?: ChatResponse;
}

export default function ChatPage() {
  const searchParams = useSearchParams();
  const prefilledQuery = searchParams.get('query') || '';

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedResponseId, setSelectedResponseId] = useState<string | null>(null);

  const selectedIndex = useAppStore((state) => state.selectedIndex);
  const maxResults = useAppStore((state) => state.maxResults);
  const allowedIndices = useAppStore((state) => state.allowedIndices);
  const accessToken = useAppStore((state) => state.user?.accessToken);

  const handleSendMessage = async (text: string) => {
    // Add user message
    const userMsgId = Date.now().toString();
    setMessages((prev) => [
      ...prev,
      {
        id: userMsgId,
        role: 'user',
        content: text,
      },
    ]);

    setIsLoading(true);

    try {
      // Call chat API
      console.log('Sending chat request:', { text, selectedIndex, maxResults });
      const response = await apiClient.chat(text, selectedIndex, maxResults, accessToken);
      console.log('Received chat response:', response);

      const assistantMsgId = (Date.now() + 1).toString();
      setMessages((prev) => [
        ...prev,
        {
          id: assistantMsgId,
          role: 'assistant',
          content: `Found ${response.results.totalHits} results`,
          response,
        },
      ]);

      setSelectedResponseId(assistantMsgId);
    } catch (err) {
      console.error('Chat error:', err);
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: 'Error processing your request. Please try again.',
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const selectedResponse = messages.find((m) => m.id === selectedResponseId);

  return (
    <ProtectedRoute>
      <div className="flex h-screen bg-slate-950">
        <ChatSidebar allowedIndices={allowedIndices} />

        <div className="flex flex-1 flex-col overflow-hidden">
          {/* Messages Area */}
          <div className="flex-1 overflow-hidden border-b border-slate-700 p-6">
            <ChatMessages messages={messages} />
          </div>

          {/* Response Tabs */}
          {selectedResponse?.response && (
            <div className="max-h-80 overflow-y-auto border-b border-slate-700 p-6">
              <ChatResponseTabs response={selectedResponse.response} />
            </div>
          )}

          {/* Input Area */}
          <div className="p-6">
            <ChatInput
              onSubmit={handleSendMessage}
              isLoading={isLoading}
              prefilledQuery={prefilledQuery}
            />
          </div>
        </div>
      </div>
    </ProtectedRoute>
  );
}
