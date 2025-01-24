'use client';

import React, { useState, useRef } from 'react';
import { Paperclip, Send } from 'lucide-react';
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
  const [messages, setMessages] = useState<Message[]>([]);
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
    <div className="flex flex-col h-[600px] max-w-2xl mx-auto bg-background border rounded-lg shadow-lg">
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
                  "max-w-[80%] rounded-lg p-3",
                  message.sender === 'user'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted'
                )}
              >
                {message.type === 'text' && <p>{message.content}</p>}
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

      <div className="p-4 border-t bg-background">
        <div className="flex items-center gap-2">
          <Input
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            placeholder="Type a message..."
            onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
            className="flex-1"
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
            className="h-10 w-10"
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