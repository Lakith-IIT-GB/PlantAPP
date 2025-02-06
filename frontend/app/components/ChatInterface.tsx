'use client';

import { useState, useRef, useEffect } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Paperclip, Send, Mic } from 'lucide-react';
import { AudioRecorder } from './AudioRecorder';

interface Message {
  id: string;
  content: string;
  type: 'text' | 'file' | 'audio' | 'image';
  sender: 'user' | 'other';
  fileUrl?: string;
  fileName?: string;
  audioUrl?: string;
  imageUrl?: string;
  isTyping?: boolean;
  displayedContent?: string;
}

export function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([{
    id: '1',
    content: 'Hello! I\'m your plant care assistant. How can I help you with your plants today? 🌿',
    type: 'text',
    sender: 'other',
    isTyping: true,
    displayedContent: ''
  }]);
  const [inputMessage, setInputMessage] = useState('');
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [showAudioRecorder, setShowAudioRecorder] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  const simulateTyping = (fullMessage: string, messageId: string) => {
    let currentText = "";
    let charIndex = 0;

    const typeChar = () => {
      if (charIndex < fullMessage.length) {
        currentText += fullMessage[charIndex];
        setMessages(prev => prev.map(msg => 
          msg.id === messageId 
            ? { ...msg, displayedContent: currentText, isTyping: true }
            : msg
        ));
        charIndex++;
        setTimeout(typeChar, 25);
      } else {
        setMessages(prev => prev.map(msg => 
          msg.id === messageId 
            ? { ...msg, isTyping: false }
            : msg
        ));
      }
    };

    typeChar();
  };

  useEffect(() => {
    const initialMessage = messages[0];
    simulateTyping(initialMessage.content, initialMessage.id);
  }, []); // Initial greeting animation

  useEffect(() => {
    const websocket = new WebSocket('ws://52.207.245.139:8000/ws');
    
    websocket.onmessage = (event) => {
      const response = event.data;
      const messageId = Date.now().toString();
      
      setMessages(prev => [...prev, {
        id: messageId,
        content: response,
        type: 'text',
        sender: 'other',
        isTyping: true,
        displayedContent: ''
      }]);

      simulateTyping(response, messageId);
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

  const handleAudioCapture = async (audioBlob: Blob) => {
    const formData = new FormData();
    formData.append("file", audioBlob, "audio.wav");
    
    try {
      const response = await fetch("http://52.207.245.139/upload-audio", {
        method: "POST",
        body: formData,
      });
  
      const data = await response.json();
      if (data.transcript) {
        const messageId = Date.now().toString();
        setMessages(prev => [...prev, {
          id: messageId,
          content: data.transcript,
          type: "text",
          sender: "other",
          isTyping: true,
          displayedContent: ''
        }]);
        simulateTyping(data.transcript, messageId);
      }
    } catch (error) {
      console.error("Error uploading audio:", error);
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file && file.type.startsWith("image/")) {
      const imageUrl = URL.createObjectURL(file);
      
      const newImageMessage: Message = {
        id: Date.now().toString(),
        content: '',
        type: "image",
        sender: "user",
        imageUrl: imageUrl,
      };
      setMessages(prev => [...prev, newImageMessage]);

      const formData = new FormData();
      formData.append("file", file);
      
      try {
        const response = await fetch("http://52.207.245.139/upload-image", {
          method: "POST",
          body: formData,
        });

        const data = await response.json();
        if (data.analysis) {
          const messageId = Date.now().toString();
          setMessages(prev => [...prev, {
            id: messageId,
            content: data.analysis,
            type: "text",
            sender: "other",
            isTyping: true,
            displayedContent: ''
          }]);
          simulateTyping(data.analysis, messageId);
        }
      } catch (error) {
        console.error("Error uploading image:", error);
      }
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
                {message.type === 'text' && (
                  <p className="font-medium whitespace-pre-line">
                    {message.sender === 'other' 
                      ? (message.displayedContent || '') + (message.isTyping ? '▋' : '')
                      : message.content
                    }
                  </p>
                )}
                {message.type === 'image' && message.imageUrl && (
                  <img src={message.imageUrl} alt="Uploaded plant" className="max-w-full rounded" />
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
          <Button
            size="icon"
            variant="ghost"
            onClick={() => setShowAudioRecorder(!showAudioRecorder)}
          >
            <Mic className="h-4 w-4" />
          </Button>
          <Button size="icon" onClick={handleSendMessage}>
            <Send className="h-4 w-4" />
          </Button>
        </div>
        {showAudioRecorder && (
          <div className="mt-2">
            <AudioRecorder onAudioCapture={handleAudioCapture} />
          </div>
        )}
      </div>
    </div>
  );
}