import React, { useState, useEffect } from "react";
import "../styliing/imageupload.css";
const ImageUploader = () => {
  const [image, setImage] = useState(null);
  const [preview, setPreview] = useState(null);
  const [uiElements, setUiElements] = useState([]);
  const [generatedPrompt, setGeneratedPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const handlePaste = (e) => {
      const items = e.clipboardData.items;
      for (let item of items) {
        if (item.type.indexOf("image") !== -1) {
          const file = item.getAsFile();
          setImage(file);
          setPreview(URL.createObjectURL(file));
          break;
        }
      }
    };

    window.addEventListener("paste", handlePaste);
    return () => window.removeEventListener("paste", handlePaste);
  }, []);

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    setImage(file);
    setPreview(URL.createObjectURL(file));
  };

  const handleUpload = async () => {
    if (!image) {
      setError("Please select or paste an image first.");
      return;
    }

    setLoading(true);
    setError("");
    setUiElements([]);
    setGeneratedPrompt("");

    const formData = new FormData();
    formData.append("image", image);

    try {
      const res = await fetch("http://localhost:5000/upload-image", {
        method: "POST",
        body: formData,
      });

      const data = await res.json();
      if (res.ok) {
        setUiElements(data.ui_elements);
        setGeneratedPrompt(data.generated_prompt);
      } else {
        setError(data.error || "Something went wrong.");
      }
    } catch (err) {
      setError("Failed to upload image.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      <div className="card">
        <h1>🧠 UI Prompt Generator</h1>
        <p className="subtext">
          Upload or paste a UI screenshot to generate a prompt.
        </p>

        <div className="upload-box">
          <input type="file" accept="image/*" onChange={handleImageChange} />
          <p className="paste-hint">
            Or paste an image here using <strong>Ctrl+V</strong>
          </p>

          {preview && (
            <img src={preview} alt="Preview" className="image-preview" />
          )}

          <button onClick={handleUpload} disabled={loading}>
            {loading ? "Processing..." : "Upload & Generate"}
          </button>

          {error && <p className="error-text">{error}</p>}
        </div>

        {uiElements.length > 0 && (
          <div className="result-box">
            <h2>🧩 Extracted UI Elements</h2>
            <ul>
              {uiElements.map((el, idx) => (
                <li key={idx}>
                  <strong>{el.type}</strong>: “{el.content}” at{" "}
                  {JSON.stringify(el.position)}
                </li>
              ))}
            </ul>
          </div>
        )}

        {generatedPrompt && (
          <div className="result-box">
            <h2>📝 Generated Prompt</h2>
            <pre>{generatedPrompt}</pre>
          </div>
        )}
      </div>
    </div>
  );
};

export default ImageUploader;
