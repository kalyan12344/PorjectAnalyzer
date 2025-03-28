import React, { useRef, useState } from "react";
import {
  Folder,
  Upload,
  Trash,
  File,
  GitBranch,
  Download,
  SparklesIcon,
  FileX,
} from "lucide-react";
import axios from "axios";
import ReactMarkdown from "react-markdown";
import UmlDiagrams from "./uml";

import "../styliing/folderupload.css"; // Import CSS file
// import "../styliing/Doc-Gen.css";

function FolderUpload() {
  const folderInputRef = useRef(null);
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [documentation, setDocumentation] = useState(""); // Stores documentation
  const [gitRepo, setGitRepo] = useState(""); // Stores GitHub URL
  const [loadingGit, setLoadingGit] = useState(false);
  const [activeTab, setActiveTab] = useState("documentation");
  //   const [activeView, setActiveView] = useState("documentation");

  // Open folder selection
  const handleFolderClick = () => {
    folderInputRef.current?.click();
  };

  const handleFolderChange = (event) => {
    const selectedFiles = Array.from(event.target.files);
    setFiles(selectedFiles);
  };

  const [loadingSuggestions, setLoadingSuggestions] = useState(false);
  const [suggestions, setSuggestions] = useState(""); // Store AI suggestions

  const handleGenerateSuggestions = async () => {
    if (!gitRepo) {
      console.error("No GitHub repo URL provided.");
      return;
    }

    setLoadingSuggestions(true);

    try {
      const response = await axios.post(
        "http://127.0.0.1:5000/generate-suggestions",
        { repo_url: gitRepo }
      );

      setSuggestions(response.data.suggestions);
    } catch (error) {
      console.error("Suggestions generation error:", error);
      setSuggestions("Error generating suggestions.");
    } finally {
      setLoadingSuggestions(false);
    }
  };

  // Handle drag and drop
  const handleDrop = (event) => {
    event.preventDefault();
    const droppedFiles = Array.from(event.dataTransfer.files);
    setFiles(droppedFiles);
  };

  const handleDragOver = (event) => {
    event.preventDefault();
  };

  const handleClearFiles = () => {
    setFiles([]);
    setDocumentation("");
  };

  const handleUpload = async () => {
    if (files.length === 0) return;
    setUploading(true);

    const formData = new FormData();
    files.forEach((file) => {
      formData.append("files", file);
    });

    try {
      const response = await axios.post(
        "http://127.0.0.1:5000/generate-docs",
        formData,
        {
          headers: { "Content-Type": "multipart/form-data" },
        }
      );

      console.log("Upload successful:", response.data);
      fetchDocumentation(response.data.documentation_url);
    } catch (error) {
      console.error("Upload error:", error);
    } finally {
      setUploading(false);
    }
  };

  const handleDownloadPDF = async () => {
    if (!documentation) return;

    try {
      const response = await axios.post("http://127.0.0.1:5000/generate-pdf", {
        documentation: documentation,
        project_name: gitRepo ? gitRepo.split("/").pop() : "Project",
      });

      if (response.data.pdf_url) {
        window.open(response.data.pdf_url, "_blank"); // ✅ Open the PDF link in a new tab
      }
    } catch (error) {
      console.error("PDF Generation Error:", error);
    }
  };

  const handleAnalyzeGitRepo = async () => {
    console.log("Analyzing GitHub repository:", gitRepo);
    if (!gitRepo) return;
    setLoadingGit(true);

    try {
      const response = await axios.post("http://127.0.0.1:5000/generate-docs", {
        repo_url: gitRepo,
      });

      console.log("GitHub Analysis successful:", response.data);
      setDocumentation(response.data.documentation); // ✅ Correct key
    } catch (error) {
      console.error("GitHub Analysis error:", error);
    } finally {
      setLoadingGit(false);
    }
  };

  const fetchDocumentation = async (url) => {
    try {
      const response = await axios.get(url);
      setDocumentation(response.data);
    } catch (error) {
      console.error("Failed to fetch documentation:", error);
      setDocumentation("Error loading documentation.");
    }
  };

  return (
    <div>
      <h2>Upload a Project Folder or Analyze GitHub </h2>
      <div className="upload-container">
        <div className="upload-section">
          <h3>Upload Folder</h3>
          <div
            className="drop-zone"
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onClick={handleFolderClick}
          >
            <Folder className="folder-icon" />
            <p>Drag & drop your project folder here</p>
          </div>

          <input
            type="file"
            ref={folderInputRef}
            webkitdirectory=""
            directory=""
            multiple
            onChange={handleFolderChange}
            className="file-input"
          />

          {files.length > 0 && (
            <div className="file-list">
              <div className="file-header">
                <p>{files.length} files selected</p>
                <button className="clear-btn" onClick={handleClearFiles}>
                  <Trash size={16} /> Clear
                </button>
              </div>
              <ul>
                {files.slice(0, 5).map((file, index) => (
                  <li key={index}>
                    <File size={16} className="file-icon" />
                    {file.name}
                  </li>
                ))}
                {files.length > 5 && <li>+ {files.length - 5} more files</li>}
              </ul>
            </div>
          )}

          {/* Upload Button */}
          <button
            className="upload-btn"
            style={{ width: "200px" }}
            onClick={handleUpload}
            disabled={files.length === 0 || uploading}
          >
            {uploading ? (
              "Uploading..."
            ) : (
              <>
                <Upload size={16} /> Upload Folder
              </>
            )}
          </button>
        </div>

        <div className="github-section">
          <h3>Analyze GitHub Repository</h3>
          <div className="github-input-container">
            <input
              type="text"
              placeholder="Enter GitHub repo URL"
              value={gitRepo}
              onChange={(e) => setGitRepo(e.target.value)}
              className="github-input"
            />
            <button
              className="github-btn"
              onClick={handleAnalyzeGitRepo}
              disabled={!gitRepo || loadingGit}
            >
              {loadingGit ? (
                "Analyzing..."
              ) : (
                <>
                  <GitBranch size={16} /> Analyze Repo
                </>
              )}
            </button>
            <button
              className="suggestions-btn"
              onClick={handleGenerateSuggestions}
              disabled={!gitRepo || loadingSuggestions}
            >
              {loadingSuggestions ? "Analyzing..." : "Code Suggestions"}
            </button>
          </div>
        </div>
      </div>
      {(documentation || suggestions) && (
        <div
          style={{
            display: "flex",
            justifyContent: "flex-start",
            alignItems: "baseline",
          }}
        >
          <div
            className="tab-nav"
            style={{
              width: "20px",
              display: "flex",
              justifyContent: "flex-start",
              alignItems: "baseline",
              flexDirection: "column",
            }}
          >
            <button
              className={`tab-btn ${
                activeTab === "documentation" ? "active" : ""
              }`}
              onClick={() => setActiveTab("documentation")}
            >
              D
            </button>
            <button
              className={`tab-btn ${
                activeTab === "suggestions" ? "active" : ""
              }`}
              onClick={() => setActiveTab("suggestions")}
              disabled={!suggestions}
            >
              S
            </button>
          </div>

          {activeTab === "documentation" && documentation && (
            <div className="doc-sec">
              <div className="doc-btn">
                <button className="download-btn" onClick={handleDownloadPDF}>
                  <Download size={16} /> Download PDF
                </button>
                <button
                  className="suggestions-btn"
                  onClick={handleGenerateSuggestions}
                  disabled={loadingSuggestions}
                >
                  {loadingSuggestions ? "Analyzing..." : " Code Suggestions"}
                </button>
              </div>

              <div className="documentation">
                <h3>📄 Generated Documentation</h3>
                <ReactMarkdown>{documentation}</ReactMarkdown>

                <UmlDiagrams
                  repoUrl={gitRepo}
                  projectName={gitRepo?.split("/").pop()}
                />
              </div>
            </div>
          )}

          {activeTab === "suggestions" && suggestions && (
            <div className="suggestions">
              <h3>💡 AI Code Suggestions</h3>
              <ReactMarkdown>{suggestions}</ReactMarkdown>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default FolderUpload;
