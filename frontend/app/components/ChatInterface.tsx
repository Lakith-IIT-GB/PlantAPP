'use client';

import React, { useState, useRef } from 'react';
import { Paperclip, Send, Leaf } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { AudioRecorder } from './AudioRecorder';
import { ScrollArea } from '@/components/ui/scroll-area';
import { cn } from '@/lib/utils';

interface Message {
  id: string;
  content: string;
  type: 'text' | 'audio' | 'file';
  sender: 'user' | 'other';
  fileUrl?: string;
  fileName?: string;
}

export function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([{
    id: '1',
    content: 'Hello! I\'m your plant care assistant. How can I help you with your plants today? 🌿',
    type: 'text',
    sender: 'other'
  }]);
  const [inputMessage, setInputMessage] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSendMessage = () => {
    if (inputMessage.trim()) {
      const newMessage: Message = {
        id: Date.now().toString(),
        content: inputMessage,
        type: 'text',
        sender: 'user',
      };
      setMessages([...messages, newMessage]);
      setInputMessage('');
    }
  };

  const handleAudioCapture = (audioBlob: Blob) => {
    const audioUrl = URL.createObjectURL(audioBlob);
    const newMessage: Message = {
      id: Date.now().toString(),
      content: 'Audio message',
      type: 'audio',
      sender: 'user',
      fileUrl: audioUrl,
    };
    setMessages([...messages, newMessage]);
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const fileUrl = URL.createObjectURL(file);
      const newMessage: Message = {
        id: Date.now().toString(),
        content: 'File attachment',
        type: 'file',
        sender: 'user',
        fileUrl,
        fileName: file.name,
      };
      setMessages([...messages, newMessage]);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-24rem)] bg-white/95 backdrop-blur-sm border-2 border-primary/20 rounded-xl shadow-xl overflow-hidden">
      <div className="bg-primary/10 p-4 border-b border-primary/20">
        <div className="flex items-center gap-2">
          <Leaf className="h-5 w-5 text-primary" />
          <h2 className="text-lg font-semibold text-primary">Plant Care Chat</h2>
        </div>
      </div>
      <ScrollArea className="flex-1 p-4">
        <div className="space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={cn(
                "flex",
                message.sender === 'user' ? 'justify-end' : 'justify-start'
              )}
            >
              <div
                className={cn(
                  "max-w-[80%] rounded-xl p-3 shadow-md",
                  message.sender === 'user'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-white text-foreground border border-primary/20'
                )}
              >
                {message.type === 'text' && <p className="font-medium">{message.content}</p>}
                {message.type === 'audio' && (
                  <audio controls src={message.fileUrl} className="max-w-full" />
                )}
                {message.type === 'file' && (
                  <a
                    href={message.fileUrl}
                    download={message.fileName}
                    className="flex items-center gap-2 text-sm"
                  >
                    <Paperclip className="h-4 w-4" />
                    {message.fileName}
                  </a>
                )}
              </div>
            </div>
          ))}
        </div>
      </ScrollArea>

      <div className="p-4 border-t border-primary/20 bg-white/80">
        <div className="flex items-center gap-2">
          <Input
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            placeholder="Ask about your plants..."
            onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
            className="flex-1 bg-white border-primary/20 focus:border-primary/40"
          />
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileUpload}
            className="hidden"
          />
          <Button
            onClick={() => fileInputRef.current?.click()}
            variant="outline"
            size="icon"
            className="h-10 w-10 border-primary/20 hover:bg-primary/10"
          >
            <Paperclip className="h-4 w-4" />
          </Button>
          <AudioRecorder onAudioCapture={handleAudioCapture} />
          <Button onClick={handleSendMessage} size="icon" className="h-10 w-10">
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}