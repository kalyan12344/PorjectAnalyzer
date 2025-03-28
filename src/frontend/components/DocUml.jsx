import React, { useRef, useState } from "react";
import { Folder, Upload, Trash, File, GitBranch } from "lucide-react";
import axios from "axios";
import ReactMarkdown from "react-markdown";
import UmlDiagrams from "./uml";
import "./DocuUML.css"; // Import the CSS file

function FolderUpload() {
  const folderInputRef = useRef(null);
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [documentation, setDocumentation] = useState("");
  const [gitRepo, setGitRepo] = useState("");
  const [loadingGit, setLoadingGit] = useState(false);
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);
  const [suggestions, setSuggestions] = useState("");

  const handleFolderClick = () => {
    folderInputRef.current?.click();
  };

  const handleFolderChange = (event) => {
    const selectedFiles = Array.from(event.target.files);
    setFiles(selectedFiles);
  };

  const handleGenerateSuggestions = async () => {
    if (!documentation) {
      console.error("No documentation available for suggestions.");
      return;
    }

    setLoadingSuggestions(true);

    try {
      const response = await axios.post(
        "http://127.0.0.1:5000/generate-suggestions",
        {
          documentation: documentation,
          project_name: gitRepo ? gitRepo.split("/").pop() : "Project",
        }
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

  // Handle GitHub repository analysis
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

  // Fetch documentation
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
    <div className="docuuml-container">
      <div className="header">
        <h2 className="title">DocuUML AI</h2>
        <div className="github-link">
          <a
            href="https://github.com/username/repo" // Replace with your repo link
            target="_blank"
            rel="noopener noreferrer"
          >
            GitHub Repository
          </a>
        </div>
      </div>

      <div className="content">
        <div className="upload-section">
          <div
            className="drop-zone"
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onClick={handleFolderClick}
          >
            <Folder className="folder-icon" />
            <p>Drop your folder here</p>
            <p>or click to browse</p>
            {files.length > 0 && (
              <div className="file-list">
                <p>{files.length} files</p>
                <ul>
                  {files.slice(0, 3).map((file, index) => (
                    <li key={index}>
                      <File className="file-icon" /> {file.name}
                    </li>
                  ))}
                  {files.length > 3 && <li>+{files.length - 3} more files</li>}
                </ul>
              </div>
            )}
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
          <button
            className="upload-btn"
            onClick={handleUpload}
            disabled={files.length === 0 || uploading}
          >
            {uploading ? "Analyzing Repository..." : "Upload & Analyze"}
          </button>
        </div>

        <div className="git-section">
          <input
            type="text"
            placeholder="https://github.com/username/repo"
            value={gitRepo}
            onChange={(e) => setGitRepo(e.target.value)}
            className="git-input"
          />
          <button
            className="analyze-btn"
            onClick={handleAnalyzeGitRepo}
            disabled={!gitRepo || loadingGit}
          >
            {loadingGit ? "Analyzing Repository..." : "Analyzing Repository..."}
          </button>
        </div>

        {documentation && (
          <div className="documentation-section">
            <div className="doc-header">
              <h3>Documentation</h3>
              <div className="doc-buttons">
                <button className="pdf-btn" onClick={handleDownloadPDF}>
                  Download PDF
                </button>
                <button
                  className="ai-btn"
                  onClick={handleGenerateSuggestions}
                  disabled={loadingSuggestions}
                >
                  {loadingSuggestions
                    ? "Get AI Suggestions"
                    : "Get AI Suggestions"}
                </button>
              </div>
            </div>

            <div className="project-structure">
              <h4>Project Structure</h4>
              <ReactMarkdown>{documentation}</ReactMarkdown>
            </div>

            <div className="diagrams">
              <UmlDiagrams
                repoUrl={gitRepo}
                projectName={gitRepo?.split("/").pop()}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default FolderUpload;
