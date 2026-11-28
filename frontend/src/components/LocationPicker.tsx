import React, { useState, useEffect, useRef, useId } from "react";
import { m, AnimatePresence } from "motion/react";
import {
  MapPin,
  LocateFixed,
  Search,
  X,
  Loader2,
  AlertCircle,
  Building,
} from "lucide-react";
import type {
  ActiveLocation,
  LocationSearchResult,
  ReverseGeocodeResult,
} from "../api/types";

export interface LocationPickerProps {
  activeLocation: ActiveLocation | null;
  stationDistanceKm?: number;
  stationStatus?: "live" | "modelled_live" | "stale";
  onSelectLocation: (loc: ActiveLocation) => void;
  isLoading?: boolean;
  gate?: boolean;
}

const QUICK_CITIES: Array<{
  name: string;
  state: string;
  lat: number;
  lon: number;
}> = [
  { name: "Delhi", state: "Central Delhi", lat: 28.6139, lon: 77.209 },
  { name: "Noida", state: "Sector 62", lat: 28.5355, lon: 77.391 },
  { name: "Gurugram", state: "Cyber City", lat: 28.4595, lon: 77.0266 },
  { name: "Mumbai", state: "Andheri / Bandra", lat: 19.076, lon: 72.8777 },
  { name: "Kolkata", state: "Salt Lake", lat: 22.5726, lon: 88.3639 },
  { name: "Bengaluru", state: "Koramangala", lat: 12.9716, lon: 77.5946 },
];

export const LocationPicker: React.FC<LocationPickerProps> = ({
  activeLocation,
  stationDistanceKm,
  stationStatus,
  onSelectLocation,
  isLoading = false,
  gate = false,
}) => {
  const id = useId();
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const [query, setQuery] = useState<string>("");
  const [searchResults, setSearchResults] = useState<LocationSearchResult[]>(
    [],
  );
  const [isSearching, setIsSearching] = useState<boolean>(false);
  const [gpsLoading, setGpsLoading] = useState<boolean>(false);
  const [gpsError, setGpsError] = useState<string | null>(null);
  const [focusedIndex, setFocusedIndex] = useState<number>(-1);

  const searchInputRef = useRef<HTMLInputElement>(null);
  const popoverRef = useRef<HTMLDivElement>(null);
  const gpsRequest = useRef<AbortController | null>(null);

  useEffect(() => () => gpsRequest.current?.abort(), []);

  // Focus search input when popover opens
  useEffect(() => {
    if (isOpen) {
      setGpsError(null);
      setFocusedIndex(-1);
      searchInputRef.current?.focus();
    }
  }, [isOpen]);

  // Debounced search (300ms)
  useEffect(() => {
    const trimmed = query.trim();
    if (trimmed.length < 2) {
      setSearchResults([]);
      setIsSearching(false);
      return;
    }

    const controller = new AbortController();
    setIsSearching(true);
    setSearchResults([]);
    setFocusedIndex(-1);
    const debounceTimer = setTimeout(async () => {
      try {
        const res = await fetch(
          `/api/locations/search?q=${encodeURIComponent(trimmed)}`,
          { signal: controller.signal },
        );
        if (!res.ok || controller.signal.aborted) return;
        const data: LocationSearchResult[] = await res.json();
        if (controller.signal.aborted) return;
        setSearchResults(data);
        setFocusedIndex(-1);
      } catch {
        // Fallback gracefully on search error
        if (!controller.signal.aborted) setSearchResults([]);
      } finally {
        if (!controller.signal.aborted) setIsSearching(false);
      }
    }, 300);

    return () => {
      controller.abort();
      clearTimeout(debounceTimer);
    };
  }, [query]);

  // Close on Escape or click outside
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        setIsOpen(false);
      }
    };

    const handleClickOutside = (e: MouseEvent) => {
      if (
        popoverRef.current &&
        e.target instanceof Node &&
        !popoverRef.current.contains(e.target)
      ) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener("keydown", handleKeyDown);
      document.addEventListener("mousedown", handleClickOutside);
    }

    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isOpen]);

  const selectLocation = (location: ActiveLocation) => {
    gpsRequest.current?.abort();
    gpsRequest.current = null;
    setGpsLoading(false);
    onSelectLocation(location);
    setIsOpen(false);
  };

  const handleUseMyLocation = () => {
    setGpsError(null);

    if (!navigator.geolocation) {
      setGpsError(
        "Geolocation is not supported by your browser. Search your area manually.",
      );
      return;
    }

    const controller = new AbortController();
    gpsRequest.current?.abort();
    gpsRequest.current = controller;
    setGpsLoading(true);

    navigator.geolocation.getCurrentPosition(
      async ({ coords }) => {
        if (controller.signal.aborted) return;
        const { latitude: lat, longitude: lon } = coords;
        let label = "Current Location";

        try {
          const revRes = await fetch(
            `/api/locations/reverse?lat=${lat.toFixed(2)}&lon=${lon.toFixed(2)}`,
            { signal: controller.signal },
          );
          if (revRes.ok) {
            const revData: ReverseGeocodeResult = await revRes.json();
            label = revData.label || `${revData.city || "Current Area"}, India`;
          }
        } catch {
          label = "GPS Location";
        }
        if (!controller.signal.aborted)
          selectLocation({ label, lat, lon, origin: "gps" });
      },
      (err) => {
        if (controller.signal.aborted) return;
        gpsRequest.current = null;
        setGpsLoading(false);
        if (err.code === err.PERMISSION_DENIED) {
          setGpsError(
            "Location access blocked. Search any Indian city or locality below.",
          );
        } else {
          setGpsError("Couldn't detect GPS. Enter your area manually.");
        }
      },
      {
        enableHighAccuracy: false,
        timeout: 8000,
        maximumAge: 300_000,
      },
    );
  };

  const handleSelectSearchResult = (item: LocationSearchResult) => {
    selectLocation({
      label: item.label,
      lat: item.lat,
      lon: item.lon,
      origin: "search",
    });
  };

  const handleSelectQuickCity = (city: (typeof QUICK_CITIES)[0]) => {
    selectLocation({
      label: `${city.name} (${city.state})`,
      lat: city.lat,
      lon: city.lon,
      origin: "search",
    });
  };

  const handleComboboxKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (searchResults.length === 0) return;

    if (e.key === "ArrowDown") {
      e.preventDefault();
      setFocusedIndex((prev) => (prev + 1) % searchResults.length);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setFocusedIndex(
        (prev) => (prev <= 0 ? searchResults.length - 1 : prev - 1),
      );
    } else if (
      e.key === "Enter" &&
      focusedIndex >= 0 &&
      focusedIndex < searchResults.length
    ) {
      e.preventDefault();
      handleSelectSearchResult(searchResults[focusedIndex]);
    }
  };

  const isLive = stationStatus === "live";

  return (
    <div className="relative inline-block" ref={popoverRef}>
      {/* Trigger Pill */}
      {!gate && (
        <button
          type="button"
          aria-haspopup="dialog"
          aria-expanded={isOpen}
          aria-label={`Change location. Currently selected: ${activeLocation?.label ?? "None"}`}
          onClick={() => setIsOpen((prev) => !prev)}
          className="min-h-[44px] px-3.5 py-1.5 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-elevated)] hover:bg-[var(--bg-surface)] text-[var(--text-primary)] transition-all focus:outline-none focus:ring-2 focus:ring-teal-500 inline-flex items-center gap-2.5 text-xs font-semibold shadow-2xs cursor-pointer group"
        >
          <span className="p-1 rounded-md bg-teal-50 text-teal-700 dark:bg-teal-950 dark:text-teal-400 group-hover:scale-105 transition-transform">
            <MapPin
              className="w-3.5 h-3.5"
              strokeWidth={2}
              aria-hidden="true"
            />
          </span>

          <span className="max-w-[140px] sm:max-w-[190px] truncate font-bold text-[var(--text-primary)]">
            {activeLocation?.label ?? "Choose location"}
          </span>

          {typeof stationDistanceKm === "number" && (
            <span className="text-[11px] text-[var(--text-secondary)] font-mono hidden xs:inline">
              ({stationDistanceKm.toFixed(1)} km)
            </span>
          )}

          {stationStatus && (
            <span
              className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider border ${
                isLive
                  ? "bg-emerald-50 text-emerald-800 border-emerald-300 dark:bg-emerald-950/80 dark:text-emerald-300 dark:border-emerald-700"
                  : "bg-amber-50 text-amber-800 border-amber-300 dark:bg-amber-950/80 dark:text-amber-300 dark:border-amber-700"
              }`}
            >
              <span
                aria-hidden="true"
                className={`w-1.5 h-1.5 rounded-full ${
                  isLive ? "bg-emerald-500 animate-pulse" : "bg-amber-500"
                }`}
              />
              {stationStatus === "modelled_live" ? "Modelled" : stationStatus}
            </span>
          )}

          {isLoading && (
            <Loader2
              className="w-3.5 h-3.5 text-teal-600 animate-spin"
              aria-hidden="true"
            />
          )}
        </button>
      )}

      {/* Popover / Panel Modal */}
      <AnimatePresence>
        {(isOpen || gate) && (
          <m.div
            initial={{ opacity: 0, y: 8, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 8, scale: 0.98 }}
            transition={{ duration: 0.18, ease: "easeOut" }}
            role={gate ? "region" : "dialog"}
            aria-label="Location Search and Geolocation"
            className={`${gate ? "relative w-full max-w-xl mx-auto" : "absolute right-0 sm:left-0 sm:right-auto mt-2 w-[calc(100vw-2rem)] sm:w-[380px]"} bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl shadow-xl p-4 z-50 space-y-4 text-left`}
          >
            {/* Popover Header */}
            <div className="flex items-center justify-between pb-2 border-b border-[var(--border-subtle)]">
              <div className="flex items-center gap-2">
                <MapPin
                  className="w-4 h-4 text-teal-600 dark:text-teal-400"
                  aria-hidden="true"
                />
                <p className="text-sm font-bold text-[var(--text-primary)]">
                  Choose Location
                </p>
              </div>
              {!gate && (
                <button
                  type="button"
                  onClick={() => setIsOpen(false)}
                  aria-label="Close location selector"
                  className="min-h-[44px] min-w-[44px] p-1 rounded-lg hover:bg-[var(--bg-elevated)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-teal-500"
                >
                  <X className="w-4 h-4" aria-hidden="true" />
                </button>
              )}
            </div>

            {/* GPS Geolocation Button */}
            <button
              type="button"
              onClick={handleUseMyLocation}
              disabled={gpsLoading}
              className="w-full min-h-[44px] px-3.5 py-2.5 rounded-xl bg-teal-700 hover:bg-teal-800 text-white font-bold text-xs flex items-center justify-center gap-2 focus:outline-none focus:ring-2 focus:ring-teal-400 shadow-xs cursor-pointer disabled:opacity-60 transition-colors"
            >
              {gpsLoading ? (
                <>
                  <Loader2
                    className="w-4 h-4 animate-spin"
                    aria-hidden="true"
                  />
                  <span>Detecting GPS Coordinates...</span>
                </>
              ) : (
                <>
                  <LocateFixed
                    className="w-4 h-4"
                    strokeWidth={2}
                    aria-hidden="true"
                  />
                  <span>
                    {gate ? "Use My Live Location" : "Use My Location (GPS)"}
                  </span>
                </>
              )}
            </button>

            {/* Inline GPS Error Feedback */}
            {gpsError && (
              <div
                role="alert"
                className="p-2.5 rounded-xl bg-amber-50 dark:bg-amber-950/60 border border-amber-200 dark:border-amber-800 text-amber-900 dark:text-amber-200 text-xs flex items-start gap-2"
              >
                <AlertCircle
                  className="w-4 h-4 shrink-0 text-amber-600 dark:text-amber-400 mt-0.5"
                  aria-hidden="true"
                />
                <span>{gpsError}</span>
              </div>
            )}

            {/* Debounced Search Combobox */}
            <div className="space-y-1.5">
              <label
                htmlFor={`${id}-search`}
                className="block text-xs font-semibold text-[var(--text-secondary)]"
              >
                Search Any Indian City / Locality
              </label>

              <div className="relative">
                <Search
                  className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-secondary)]"
                  aria-hidden="true"
                />
                <input
                  ref={searchInputRef}
                  id={`${id}-search`}
                  type="text"
                  role="combobox"
                  aria-expanded={searchResults.length > 0}
                  aria-controls={
                    searchResults.length ? `${id}-options` : undefined
                  }
                  aria-autocomplete="list"
                  aria-activedescendant={
                    focusedIndex >= 0 ? `${id}-opt-${focusedIndex}` : undefined
                  }
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={handleComboboxKeyDown}
                  placeholder="e.g. Noida Sector 62, Indirapuram, Connaught Place..."
                  className="w-full min-h-[44px] pl-9 pr-9 py-2 text-xs rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-elevated)] text-[var(--text-primary)] placeholder-[var(--text-secondary)] focus:outline-none focus:ring-2 focus:ring-teal-500"
                />

                {isSearching && (
                  <Loader2
                    className="w-4 h-4 absolute right-3 top-1/2 -translate-y-1/2 text-teal-600 animate-spin"
                    aria-hidden="true"
                  />
                )}
                {!isSearching && query.length > 0 && (
                  <button
                    type="button"
                    onClick={() => setQuery("")}
                    aria-label="Clear search query"
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
                  >
                    <X className="w-3.5 h-3.5" aria-hidden="true" />
                  </button>
                )}
              </div>
            </div>

            {/* Autocomplete Search Results */}
            {searchResults.length > 0 && (
              <ul
                id={`${id}-options`}
                role="listbox"
                aria-label="Search Results"
                className="max-h-48 overflow-y-auto space-y-1 border border-[var(--border-subtle)] rounded-xl p-1 bg-[var(--bg-elevated)]"
              >
                {searchResults.map((item, idx) => {
                  const isFocused = focusedIndex === idx;
                  return (
                    <li
                      key={`${item.lat}-${item.lon}-${idx}`}
                      id={`${id}-opt-${idx}`}
                      role="option"
                      aria-selected={isFocused}
                      onClick={() => handleSelectSearchResult(item)}
                      className={`p-2 rounded-lg text-xs cursor-pointer flex items-center justify-between transition-colors ${
                        isFocused
                          ? "bg-teal-700 text-white"
                          : "text-[var(--text-primary)] hover:bg-[var(--bg-surface)]"
                      }`}
                    >
                      <span className="truncate font-medium">{item.label}</span>
                      <span
                        className={`text-[10px] shrink-0 ml-2 ${
                          isFocused
                            ? "text-teal-100"
                            : "text-[var(--text-secondary)]"
                        }`}
                      >
                        {item.state}
                      </span>
                    </li>
                  );
                })}
              </ul>
            )}

            {/* Quick 1-Click Indian City Chips */}
            <div className="space-y-1.5 pt-1">
              <span className="block text-[11px] font-semibold text-[var(--text-secondary)]">
                Quick Metropolitan Hubs:
              </span>
              <div className="flex flex-wrap gap-1.5">
                {QUICK_CITIES.map((city) => (
                  <button
                    key={city.name}
                    type="button"
                    onClick={() => handleSelectQuickCity(city)}
                    className="min-h-[44px] px-2.5 py-1 text-[11px] font-bold rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-elevated)] hover:bg-teal-50 dark:hover:bg-teal-950/60 hover:text-teal-800 dark:hover:text-teal-300 text-[var(--text-primary)] transition-colors focus:outline-none focus:ring-2 focus:ring-teal-500 inline-flex items-center gap-1 cursor-pointer"
                  >
                    <Building
                      className="w-3 h-3 text-teal-600 dark:text-teal-400"
                      aria-hidden="true"
                    />
                    <span>{city.name}</span>
                  </button>
                ))}
              </div>
            </div>
          </m.div>
        )}
      </AnimatePresence>
    </div>
  );
};
