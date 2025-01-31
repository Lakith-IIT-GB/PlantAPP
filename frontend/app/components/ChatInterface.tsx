'use client';

import { useState, useRef, useEffect } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Paperclip, Send } from 'lucide-react';

interface Message {
  id: string;
  content: string;
  type: 'text' | 'file' | 'audio';
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
  const [ws, setWs] = useState<WebSocket | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  const simulateTyping = (fullMessage: string) => {
    let currentMessage = "";
    let index = 0;

    const interval = setInterval(() => {
      if (index < fullMessage.length) {
        currentMessage += fullMessage[index];
        setMessages(prev => prev.map((msg, i) => 
          i === prev.length - 1 
            ? { ...msg, content: currentMessage }
            : msg
        ));
        index++;
      } else {
        clearInterval(interval);
      }
    }, 25);
  };

  useEffect(() => {
    const websocket = new WebSocket('ws://localhost:8000/ws');
    
    websocket.onmessage = (event) => {
      const response = event.data;
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        content: '',
        type: 'text',
        sender: 'other'
      }]);
      simulateTyping(response);
    };

    setWs(websocket);

    return () => {
      websocket.close();
    };
  }, []);

  const handleSendMessage = () => {
    if (inputMessage.trim()) {
      const newMessage: Message = {
        id: Date.now().toString(),
        content: inputMessage,
        type: 'text',
        sender: 'user',
      };
      setMessages(prev => [...prev, newMessage]);
      
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(inputMessage);
      }
      
      setInputMessage('');
    }
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        const fileUrl = e.target?.result as string;
        const newMessage: Message = {
          id: Date.now().toString(),
          content: 'File uploaded',
          type: 'file',
          sender: 'user',
          fileUrl,
          fileName: file.name
        };
        setMessages(prev => [...prev, newMessage]);
      };
      reader.readAsDataURL(file);
    }
  };

  return (
    <div className="flex flex-col h-[600px] border rounded-lg bg-white">
      <ScrollArea className="flex-1 p-4" ref={scrollAreaRef}>
        <div className="space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${
                message.sender === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              <div
                className={`rounded-lg px-4 py-2 max-w-[80%] ${
                  message.sender === 'user'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted'
                }`}
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
            type="text"
            placeholder="Type a message..."
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter') {
                handleSendMessage();
              }
            }}
          />
          <input
            type="file"
            ref={fileInputRef}
            className="hidden"
            onChange={handleFileUpload}
          />
          <Button
            size="icon"
            variant="ghost"
            onClick={() => fileInputRef.current?.click()}
          >
            <Paperclip className="h-4 w-4" />
          </Button>
          <Button size="icon" onClick={handleSendMessage}>
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}