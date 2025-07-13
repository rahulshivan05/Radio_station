import React, { useState, useEffect, useRef } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const RadioPlayer = () => {
  const [stations, setStations] = useState([]);
  const [currentStation, setCurrentStation] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [volume, setVolume] = useState(0.7);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCountry, setSelectedCountry] = useState("");
  const [selectedGenre, setSelectedGenre] = useState("");
  const [countries, setCountries] = useState([]);
  const [genres, setGenres] = useState([]);
  const [error, setError] = useState("");
  
  const audioRef = useRef(null);

  // Load popular stations on mount
  useEffect(() => {
    loadPopularStations();
    loadCountries();
    loadGenres();
  }, []);

  // Update audio element when station changes
  useEffect(() => {
    if (audioRef.current && currentStation) {
      audioRef.current.src = currentStation.url_resolved || currentStation.url;
      audioRef.current.volume = volume;
      
      if (isPlaying) {
        audioRef.current.play().catch(err => {
          console.error("Playback failed:", err);
          setError("Failed to play this station. The stream might be unavailable.");
          setIsPlaying(false);
        });
      }
    }
  }, [currentStation]);

  // Update volume
  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.volume = volume;
    }
  }, [volume]);

  const loadPopularStations = async () => {
    setLoading(true);
    setError("");
    try {
      const response = await axios.get(`${API}/radio/popular?limit=30`);
      setStations(response.data);
    } catch (error) {
      console.error("Error loading stations:", error);
      setError("Failed to load radio stations. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const loadCountries = async () => {
    try {
      const response = await axios.get(`${API}/radio/countries`);
      setCountries(response.data.slice(0, 50)); // Limit to top 50 countries
    } catch (error) {
      console.error("Error loading countries:", error);
    }
  };

  const loadGenres = async () => {
    try {
      const response = await axios.get(`${API}/radio/genres?limit=30`);
      setGenres(response.data);
    } catch (error) {
      console.error("Error loading genres:", error);
    }
  };

  const searchStations = async () => {
    setLoading(true);
    setError("");
    try {
      const params = new URLSearchParams();
      if (searchTerm) params.append("name", searchTerm);
      if (selectedCountry) params.append("country", selectedCountry);
      if (selectedGenre) params.append("tag", selectedGenre);
      params.append("limit", "50");

      const response = await axios.get(`${API}/radio/search?${params}`);
      setStations(response.data);
      
      if (response.data.length === 0) {
        setError("No stations found matching your criteria.");
      }
    } catch (error) {
      console.error("Error searching stations:", error);
      setError("Failed to search stations. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const playStation = async (station) => {
    setError("");
    setCurrentStation(station);
    setIsPlaying(true);
    
    // Register click for popularity tracking
    try {
      await axios.post(`${API}/radio/click/${station.stationuuid}`);
    } catch (error) {
      console.log("Click registration failed:", error);
    }
  };

  const togglePlayPause = () => {
    if (!currentStation) return;
    
    if (isPlaying) {
      audioRef.current?.pause();
      setIsPlaying(false);
    } else {
      audioRef.current?.play().catch(err => {
        console.error("Playback failed:", err);
        setError("Failed to play this station. The stream might be unavailable.");
        setIsPlaying(false);
      });
      setIsPlaying(true);
    }
  };

  const stopPlayback = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
    }
    setIsPlaying(false);
    setCurrentStation(null);
  };

  const clearFilters = () => {
    setSearchTerm("");
    setSelectedCountry("");
    setSelectedGenre("");
    loadPopularStations();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900">
      <audio ref={audioRef} crossOrigin="anonymous" />
      
      {/* Header */}
      <div className="bg-black bg-opacity-30 backdrop-blur-lg border-b border-white border-opacity-20">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <h1 className="text-4xl font-bold text-white text-center">
            🌍 Global Radio Stations
          </h1>
          <p className="text-blue-200 text-center mt-2">
            Discover and listen to radio stations from around the world
          </p>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="bg-white bg-opacity-10 backdrop-blur-lg rounded-2xl border border-white border-opacity-20 p-6 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
            <input
              type="text"
              placeholder="Search stations..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="bg-white bg-opacity-20 text-white placeholder-blue-200 border border-white border-opacity-30 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400"
              onKeyPress={(e) => e.key === 'Enter' && searchStations()}
            />
            
            <select
              value={selectedCountry}
              onChange={(e) => setSelectedCountry(e.target.value)}
              className="bg-white bg-opacity-20 text-white border border-white border-opacity-30 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400"
            >
              <option value="">All Countries</option>
              {countries.map((country) => (
                <option key={country.name} value={country.name} className="text-black">
                  {country.name} ({country.stationcount})
                </option>
              ))}
            </select>
            
            <select
              value={selectedGenre}
              onChange={(e) => setSelectedGenre(e.target.value)}
              className="bg-white bg-opacity-20 text-white border border-white border-opacity-30 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400"
            >
              <option value="">All Genres</option>
              {genres.map((genre) => (
                <option key={genre.name} value={genre.name} className="text-black">
                  {genre.name} ({genre.stationcount})
                </option>
              ))}
            </select>
            
            <div className="flex gap-2">
              <button
                onClick={searchStations}
                disabled={loading}
                className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-lg transition-colors duration-200 disabled:opacity-50"
              >
                {loading ? "Searching..." : "Search"}
              </button>
              <button
                onClick={clearFilters}
                className="bg-gray-600 hover:bg-gray-700 text-white font-semibold py-2 px-4 rounded-lg transition-colors duration-200"
              >
                Clear
              </button>
            </div>
          </div>
        </div>

        {/* Current Player */}
        {currentStation && (
          <div className="bg-white bg-opacity-10 backdrop-blur-lg rounded-2xl border border-white border-opacity-20 p-6 mb-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                  {currentStation.favicon ? (
                    <img src={currentStation.favicon} alt="Station" className="w-8 h-8 rounded-full" />
                  ) : (
                    <span className="text-white text-xl">📻</span>
                  )}
                </div>
                <div>
                  <h3 className="text-white font-semibold text-lg">{currentStation.name}</h3>
                  <p className="text-blue-200 text-sm">
                    {currentStation.country && `${currentStation.country} • `}
                    {currentStation.tags && currentStation.tags.split(',')[0]}
                    {currentStation.bitrate && ` • ${currentStation.bitrate}kbps`}
                  </p>
                </div>
              </div>
              
              <div className="flex items-center space-x-4">
                <button
                  onClick={togglePlayPause}
                  className="bg-green-600 hover:bg-green-700 text-white p-3 rounded-full transition-colors duration-200"
                >
                  {isPlaying ? "⏸️" : "▶️"}
                </button>
                <button
                  onClick={stopPlayback}
                  className="bg-red-600 hover:bg-red-700 text-white p-3 rounded-full transition-colors duration-200"
                >
                  ⏹️
                </button>
                <div className="flex items-center space-x-2">
                  <span className="text-white text-sm">🔊</span>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={volume}
                    onChange={(e) => setVolume(parseFloat(e.target.value))}
                    className="w-20"
                  />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="bg-red-500 bg-opacity-20 border border-red-500 border-opacity-30 rounded-lg p-4 mb-6">
            <p className="text-red-200">{error}</p>
          </div>
        )}

        {/* Station List */}
        <div className="bg-white bg-opacity-10 backdrop-blur-lg rounded-2xl border border-white border-opacity-20 p-6">
          <h2 className="text-2xl font-bold text-white mb-4">
            {searchTerm || selectedCountry || selectedGenre ? "Search Results" : "Popular Stations"}
          </h2>
          
          {loading ? (
            <div className="text-center py-8">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
              <p className="text-white mt-2">Loading stations...</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {stations.map((station) => (
                <div
                  key={station.stationuuid}
                  className={`bg-white bg-opacity-10 rounded-lg p-4 border border-white border-opacity-20 cursor-pointer transition-all duration-200 hover:bg-opacity-20 ${
                    currentStation?.stationuuid === station.stationuuid ? 'ring-2 ring-blue-400' : ''
                  }`}
                  onClick={() => playStation(station)}
                >
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center flex-shrink-0">
                      {station.favicon ? (
                        <img src={station.favicon} alt="Station" className="w-6 h-6 rounded-full" />
                      ) : (
                        <span className="text-white">📻</span>
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="text-white font-semibold truncate">{station.name}</h3>
                      <p className="text-blue-200 text-sm truncate">
                        {station.country && `${station.country} • `}
                        {station.tags && station.tags.split(',')[0]}
                      </p>
                      <div className="flex items-center space-x-2 mt-1">
                        {station.bitrate > 0 && (
                          <span className="text-xs bg-blue-600 text-white px-2 py-1 rounded">
                            {station.bitrate}kbps
                          </span>
                        )}
                        {station.clickcount > 0 && (
                          <span className="text-xs bg-green-600 text-white px-2 py-1 rounded">
                            {station.clickcount} plays
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
          
          {!loading && stations.length === 0 && !error && (
            <div className="text-center py-8">
              <p className="text-white">No stations found. Try adjusting your search criteria.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default RadioPlayer;