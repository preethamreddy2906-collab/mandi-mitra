import { useState } from "react";
import { motion } from "framer-motion";
import {
  FaSeedling,
  FaMapMarkerAlt,
  FaMapMarkedAlt,
  FaCalendarAlt,
  FaWeightHanging,
  FaMicrophone,
} from "react-icons/fa";
import VoiceInput from "./VoiceInput";

const STATE_DISTRICT_MAP = {
  "Andhra Pradesh": [
    "Alluri Sitharama Raju",
    "Anakapalli",
    "Ananthapuramu",
    "Annamayya",
    "Bapatla",
    "Chittoor",
    "Dr. B.R. Ambedkar Konaseema",
    "East Godavari",
    "Eluru",
    "Guntur",
    "Kakinada",
    "Krishna",
    "Kurnool",
    "Nandyal",
    "NTR",
    "Palnadu",
    "Parvathipuram Manyam",
    "Prakasam",
    "SPSR Nellore",
    "Srikakulam",
    "Sri Sathya Sai",
    "Tirupati",
    "Visakhapatnam",
    "Vizianagaram",
    "West Godavari",
    "YSR Kadapa"
  ]
};


const CROPS = [
  "Tomato",
  "Onion",
  "Potato",
  "Green Chilli",
  "Brinjal",
  "Cauliflower"
];

export {
  STATE_DISTRICT_MAP,
  CROPS,
  MARKET_OPTIONS,
};


const MARKET_OPTIONS = {
  Tomato: [
    "B.Kothakota H/Q Angallu",
    "Guramkonda Sub-yard of AMC Valmikipuram",
    "Kalikiri APMC",
    "Madanapalli APMC",
    "Mulakalacheruvu APMC",
    "Punganur APMC",
    "Valmikipuram APMC",
    "Palamaner APMC",
    "V. Kota Sub-yard of AMC Palamaneru",
    "Somala APMC",
  ],
  Onion: ["Kurnool APMC"],
  Potato: ["Palamaner APMC"],
  "Green Chilli": ["Palamaner APMC"],
  Brinjal: ["Palamaner APMC"],
  Cauliflower: ["Palamaner APMC"],
};



function FieldLabel({ icon, children }) {
  return (
    <label className="flex items-center gap-2 font-semibold text-gray-700 text-sm mb-1.5">
      <span className="text-green-600">{icon}</span>
      {children}
    </label>
  );
}

const selectClass =
  "w-full border-2 border-gray-200 rounded-xl px-4 py-3.5 text-base bg-white focus:outline-none focus:ring-4 focus:ring-green-100 focus:border-green-500 transition disabled:bg-gray-50 disabled:cursor-not-allowed";

function FarmerForm({ t, formData, onChange, onSubmit, loading }) {
  const [query, setQuery] = useState("");

  const availableMarkets = formData.crop
    ? MARKET_OPTIONS[formData.crop] || []
    : [];

  const langMapping = {
    Telugu: "te-IN",
    Hindi: "hi-IN",
    Tamil: "ta-IN",
    English: "en-IN",
  };
  const voiceLang = langMapping[formData.language] || "te-IN";

  return (
    <motion.div
      initial={{ opacity: 0, x: -16 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.4 }}
      className="rounded-2xl bg-white/70 backdrop-blur-md border border-white/60 shadow-lg p-5 md:p-7"
    >
      <h3 className="text-xl md:text-2xl font-bold text-gray-800 flex items-center gap-2 mb-5">
        <FaSeedling className="text-green-700" />
        {t("farmerDetails")}
      </h3>

      <div className="flex flex-col gap-4">
        <div>
          <FieldLabel icon={<FaMapMarkerAlt />}>{t("state")}</FieldLabel>
          <select
            name="state"
            value={formData.state}
            onChange={onChange}
            className={selectClass}
          >
            <option value="">{t("selectState")}</option>
            <option value="Andhra Pradesh">
              Andhra Pradesh
            </option>
          </select >
        </div >

        <div>
          <FieldLabel icon={<FaSeedling />}>{t("crop")}</FieldLabel>
          <select
            name="crop"
            value={formData.crop}
            onChange={onChange}
            className={selectClass}
          >
            <option value="">{t("selectCrop")}</option>
            {CROPS.map((crop) => (
              <option key={crop} value={crop}>
                {crop}
              </option>
            ))}
          </select>
        </div>

        <div>
          <FieldLabel icon={<FaMapMarkerAlt />}>{t("market")}</FieldLabel>
          <select
            name="market"
            value={formData.market}
            onChange={onChange}
            disabled={!formData.crop}
            className={selectClass}
          >
            <option value="">
              {formData.crop ? t("selectMarket") : t("selectCropFirst")}
            </option>
            {availableMarkets.map((market) => (
              <option key={market} value={market}>
                {market}
              </option>
            ))}
          </select>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <FieldLabel>{t("latitude")}</FieldLabel>

            <input
              type="number"
              step="any"
              name="latitude"
              value={formData.latitude}
              onChange={onChange}
              placeholder={`${t("example")} 13.552040`}
              className={selectClass}
            />
          </div>

          <div>
            <FieldLabel>{t("longitude")}</FieldLabel>

            <input
              type="number"
              step="any"
              name="longitude"
              value={formData.longitude}
              onChange={onChange}
              placeholder={`${t("example")} 78.505798`}
              className={selectClass}
            />
          </div>
        </div>

        <div>
          <FieldLabel>{t("language")}</FieldLabel>

          <select
            name="language"
            value={formData.language}
            onChange={onChange}
            className={selectClass}
          >
            <option value="">
              {t("selectLanguage")}
            </option>

            <option value="English">English</option>
            <option value="Tamil">தமிழ்</option>
            <option value="Telugu">తెలుగు</option>
            <option value="Hindi">हिन्दी</option>
          </select>
        </div>

        <div>
          <FieldLabel icon={<FaMicrophone />}>{t("voiceQuery") || "Ask a Custom Question"}</FieldLabel>
          <div className="flex gap-2 items-center w-full relative z-10">
            <input
              type="text"
              name="query"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Speak or type your question..."
              className="flex-grow min-w-0 border-2 border-gray-200 rounded-xl px-4 py-3.5 text-base bg-white focus:outline-none focus:ring-4 focus:ring-green-100 focus:border-green-500 transition disabled:bg-gray-50 disabled:cursor-not-allowed"
            />
            <VoiceInput
              lang={voiceLang}
              onTranscript={(text) => setQuery(text)}
            />
          </div>
        </div>

      </div >

      <button
        onClick={onSubmit}
        disabled={loading}
        className="mt-6 w-full bg-green-700 hover:bg-green-800 disabled:bg-green-400 disabled:cursor-not-allowed text-white px-8 py-4 rounded-xl font-bold text-lg transition-colors duration-200 shadow-md hover:shadow-lg active:scale-[0.98]"
      >
        {loading ? "…" : t("getAdvisory")}
      </button>
    </motion.div >
  );
}

export default FarmerForm;