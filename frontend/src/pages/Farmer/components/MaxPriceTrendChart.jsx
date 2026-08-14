import { motion } from "framer-motion";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import { FaChartLine, FaMapMarkerAlt } from "react-icons/fa";

function MaxPriceTrendChart({ t, history, empty, location }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.1 }}
      className="rounded-2xl bg-white/70 backdrop-blur-md border border-white/60 shadow-md p-5 md:p-6"
    >
      <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <FaChartLine className="text-2xl text-green-600" />
          <h3 className="text-lg font-bold text-gray-800">
            {t("maxPriceTrend")}
          </h3>
        </div>
        {!empty && location && (
          <span className="flex items-center gap-1.5 text-xs font-medium text-gray-500 bg-gray-50 px-3 py-1 rounded-full">
            <FaMapMarkerAlt className="text-green-600" />
            {location}
          </span>
        )}
      </div>

      {empty ? (
        <p className="text-gray-500 text-sm">{t("fillFormPrompt")}</p>
      ) : history.length === 0 ? (
        <p className="text-gray-500 text-sm">{t("noHistoryData")}</p>
      ) : (
        <div className="h-56 md:h-64 -ml-2">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={history}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 11, fill: "#6b7280" }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                tick={{ fontSize: 11, fill: "#6b7280" }}
                axisLine={false}
                tickLine={false}
                width={44}
              />
              <Tooltip
                contentStyle={{
                  borderRadius: 12,
                  border: "1px solid #d1fae5",
                  fontSize: 13,
                }}
                formatter={(value, name) => {
                  const label = name === "modalPrice" ? "Modal Price" : "Max Price";
                  return [`₹${value}`, label];
                }}
              />
              <Line
                type="monotone"
                dataKey="modalPrice"
                stroke="#16a34a"
                strokeWidth={2.5}
                dot={{ r: 3, fill: "#16a34a" }}
                activeDot={{ r: 5 }}
                name="modalPrice"
              />
              <Line
                type="monotone"
                dataKey="maxPrice"
                stroke="#dc2626"
                strokeWidth={2.0}
                dot={{ r: 2.5, fill: "#dc2626" }}
                activeDot={{ r: 4 }}
                name="maxPrice"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </motion.div>
  );
}

export default MaxPriceTrendChart;