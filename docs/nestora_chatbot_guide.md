# Frontend Integration Guide — Nestora Assistant AI Chatbot

> **API Endpoint:** `POST /api/v1/public/chat/message`  
> **Status:** ✅ Live on Production (Render)  
> **Auth Required:** ❌ No (Publicly available to visitors, students, and admins)

---

## 🏗️ How it Works

The chatbot UI built by the frontend team can now be connected to our backend AI service. When a user enters a question:
1. The frontend calls the `POST /api/v1/public/chat/message` endpoint with the user's text message.
2. The backend queries Google's Gemini 1.5 Flash AI model with platform instructions.
3. The backend returns a real-time, context-aware smart response to show in the chat window.

---

## 📡 API Details

### Request
```http
POST /api/v1/public/chat/message
Content-Type: application/json

{
  "message": "How do I pay my hostel rent?"
}
```

### Response (200 OK)
```json
{
  "reply": "To pay your rent, go to the Student Dashboard, click on the 'Payments' tab, and click the 'Pay' button next to your active booking. You can complete the transaction online using Razorpay."
}
```

---

## 💻 Sample React Integration Code

Replace your static button-click handlers and mock answers in the Chatbot component with this API call:

```javascript
import React, { useState } from 'react';

const NestoraChatbot = () => {
  const [messages, setMessages] = useState([
    { sender: 'bot', text: 'Hello 👋 Welcome to Hostel Management System. How can I help you today?' }
  ]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSendMessage = async (textToSend) => {
    if (!textToSend.trim()) return;

    // Add user message to UI
    setMessages(prev => [...prev, { sender: 'user', text: textToSend }]);
    setInputText('');
    setIsLoading(true);

    try {
      const response = await fetch('https://hostel-final-cqes.onrender.com/api/v1/public/chat/message', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: textToSend }),
      });

      if (!response.ok) {
        throw new Error('Network response was not ok');
      }

      const data = await response.json();
      
      // Add AI reply to UI
      setMessages(prev => [...prev, { sender: 'bot', text: data.reply }]);
    } catch (error) {
      console.error('Chat error:', error);
      setMessages(prev => [...prev, { sender: 'bot', text: 'Sorry, I am offline right now. Please try again later.' }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="chatbot-window">
      {/* Messages list */}
      <div className="messages-container">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.sender}`}>
            {msg.text}
          </div>
        ))}
        {isLoading && <div className="message bot loading">Nestora is typing...</div>}
      </div>

      {/* Input box */}
      <div className="input-container">
        <input 
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder="Ask another question..."
          onKeyPress={(e) => e.key === 'Enter' && handleSendMessage(inputText)}
          disabled={isLoading}
        />
        <button onClick={() => handleSendMessage(inputText)} disabled={isLoading}>
          Send
        </button>
      </div>

      {/* Suggestion Chips */}
      <div className="chips">
        <button onClick={() => handleSendMessage("Fees & Payment")}>Fees & Payment</button>
        <button onClick={() => handleSendMessage("Room Allocation")}>Room Allocation</button>
        <button onClick={() => handleSendMessage("Complaints")}>Complaints</button>
      </div>
    </div>
  );
};
```

---

## 🧪 Quick Test in Swagger Docs
You can test this endpoint directly in the Swagger UI:
👉 `https://hostel-final-cqes.onrender.com/docs#/public/chat_with_assistant_api_v1_public_chat_message_post`
