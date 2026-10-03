import { useState } from "react";
import { ChatProvider, useChat } from "../context/ChatContext";
import { ConversationList } from "../features/chat/ConversationList";
import { ChatWindow } from "../features/chat/ChatWindow";
import styles from "./ChatPage.module.css";

function ChatPageInner() {
  const { conversations, activeConversationId, setActiveConversationId } = useChat();
  const [mobileShowWindow, setMobileShowWindow] = useState(false);

  const activeConversation = conversations.find((c) => c.id === activeConversationId) ?? null;

  function handleSelect(id: string) {
    setActiveConversationId(id);
    setMobileShowWindow(true);
  }

  return (
    <div className={styles.page}>
      <div className={[styles.sidebar, mobileShowWindow ? styles.sidebarHiddenMobile : ""].join(" ")}>
        <div className={styles.sidebarHeader}>
          <h1>Chat</h1>
        </div>
        <ConversationList conversations={conversations} activeId={activeConversationId} onSelect={handleSelect} />
      </div>
      <div className={[styles.windowWrap, mobileShowWindow ? "" : styles.windowHiddenMobile].join(" ")}>
        <ChatWindow conversation={activeConversation} onBack={() => setMobileShowWindow(false)} />
      </div>
    </div>
  );
}

export default function ChatPage() {
  return (
    <ChatProvider>
      <ChatPageInner />
    </ChatProvider>
  );
}
