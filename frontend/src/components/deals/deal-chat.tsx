"use client";

import { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useDealMessages, useSendMessage } from '@/hooks/useDeals';
import { useAuthStore } from '@/store/auth';
import { formatDate } from '@/lib/utils';
import { Send, Loader2, MessageCircle } from 'lucide-react';

interface DealChatProps {
  dealId: string;
}

export function DealChat({ dealId }: DealChatProps) {
  const { user } = useAuthStore();
  const { data: messagesData, isLoading } = useDealMessages(dealId);
  const sendMessage = useSendMessage();
  const [message, setMessage] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => { scrollToBottom(); }, [messagesData]);

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim()) return;
    sendMessage.mutate({ dealId, content: message }, {
      onSuccess: () => setMessage(''),
    });
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  const messages = messagesData?.results || [];

  return (
    <div className="space-y-3">
      {/* Messages container */}
      <div className="h-[400px] overflow-y-auto space-y-3 p-4 rounded-2xl bg-muted/20 border border-border/40 shadow-[inset_0_2px_8px_rgba(0,0,0,0.06)]">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-muted/60 mb-3 shadow-[inset_0_2px_6px_rgba(0,0,0,0.06)]">
              <MessageCircle className="h-5 w-5 text-muted-foreground" />
            </div>
            <p className="text-sm text-muted-foreground font-medium">No messages yet</p>
            <p className="text-xs text-muted-foreground mt-0.5">Start the conversation!</p>
          </div>
        ) : (
          messages.map((msg: any) => {
            const isOwn = msg.sender_id === user?.id;
            return (
              <div key={msg.id} className={`flex ${isOwn ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[72%] rounded-2xl px-4 py-2.5 ${
                  isOwn
                    ? 'chat-bubble-own text-white rounded-br-sm'
                    : 'chat-bubble-other rounded-bl-sm'
                }`}>
                  {!isOwn && (
                    <div className="text-xs font-semibold mb-1 text-primary">
                      {msg.sender_username}
                    </div>
                  )}
                  <div className="text-sm leading-relaxed">{msg.content}</div>
                  <div className={`text-xs mt-1 ${isOwn ? 'text-white/60' : 'text-muted-foreground'}`}>
                    {formatDate(msg.created_at)}
                  </div>
                </div>
              </div>
            );
          })
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSend} className="flex space-x-2.5">
        <Input
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Type a message..."
          disabled={sendMessage.isPending}
          className="rounded-xl"
        />
        <Button
          type="submit"
          size="icon"
          className="rounded-xl shrink-0"
          disabled={!message.trim() || sendMessage.isPending}
        >
          {sendMessage.isPending ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Send className="h-4 w-4" />
          )}
        </Button>
      </form>
    </div>
  );
}
