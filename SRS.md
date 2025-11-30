# Software Requirements Specification (SRS)
## Transport-LLM-Project

**Version**: 2.0
**Date**: 2025-11-30

---

## CHAPTER 1
### 1. INTRODUCTION

#### 1.1 Purpose of the project
The purpose of this project is to develop a **Transport-LLM-Project**, a web-based chatbot application designed to answer transportation-related queries. This system aims to provide users with accurate, context-aware, and real-time information about transportation schedules, routes, and booking procedures by leveraging advanced Large Language Model (LLM) capabilities and Retrieval-Augmented Generation (RAG).

#### 1.2 Problem with Existing Systems
Existing transportation information systems often suffer from:
- **Fragmented Information**: Data is scattered across multiple websites and formats.
- **Static Responses**: Traditional chatbots rely on rigid decision trees and cannot handle complex natural language queries.
- **Lack of Context**: Standard search engines may provide generic links rather than direct answers.
- **Outdated Data**: Pre-trained models may not have access to the latest schedules or policy changes.

#### 1.3 Proposed System
The proposed system addresses these issues by:
- **Unified Interface**: A single chat interface for all transportation queries.
- **Natural Language Processing**: Using Google's Gemini LLM to understand and respond to complex user questions.
- **RAG Architecture**: Retrieving relevant documents from a local knowledge base (FAISS) to ground answers in fact.
- **Real-time Web Search**: Integrating DuckDuckGo to fetch the latest links and information when the knowledge base is insufficient.

#### 1.4 Scope of the Project
The scope of the **Transport-LLM-Project** includes:
- Developing a **FastAPI** backend to handle API requests and business logic.
- Creating a **React** frontend for a responsive and intuitive user experience.
- Implementing a **RAG pipeline** using FAISS and HuggingFace embeddings.
- Integrating **Google GenAI** for response generation.
- Managing user sessions and chat history using **MongoDB**.

#### 1.5 Architecture Diagram
*(Conceptual Description)*
The system follows a client-server architecture:
1.  **Client (Frontend)**: React application sends user queries to the backend.
2.  **Server (Backend)**: FastAPI receives the query.
3.  **Retrieval**: The system searches the FAISS vector database for relevant context.
4.  **Generation**: The system constructs a prompt with the query and context, sending it to the Google Gemini API.
5.  **Response**: The LLM generates an answer, which is sent back to the client.
6.  **Storage**: Chat history is saved in MongoDB.

---

## CHAPTER 2
### 2. LITERATURE SURVEY

The development of the Transport-LLM-Project draws upon recent advancements in Natural Language Processing (NLP) and Information Retrieval.

**Large Language Models (LLMs)**: Models like GPT-4 and Gemini have revolutionized NLP by demonstrating human-like understanding and generation capabilities. However, they suffer from "hallucinations" and a lack of up-to-date knowledge.

**Retrieval-Augmented Generation (RAG)**: To mitigate LLM limitations, Lewis et al. (2020) proposed RAG, which combines a pre-trained generator with a retrieval component. This allows the model to access external knowledge bases, significantly improving factual accuracy.

**Vector Databases**: Technologies like FAISS (Facebook AI Similarity Search) enable efficient similarity search in high-dimensional spaces, making it possible to retrieve relevant document chunks in milliseconds.

**Chatbot Interfaces**: Modern chatbots have evolved from rule-based systems to conversational agents. Frameworks like React allow for dynamic, responsive interfaces that enhance user engagement.

---

## CHAPTER 3
### 3. SOFTWARE REQUIREMENT SPECIFICATION

#### 3.1 Introduction to SRS
This section outlines the specific requirements for the Transport-LLM-Project, ensuring that the final product meets user needs and system constraints.

#### 3.2 Role of SRS
The SRS serves as a blueprint for developers, testers, and stakeholders. It minimizes communication gaps and provides a baseline for validation and verification.

#### 3.3 Requirements Specification Document
This document details the functional and non-functional requirements, acting as the primary reference for the project's development lifecycle.

#### 3.4 Functional Requirements
1.  **User Authentication**: Users must register and login to access the system.
2.  **Query Processing**: The system shall accept natural language queries.
3.  **Context Retrieval**: The system shall retrieve relevant documents using FAISS.
4.  **Answer Generation**: The system shall generate answers using Google GenAI.
5.  **Web Search**: The system shall perform web searches if requested by the user.
6.  **History Management**: The system shall save and display past chat sessions.

#### 3.5 Non-Functional Requirements
1.  **Usability**: The interface should be intuitive and support dark/light modes.
2.  **Scalability**: The backend should handle multiple concurrent users.
3.  **Maintainability**: The code should be modular and well-documented.

#### 3.6 Performance Requirements
- **Latency**: Responses should be generated within 5-10 seconds.
- **Availability**: The system should be available 99.9% of the time during operation hours.

#### 3.7 Software Requirements
- **Operating System**: Windows/Linux/MacOS
- **Language**: Python 3.8+, JavaScript (Node.js)
- **Database**: MongoDB
- **Libraries**: FastAPI, LangChain, FAISS, React, Tailwind CSS

#### 3.8 Hardware Requirements
- **Processor**: Intel Core i5 or equivalent (for local development).
- **RAM**: 8GB minimum (16GB recommended for running local embeddings).
- **Storage**: 500MB for application code and dependencies.
- **Network**: Stable internet connection for API access.

---

## CHAPTER 4
### 4. SYSTEM DESIGN

#### 4.1 Introduction to UML
Unified Modeling Language (UML) is a standard way to visualize the design of a system. (UML diagrams are omitted as per instruction).

#### 4.2 UML Diagrams
*(Ignored as per instruction)*

#### 4.3 TECHNOLOGIES USED
- **Frontend**: React, Vite, Tailwind CSS, Material-Tailwind.
- **Backend**: Python, FastAPI, Uvicorn.
- **AI/ML**: Google Gemini API, HuggingFace Embeddings, FAISS.
- **Database**: MongoDB (pymongo).
- **Tools**: VS Code, Git, Postman.

---

## CHAPTER 5
### 5. IMPLEMENTATION

#### 5.1 Setting up connections with Backend and Frontend
The implementation begins with setting up the communication channel between the React frontend and the FastAPI backend.
- **CORS Configuration**: The FastAPI app is configured with `CORSMiddleware` to allow requests from the frontend origin.
- **API Endpoints**: RESTful endpoints like `/query`, `/login`, and `/chats` are defined to handle specific client requests.

#### 5.2 Coding the logic
The core logic involves several key components:
- **RAG Pipeline (`rag.py`)**: This module initializes the FAISS index and the Google GenAI client. It handles the retrieval of context based on vector similarity and constructs the prompt for the LLM.
- **Database Logic (`database.py`)**: This module manages the connection to MongoDB, handling user registration, authentication, and the storage/retrieval of chat logs.
- **Web Search**: A fallback mechanism using `duckduckgo_search` is implemented to fetch real-time links when the user explicitly asks for sources.

#### 5.3 Connecting the dashboard
The frontend dashboard is built using React components:
- **Chat Interface**: A scrollable chat window displays the conversation history.
- **Session Sidebar**: A sidebar lists previous chat sessions, allowing users to switch contexts easily.
- **State Management**: React `useState` and `useEffect` hooks manage the application state, including the current query, chat history, and loading status.

#### 5.4 Screenshots
*(Placeholders for project screenshots)*
- **Login Screen**: Shows the user authentication form.
- **Chat Interface**: Displays the main chat window with a user query and bot response.
- **Sidebar**: Shows the list of saved sessions.

#### 5.5 UI Screenshots
*(Placeholders for specific UI elements)*
- **Dark Mode**: Demonstrates the application's appearance in dark mode.
- **Mobile View**: Shows the responsive layout on a smaller screen.

---

## CHAPTER 6
### 6. SOFTWARE TESTING

#### 6.1 Introduction
Software testing is a critical phase to ensure the system meets the specified requirements and is free of defects.

#### 6.1.1 Testing Objectives
- To verify that all functional requirements are met.
- To ensure the system handles errors and edge cases gracefully.
- To validate the accuracy of the RAG responses.

#### 6.1.2 Testing Strategies
- **Unit Testing**: Testing individual components (e.g., database connection, API endpoints) in isolation.
- **Integration Testing**: Verifying that the frontend and backend communicate correctly.
- **System Testing**: Testing the complete application flow from login to query generation.

#### 6.1.3 System Evaluation
The system is evaluated based on response accuracy, latency, and user satisfaction. Initial tests show that the RAG implementation significantly improves answer relevance compared to a standard LLM.

#### 6.2 Testing New System
The new system was tested in a local environment. Key scenarios included:
- Registering a new user.
- Asking a question present in the knowledge base.
- Asking a question requiring web search.
- Switching between chat sessions.

#### 6.3 Test Cases

| Test Case ID | Description | Expected Result | Actual Result | Status |
| :--- | :--- | :--- | :--- | :--- |
| TC-01 | User Registration | User created in DB | User created | Pass |
| TC-02 | User Login | Token/UID returned | UID returned | Pass |
| TC-03 | Send Query | Bot responds with text | Bot responded | Pass |
| TC-04 | Web Search Request | Links provided in answer | Links provided | Pass |
| TC-05 | Load Chat History | Previous chats displayed | Chats displayed | Pass |

---

## CONCLUSION
The **Transport-LLM-Project** successfully demonstrates the power of Retrieval-Augmented Generation in creating a domain-specific chatbot. By combining the reasoning capabilities of Google's Gemini with a curated knowledge base, the system provides accurate and helpful responses to transportation queries. The modern React frontend ensures a seamless user experience, while the robust FastAPI backend handles complex logic efficiently.

---

## FUTURE ENHANCEMENTS
- **Voice Support**: Adding speech-to-text and text-to-speech capabilities for hands-free interaction.
- **Multi-modal Support**: Allowing users to upload images (e.g., tickets, maps) for analysis.
- **Admin Dashboard**: Creating a dedicated interface for managing the knowledge base and viewing system analytics.
- **Deployment**: Deploying the application to a cloud platform (e.g., AWS, Vercel) for public access.

---

## REFERENCES
1.  Lewis, P., et al. (2020). "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks". NeurIPS.
2.  FastAPI Documentation. https://fastapi.tiangolo.com/
3.  React Documentation. https://reactjs.org/
4.  Google AI Studio. https://ai.google.dev/
5.  FAISS Documentation. https://github.com/facebookresearch/faiss

## BIBLIOGRAPHY
- "Building LLM Applications" by O'Reilly Media.
- "Modern Full-Stack Development" by Apress.
