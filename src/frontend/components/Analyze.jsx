import React, { useState, useEffect } from "react";
// import * as echarts from "echarts";
import "../styliing/analyze.css";
import axios from "axios";

const Analyze = () => {
  const [repoUrl, setRepoUrl] = useState("");
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [activeTab, setActiveTab] = useState("suggestions");
  const [showResults, setShowResults] = useState(false);
  const [isGeneratingDocs, setIsGeneratingDocs] = useState(false);
  const [suggestionText, setSuggestionText] = useState("");
  const [documentationText, setDocumentationText] = useState("");

  const [analysisOptions, setAnalysisOptions] = useState({
    suggestions: true,
    documentation: true,
    performance: true,
  });

  const handleAnalyze = async () => {
    if (!repoUrl) return;
    setIsAnalyzing(true);
    setShowResults(false);

    try {
      const response = await axios.post(
        "http://localhost:5000/generate-suggestions",
        {
          repo_url: repoUrl,
        }
      );

      const { suggestions } = response.data;

      // TODO: Store suggestions in state to render in UI
      console.log("✅ Suggestions:", suggestions);
      setSuggestionText(suggestions);
      setShowResults(true);
    } catch (error) {
      console.error("❌ API error:", error.response?.data || error.message);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleGenerateDocs = async () => {
    if (!repoUrl) return;
    setIsGeneratingDocs(true);
    setShowResults(false);
    try {
      const response = await axios.post("http://localhost:5000/generate-docs", {
        repo_url: repoUrl,
      });

      const { documentation } = response.data;
      console.log("📄 Docs:", documentation);
      setDocumentationText(documentation);

      // Optional: Set to state to show in the UI
      setShowResults(true);
    } catch (err) {
      console.error(
        "❌ Error generating docs",
        err.response?.data || err.message
      );
    } finally {
      setIsGeneratingDocs(false);
    }
  };

  //   useEffect(() => {
  //     if (showResults) {
  //       const chart = echarts.init(document.getElementById("performanceChart"));
  //       const option = {
  //         animation: false,
  //         tooltip: { trigger: "axis" },
  //         xAxis: {
  //           type: "category",
  //           data: ["Code Quality", "Performance", "Security", "Maintainability"],
  //           axisLine: { lineStyle: { color: "#666" } },
  //         },
  //         yAxis: {
  //           type: "value",
  //           max: 100,
  //           axisLine: { lineStyle: { color: "#666" } },
  //         },
  //         series: [
  //           {
  //             data: [85, 92, 78, 88],
  //             type: "bar",
  //             itemStyle: { color: "#6366F1" },
  //           },
  //         ],
  //       };
  //       chart.setOption(option);
  //     }
  //   }, [showResults]);

  return (
    <div className="app">
      <div className="background">
        <div className="bg-gradient"></div>
        <div className="bg-pulse">
          <div className="blur-circle indigo"></div>
          <div className="blur-circle purple"></div>
          <div className="blur-circle blue"></div>
        </div>
        <div className="floating-circles">
          {Array.from({ length: 20 }).map((_, i) => (
            <div
              key={i}
              className="circle"
              style={{
                top: `${Math.random() * 100}%`,
                left: `${Math.random() * 100}%`,
                width: `${Math.random() * 3 + 1}px`,
                height: `${Math.random() * 3 + 1}px`,
                opacity: Math.random() * 0.5 + 0.1,
                animationDuration: `${Math.random() * 10 + 10}s`,
              }}
            ></div>
          ))}
        </div>
      </div>

      <header className="header">
        <div className="header-content">
          <div className="logo">
            <i className="fas fa-code"></i>
            <span>CodeAnalyzer</span>
          </div>
          <nav className="nav">
            <a data-readdy="true">Dashboard</a>
            <a href="#">Documentation</a>
            <a href="#">Settings</a>
          </nav>
        </div>
      </header>

      <main className="main">
        <div className="intro">
          <h1>Analyze Your Repository</h1>
          <p>
            Get comprehensive insights, suggestions, and documentation for your
            Git repository
          </p>
        </div>

        <div className="input-section">
          <div className="input-wrapper">
            <input
              type="text"
              value={repoUrl}
              onChange={(e) => setRepoUrl(e.target.value)}
              placeholder="Enter your Git repository URL"
            />
            <i className="fas fa-link input-icon"></i>
          </div>
          <div className="buttons" style={{ height: "20px" }}>
            <button
              onClick={handleAnalyze}
              disabled={isAnalyzing || !repoUrl}
              className="btn indigo"
              style={{ height: "50px", width: "100px" }}
            >
              {isAnalyzing ? (
                <>
                  <i className="fas fa-circle-notch fa-spin"></i>
                  <span>Analyzing Suggestions...</span>
                </>
              ) : (
                <>
                  <i className="fas fa-lightbulb"></i>
                  <span>Generate Suggestions</span>
                </>
              )}
            </button>
            <button
              onClick={handleGenerateDocs}
              disabled={isGeneratingDocs || !repoUrl}
              className="btn purple"
              style={{ height: "50px", width: "100px" }}
            >
              {isGeneratingDocs ? (
                <>
                  <i className="fas fa-circle-notch fa-spin"></i>
                  <span>Generating Document...</span>
                </>
              ) : (
                <>
                  <i className="fas fa-file-alt"></i>
                  <span>Generate Documentation</span>
                </>
              )}
            </button>
          </div>
        </div>

        {showResults && (
          <div className="results">
            <div className="tabs">
              {["suggestions", "documentation", "performance"].map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`tab ${activeTab === tab ? "active" : ""}`}
                >
                  {tab}
                </button>
              ))}
            </div>

            <div className="tab-content">
              {activeTab === "suggestions" && (
                <div className="">
                  <div className="suggestion">
                    <pre
                      className="suggestion-text"
                      style={{ backgroundColor: "" }}
                    >
                      {suggestionText || "No suggestions yet."}
                    </pre>
                  </div>
                </div>
              )}
              {activeTab === "documentation" && (
                <div className="">
                  <h2>Project Documentation</h2>
                  <pre className="doc-text">
                    {documentationText || "No documentation generated yet."}
                  </pre>
                </div>
              )}
              {activeTab === "performance" && (
                <div id="performanceChart" style={{ height: "400px" }}></div>
              )}
            </div>
          </div>
        )}
      </main>

      <footer className="footer">
        <div className="footer-content">
          <div className="status">
            <span>Last analyzed: March 28, 2025 14:30</span>
            <span>|</span>
            <span>Status: Ready</span>
          </div>
          <div className="health">
            <i className="fas fa-check-circle"></i>
            <span>All systems operational</span>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Analyze;
