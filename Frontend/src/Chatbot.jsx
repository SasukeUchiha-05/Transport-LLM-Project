import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Input, Button, Avatar, Switch } from '@material-tailwind/react';
import './Chatbot.css'; // Ensure you import your CSS file
import Loading from './Loading';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const Chatbot = () => {
  const [sessionId, setSessionId] = useState(null);
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [darkMode, setDarkMode] = useState(true);
  const chatWindowRef = useRef(null);

  useEffect(() => {
    startNewSession();
    fetchSessions();
    setDarkMode(true); // Toggle dark mode by default
  }, []);

  useEffect(() => {
    if (chatWindowRef.current) {
      chatWindowRef.current.scrollTop = chatWindowRef.current.scrollHeight;
    }
  }, [messages]);

  const fetchSessions = async () => {
    try {
      const response = await axios.post('http://localhost:8000/chats', { UID: localStorage.getItem("UID") });
      setSessions(response.data);
    } catch (error) {
      console.error('Error fetching sessions:', error);
    }
  };

  const startNewSession = async () => {
    try {
      const response = await axios.post('http://localhost:8000/start_session', { UID: localStorage.getItem("UID") });
      setSessionId(response.data.session_id);
      setMessages([]);
    } catch (error) {
      console.error('Error starting new session:', error);
    }
    fetchSessions();
  };

  const selectSession = async (session) => {
    setSessionId(session.session_id);
    console.log(session.session_id);
    try {
      const response = await axios.get(`http://localhost:8000/chats/${session.session_id}`);
      setMessages(response.data.messages);
    } catch (error) {
      console.error('Error selecting session:', error);
    }
  };

  const handleQuery = async () => {
    if (!query.trim()) return;
    setLoading(true);
    const newMessage = { user: query };
    setMessages((prevMessages) => [...prevMessages, newMessage, { loading: true }]);
    setQuery('');

    try {
      const response = await axios.post('http://localhost:8000/query', {
        query,
        session_id: sessionId,
      });
      const botResponse = { chatbot: response.data.response };
      setMessages((prevMessages) => {
        const updatedMessages = [...prevMessages];
        updatedMessages.pop(); // Remove the loading message
        return [...updatedMessages, botResponse];
      });
    } catch (error) {
      console.error('Error handling query:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleDarkMode = () => {
    setDarkMode((prevDarkMode) => !prevDarkMode);
  };

  const logout = () => {
    localStorage.removeItem("UID");
    alert("Logout Successful"); // Remove the user's session or token
    window.location.href = '/login'; // Redirect to login page
  };

  return (
    <div className={`flex h-screen w-screen items-center justify-center ${darkMode ? 'dark' : ''}`}>
      <div className="w-full h-full flex flex-col">
        <div className="flex justify-between items-center p-4 bg-gray-800 text-white">
          <h2 className="text-xl font-bold">RTAbot</h2>
          <div className="flex items-center">
            <Switch
              id="custom-switch-component"
              checked={darkMode}
              onChange={toggleDarkMode}
              name="darkModeSwitch"
              color="default"
              className="h-full w-full checked:bg-[#2ec946]"
              ripple={false}
              containerProps={{
                className: "w-11 h-6",
              }}
              circleProps={{
                className: "before:hidden left-0.5 border-none",
              }}
            />
            <div className='px-1'></div>
            {darkMode ? 'Dark Mode' : 'Light Mode'}
          </div>
          <Button
            color="red"
            buttonType="filled"
            onClick={logout}
            ripple="light"
            className="rounded"
          >
            Logout
          </Button>
        </div>
        <div className="flex flex-1 overflow-hidden">
          <div className="w-1/4 bg-gray-100 dark:bg-gray-700 flex flex-col">
            <div className="flex-1 overflow-y-auto p-4">
              {sessions.map((session) => (
                <div key={session.session_id}>
                  <div
                    onClick={() => selectSession(session)}
                    className={`p-4 mb-2 cursor-pointer rounded ${session.session_id === sessionId ? 'bg-blue-200 dark:bg-blue-600' : 'hover:bg-gray-200 dark:hover:bg-gray-600'
                      }`}
                    style={{ color: darkMode ? 'white' : 'black' }}
                  >
                    {session.messages[0] ? session.messages[0]['user'] : "New Chat Session"}
                  </div>
                </div>
              ))}
            </div>
            <div className="p-4">
              <Button
                color="blue"
                onClick={startNewSession}
                ripple="light"
                className="w-full"
              >
                Start New Session
              </Button>
            </div>
          </div>
          <div className="flex-1 flex flex-col bg-white dark:bg-gray-900">
            <div className="flex-1 p-4 overflow-y-auto" ref={chatWindowRef}>
              {messages.map((message, index) => (
                <div key={index} className="mb-4">
                  {message.user && (
                    <div className="flex justify-end mb-2 px-6">
                      <div className="bg-blue-500 text-white rounded-lg py-2 px-4 max-w-xs">
                        <strong>User:</strong> {message.user}
                      </div>
                      <div className='px-1'></div>
                      <Avatar src="data:image/png;base64,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" alt="avatar" />
                    </div>
                  )}
                  {message.chatbot && (
                    <div className="flex justify-start mb-2">
                      <Avatar src="https://img.freepik.com/free-vector/chatbot-chat-message-vectorart_78370-4104.jpg?size=338&ext=jpg&ga=GA1.1.2116175301.1719100800&semt=ais_user" alt="avatar" />
                      {/* <div className='px-1'></div> */}
                      <div className="bg-gray-200 text-gray-800 rounded-lg py-2 px-4 max-w-xl dark:bg-gray-900 dark:text-gray-100">
                        <strong>Bot:</strong>
                        <div className="markdown-body">
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {message.chatbot}
                          </ReactMarkdown>
                        </div>
                      </div>
                    </div>
                  )}
                  {message.loading && (
                    <div className="flex justify-start mb-2 items-center">
                      {/* <Avatar src="https://img.freepik.com/free-vector/chatbot-chat-message-vectorart_78370-4104.jpg?size=338&ext=jpg&ga=GA1.1.2116175301.1719100800&semt=ais_user" alt="avatar" /> */}
                      <div className='px-1'></div>
                      <Loading />
                    </div>
                  )}
                </div>
              ))}
              <div ref={chatWindowRef}></div>
            </div>
            <div className="p-4 border-t border-gray-300 dark:border-gray-600">
              <div className="flex items-center">
                <Input
                  label='Enter Query'
                  color={darkMode ? 'white' : 'blue'}
                  type="text"
                  placeholder="Ask a question..."
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleQuery()}
                  disabled={loading || !sessionId}
                  className="flex-1 px-3 py-2 rounded-l dark:bg-gray-600 dark:text-white"
                />
                <Button
                  color="blue"
                  onClick={handleQuery}
                  disabled={loading || !sessionId}
                  ripple="light"
                  className="rounded-r"
                >
                  Send
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Chatbot;
