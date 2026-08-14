import { useEffect, useRef, useState } from "react";
import { MapContainer, TileLayer, Marker, useMapEvents } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

// Fix default marker icon paths (Leaflet + bundlers issue)
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl:
    "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

function ClickHandler({ onPick }) {
  useMapEvents({
    click(e) {
      onPick(e.latlng.lat, e.latlng.lng);
    },
  });
  return null;
}

function DraggableMarker({ position, onDragEnd }) {
  const markerRef = useRef(null);

  const eventHandlers = {
    dragend() {
      const marker = markerRef.current;
      if (marker) {
        const { lat, lng } = marker.getLatLng();
        onDragEnd(lat, lng);
      }
    },
  };

  return (
    <Marker
      draggable
      eventHandlers={eventHandlers}
      position={position}
      ref={markerRef}
    />
  );
}

export default function LocationPicker({
  initialLat,
  initialLng,
  onConfirm,
  onClose,
  t,
}) {
  const [position, setPosition] = useState({
    lat: initialLat ? Number(initialLat) : 15.9129,
    lng: initialLng ? Number(initialLng) : 79.74,
  });
  const [resolving, setResolving] = useState(false);
  const [label, setLabel] = useState("");

  const reverseGeocode = async (lat, lng) => {
    setResolving(true);
    try {
      const res = await fetch(
        `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}&zoom=14&addressdetails=1`,
        { headers: { "Accept-Language": "en" } }
      );
      const data = await res.json();
      const addr = data.address || {};
      const village =
        addr.village || addr.hamlet || addr.town || addr.suburb || "";
      const mandal =
        addr.county || addr.state_district || addr.city_district || "";
      setLabel(
        [village, mandal].filter(Boolean).join(", ") ||
          data.display_name ||
          "Unknown location"
      );
      return { village, mandal, state: addr.state || "" };
    } catch (err) {
      console.error("Reverse geocoding failed:", err);
      setLabel("Could not resolve name");
      return { village: "", mandal: "", state: "" };
    } finally {
      setResolving(false);
    }
  };

  useEffect(() => {
    reverseGeocode(position.lat, position.lng);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleMove = async (lat, lng) => {
    setPosition({ lat, lng });
    await reverseGeocode(lat, lng);
  };

  const handleConfirm = async () => {
    const info = await reverseGeocode(position.lat, position.lng);
    onConfirm({
      latitude: position.lat,
      longitude: position.lng,
      label,
      ...info,
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-2xl overflow-hidden">
        <div className="flex items-center justify-between px-5 py-3 border-b">
          <h3 className="font-semibold text-gray-800">
            {t?.adjustLocation || "Adjust your location"}
          </h3>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-xl leading-none"
          >
            ×
          </button>
        </div>

        <div className="h-80 w-full">
          <MapContainer
            center={position}
            zoom={13}
            style={{ height: "100%", width: "100%" }}
          >
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            <ClickHandler onPick={handleMove} />
            <DraggableMarker position={position} onDragEnd={handleMove} />
          </MapContainer>
        </div>

        <div className="px-5 py-4 flex flex-col gap-3">
          <p className="text-sm text-gray-600">
            {resolving ? "Resolving location..." : label}
          </p>
          <p className="text-xs text-gray-400">
            {position.lat.toFixed(5)}, {position.lng.toFixed(5)}
          </p>
          <div className="flex justify-end gap-3">
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm rounded-lg border border-gray-300 text-gray-600 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              onClick={handleConfirm}
              className="px-4 py-2 text-sm rounded-lg bg-green-600 text-white hover:bg-green-700"
            >
              Confirm location
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}