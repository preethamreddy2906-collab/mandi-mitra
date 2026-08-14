function parseNumber(value, fallback) {
  if (value === undefined || value === null) return fallback;
  const num = parseFloat(String(value).replace(/[^\d.]/g, ""));
  return Number.isFinite(num) ? num : fallback;
}


function classifyRainfall(rainfallRaw) {
  const percent = parseNumber(rainfallRaw, 0);
  if (percent >= 50) return "rainy";
  if (percent >= 20) return "cloudy";
  return "sunny";
}


function inferDecision(riskLevel, trend, recommendationText) {
  const text = (recommendationText || "").toLowerCase();
  if (text.includes("sell")) return "sell";
  if (text.includes("wait")) return "wait";
  if (text.includes("hold")) return "hold";

  if (riskLevel === "High") return "wait";
  if (trend === "Increasing" && riskLevel !== "High") return "sell";
  if (trend === "Decreasing") return "wait";
  return "hold";
}

export function normalizeAdvisory(raw, formData) {
  if (!raw) return null;

  const modalPrice = parseNumber(
    raw.market?.modal_price ?? raw.market?.current_price,
    2200
  );
  const highestPrice = parseNumber(raw.market?.max_price, modalPrice * 1.08);
  const lowestPrice = parseNumber(raw.market?.min_price, modalPrice * 0.9);
  const trend = raw.market?.trend ?? "Stable";
  const riskLevel = raw.risk_level ?? "Low";
  const reasons =
    raw.reasons ??
    [
      `${formData.crop || "Crop"} prices are trending ${(raw.market?.trend || trend).toLowerCase()
      } at ${formData.market || "your selected market"} in ${formData.district || "your district"
      }.`,
      `Weather conditions (${raw.weather?.rainfall ?? "low rainfall"
      }) should be considered before selling.`,
      `Market prices are based on the selected market.`,
    ];



  return {
    weather: {
      temperature: raw.weather?.temperature ?? "—",
      humidity: raw.weather?.humidity ?? "—",
      rainfall: raw.weather?.rainfall ?? "—",
      windSpeed: raw.weather?.wind_speed ?? "12 km/h",
      condition: classifyRainfall(raw.weather?.rainfall),
    },
    market: {
      marketName:
        raw.market?.market_name ||
        formData.market ||
        "Nearest Mandi",
      modalPrice: `₹${Math.round(modalPrice)}`,
      highestPrice: `₹${Math.round(highestPrice)}`,
      lowestPrice: `₹${Math.round(lowestPrice)}`,
      modalPriceValue: modalPrice,
      highestPriceValue: highestPrice,
      lowestPriceValue: lowestPrice,
      arrivalDate:
        raw.market?.arrival_date ?? new Date().toLocaleDateString(),
      trend,
    },
    crop: {
      harvestTip: raw.crop?.harvest_tip ?? "Harvest when grains reach full maturity.",
      storageTip: raw.crop?.storage_tip ?? "Store in a cool, dry, ventilated space.",
      bestSellingPeriod: raw.crop?.best_selling_period ?? "Within the next 2 weeks",
      fertilizerAdvice:
        raw.crop?.fertilizer_advice ?? "Apply balanced NPK as per soil test results.",
      waterRequirement:
        raw.crop?.water_requirement ?? "Moderate — irrigate every 5-7 days.",
    },
    recommendation: raw.recommendation ?? "Recommendation unavailable right now.",
    reasons,
    confidence: raw.confidence ?? 82,
    riskLevel,
    decision: inferDecision(riskLevel, trend, raw.recommendation),
    audioBase64: raw.audio_base64,
  };
}