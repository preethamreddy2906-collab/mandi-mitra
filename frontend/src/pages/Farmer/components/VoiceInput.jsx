import React, { useState, useRef, useEffect } from 'react';

const VoiceInput = ({ onTranscript, lang = 'te-IN' }) => {
  const [isListening, setIsListening] = useState(false);
  const recognitionRef = useRef(null);

  // Initialize SpeechRecognition instance once when the component mounts
  useEffect(() => {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      console.warn("SpeechRecognition API is not supported in this browser.");
      return;
    }

    console.log("Creating persistent SpeechRecognition instance...");
    const rec = new SpeechRecognition();
    rec.continuous = false;
    rec.interimResults = false;
    rec.lang = lang;

    // Attach listeners
    rec.onstart = () => {
      console.log("🎙️ SpeechRecognition: onstart fired.");
      setIsListening(true);
    };

    rec.onresult = (event) => {
      console.log("🎙️ SpeechRecognition: onresult fired.");
      if (event.results && event.results[0] && event.results[0][0]) {
        const transcriptText = event.results[0][0].transcript;
        console.log("Transcribed:", transcriptText);
        onTranscript(transcriptText);
      } else {
        console.warn("SpeechRecognition: Empty results received.");
      }
    };

    rec.onerror = (event) => {
      console.error("🎙️ SpeechRecognition: onerror occurred. Error code:", event.error);
      setIsListening(false);
    };

    rec.onend = () => {
      console.log("🎙️ SpeechRecognition: onend fired.");
      setIsListening(false);
    };

    recognitionRef.current = rec;

    // Cleanup on unmount
    return () => {
      if (recognitionRef.current) {
        console.log("Aborting SpeechRecognition instance due to component unmounting.");
        try {
          recognitionRef.current.abort();
        } catch (e) {
          console.error("Error during SpeechRecognition abort:", e);
        }
      }
    };
  }, []); // Empty dependencies array ensures initialization runs exactly once on mount

  // Sync lang changes without recreating the instance or losing listeners
  useEffect(() => {
    if (recognitionRef.current) {
      console.log(`Syncing SpeechRecognition language to current value: "${lang}"`);
      recognitionRef.current.lang = lang;
    }
  }, [lang]);

  const handleListen = () => {
    console.log("🎤 Mic button clicked!");

    if (!recognitionRef.current) {
      alert("Speech recognition is not supported in this browser or failed to initialize.");
      return;
    }

    if (isListening) {
      console.log("Stopping active listening session manually...");
      try {
        recognitionRef.current.stop();
      } catch (e) {
        console.error("Error stopping SpeechRecognition:", e);
      }
      setIsListening(false);
    } else {
      console.log("Starting new listening session...");
      try {
        recognitionRef.current.start();
      } catch (e) {
        console.error("Error starting SpeechRecognition. Attempting abort/restart recovery...", e);
        try {
          // If it was already starting or in an invalid state, abort it and try starting again
          recognitionRef.current.abort();
          setTimeout(() => {
            if (recognitionRef.current) {
              recognitionRef.current.start();
            }
          }, 150);
        } catch (err) {
          console.error("Failed to recover and start SpeechRecognition:", err);
        }
      }
    }
  };

  return (
    <button
      type="button"
      onClick={handleListen}
      className={`px-4 py-3.5 rounded-xl font-semibold transition-all duration-300 flex items-center justify-center min-w-[120px] cursor-pointer select-none ${
        isListening
          ? 'bg-red-500 text-white shadow-[0_0_15px_rgba(239,68,68,0.5)] animate-pulse'
          : 'bg-green-600 hover:bg-green-700 text-white shadow-sm hover:shadow-md'
      }`}
      style={{ pointerEvents: 'auto', zIndex: 10 }}
      title={isListening ? "Stop listening" : "Speak your query"}
    >
      {isListening ? (
        <span className="flex items-center gap-1.5 pointer-events-none">
          <span className="h-2.5 w-2.5 rounded-full bg-white animate-ping" />
          🛑 Stop
        </span>
      ) : (
        <span className="flex items-center gap-1.5 pointer-events-none">
          🎤 Speak
        </span>
      )}
    </button>
  );
};

export default VoiceInput;