import { useState, type KeyboardEvent } from "react";
import { Send } from "lucide-react";
import styles from "./MessageInput.module.css";

interface MessageInputProps {
  onSend: (texto: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export function MessageInput({ onSend, disabled, placeholder }: MessageInputProps) {
  const [value, setValue] = useState("");
  const isEmpty = value.trim().length === 0;

  function handleSend() {
    if (isEmpty || disabled) return; // HU016 - Escenario 2
    onSend(value);
    setValue("");
  }

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  return (
    <div className={styles.wrap}>
      <textarea
        className={styles.textarea}
        placeholder={placeholder ?? "Escribe un mensaje…"}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        rows={1}
        disabled={disabled}
      />
      <button className={styles.send} onClick={handleSend} disabled={isEmpty || disabled} aria-label="Enviar mensaje">
        <Send size={17} />
      </button>
    </div>
  );
}
