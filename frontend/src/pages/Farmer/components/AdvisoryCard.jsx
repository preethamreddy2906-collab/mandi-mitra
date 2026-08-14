import { motion } from "framer-motion";
import ReactMarkdown from "react-markdown";
import {
  FaRobot,
  FaVolumeUp,
  FaFilePdf,
  FaPrint,
  FaCheckCircle,
} from "react-icons/fa";
import jsPDF from "jspdf";
import { useRef, useEffect } from "react";

const RISK_STYLES = {
  Low: "bg-green-100 text-green-700 border-green-200",
  Medium: "bg-amber-100 text-amber-700 border-amber-200",
  High: "bg-red-100 text-red-700 border-red-200",
};

function ConfidenceMeter({ value }) {
  return (
    <div className="flex items-center gap-2.5">
      <div className="flex-1 h-2.5 rounded-full bg-white/30 overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${value}%` }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className="h-full rounded-full bg-white"
        />
      </div>
      <span className="text-sm font-bold">{value}%</span>
    </div>
  );
}

function handleReadAloud(advisory, crop, language) {
  if (!("speechSynthesis" in window)) {
    alert("Text-to-speech is not supported in this browser.");
    return;
  }
  const utterance = new SpeechSynthesisUtterance(
    `${crop} advisory. ${advisory.recommendation}. Confidence ${advisory.confidence} percent. Risk level ${advisory.riskLevel}.`
  );
  const langMap = {
    English: "en-IN",
    Tamil: "ta-IN",
    Hindi: "hi-IN",
    Telugu: "te-IN",
  };
  utterance.lang = langMap[language] || "en-IN";
  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(utterance);
}

function handleDownloadPdf(advisory, formData) {
  const doc = new jsPDF();
  let y = 20;
  doc.setFontSize(18);
  doc.text("MandiMitra - AI Advisory Report", 14, y);
  y += 10;
  doc.setFontSize(11);
  doc.text(`Crop: ${formData.crop}  |  Market: ${formData.market}  |  State: ${formData.state}`, 14, y);
  y += 10;
  doc.setFontSize(14);
  doc.text("Recommendation", 14, y);
  y += 7;
  doc.setFontSize(11);
  const recLines = doc.splitTextToSize(advisory.recommendation, 180);
  doc.text(recLines, 14, y);
  y += recLines.length * 6 + 6;

  doc.setFontSize(14);
  doc.text("Reasons", 14, y);
  y += 7;
  doc.setFontSize(11);
  advisory.reasons.forEach((reason) => {
    const lines = doc.splitTextToSize(`- ${reason}`, 180);
    doc.text(lines, 14, y);
    y += lines.length * 6;
  });
  y += 6;

  doc.setFontSize(14);
  doc.text(`Confidence Score: ${advisory.confidence}%`, 14, y);
  y += 8;
  doc.text(`Risk Level: ${advisory.riskLevel}`, 14, y);

  doc.save(`MandiMitra_Advisory_${formData.crop || "crop"}.pdf`);
}

function AdvisoryCard({ t, advisory, formData, empty, onAskAgain }) {
  const audioRef = useRef(null);

  useEffect(() => {
    if (!empty && advisory?.audioBase64) {
      const audioUrl = `data:audio/mp3;base64,${advisory.audioBase64}`;
      const audio = new Audio(audioUrl);
      audioRef.current = audio;

      audio.play().catch((err) => {
        console.log("Autoplay was prevented by browser policy. Interaction required.", err);
      });
    }

    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
    };
  }, [advisory, empty]);

  const handlePlayAdvisoryAudio = () => {
    if (advisory?.audioBase64) {
      if (audioRef.current) {
        if (audioRef.current.ended) {
          audioRef.current.currentTime = 0;
          audioRef.current.play().catch((err) => {
            console.error("Audio playback failed:", err);
          });
          return;
        }
        if (!audioRef.current.paused) {
          audioRef.current.pause();
          return;
        }
        audioRef.current.play().catch((err) => {
          console.error("Audio playback failed:", err);
        });
      } else {
        const audioUrl = `data:audio/mp3;base64,${advisory.audioBase64}`;
        const audio = new Audio(audioUrl);
        audioRef.current = audio;
        audio.play().catch((err) => {
          console.error("Audio playback failed:", err);
        });
      }
    } else {
      handleReadAloud(advisory, formData.crop, formData.language);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, delay: 0.15 }}
      className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-emerald-700 via-green-700 to-teal-700 text-white shadow-xl p-6 md:p-8"
    >
      <div className="absolute -top-10 -right-10 h-44 w-44 rounded-full bg-white/10 blur-2xl" />

      <div className="relative flex items-center gap-3 mb-5">
        <div className="h-11 w-11 rounded-xl bg-white/15 flex items-center justify-center">
          <FaRobot className="text-xl" />
        </div>
        <h3 className="text-xl md:text-2xl font-bold">
          {t("aiRecommendation")}
        </h3>
      </div>

      {empty ? (
        <p className="relative text-white/80 text-sm md:text-base">
          {t("fillFormPrompt")}
        </p>
      ) : (
        <div className="relative">
          <div className="prose prose-invert max-w-none text-white">
            <ReactMarkdown>
              {advisory.recommendation}
            </ReactMarkdown>
          </div>

          {advisory.reasons?.length > 0 && (
            <div className="mt-5">
              <p className="text-sm font-semibold text-white/80 mb-2">
                {t("reasons")}
              </p>
              <ul className="flex flex-col gap-2">
                {advisory.reasons.map((reason, i) => (
                  <li
                    key={i}
                    className="flex items-start gap-2 text-sm md:text-base text-white/95"
                  >
                    <FaCheckCircle className="mt-1 text-lime-300 shrink-0" />
                    {reason}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="mt-6 grid sm:grid-cols-2 gap-4">
            <div className="bg-white/10 rounded-xl p-4">
              <p className="text-xs font-semibold text-white/70 mb-2">
                {t("confidence")}
              </p>
              <ConfidenceMeter value={advisory.confidence} />
            </div>
            <div className="bg-white/10 rounded-xl p-4 flex items-center justify-between">
              <p className="text-xs font-semibold text-white/70">
                {t("riskLevel")}
              </p>
              <span
                className={`px-3 py-1 rounded-full text-xs font-bold border ${RISK_STYLES[advisory.riskLevel] || RISK_STYLES.Medium
                  }`}
              >
                {advisory.riskLevel}
              </span>
            </div>
          </div>

          <div className="mt-6 flex flex-wrap gap-3">
            <button
              onClick={handlePlayAdvisoryAudio}
              className="flex items-center gap-2 bg-white/15 hover:bg-white/25 px-4 py-2.5 rounded-xl text-sm font-semibold transition-colors"
            >
              <FaVolumeUp /> {advisory?.audioBase64 ? "🔊 Listen to Advisory" : t("readAloud")}
            </button>
            <button
              onClick={() => handleDownloadPdf(advisory, formData)}
              className="flex items-center gap-2 bg-white/15 hover:bg-white/25 px-4 py-2.5 rounded-xl text-sm font-semibold transition-colors"
            >
              <FaFilePdf /> {t("downloadPdf")}
            </button>
            <button
              onClick={() => window.print()}
              className="flex items-center gap-2 bg-white/15 hover:bg-white/25 px-4 py-2.5 rounded-xl text-sm font-semibold transition-colors"
            >
              <FaPrint /> {t("print")}
            </button>
            <button
              onClick={onAskAgain}
              className="flex items-center gap-2 bg-white text-green-700 hover:bg-green-50 px-4 py-2.5 rounded-xl text-sm font-bold transition-colors ml-auto"
            >
              {t("askAgain")}
            </button>
          </div>
        </div>
      )}
    </motion.div>
  );
}

export default AdvisoryCard;