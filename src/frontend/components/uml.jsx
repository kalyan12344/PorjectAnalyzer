import React, { useState } from "react";
import axios from "axios";

function UmlDiagrams({ repoUrl, projectName }) {
  const [umlDiagrams, setUmlDiagrams] = useState(null);
  const [loadingUml, setLoadingUml] = useState(false);

  const handleGenerateUML = async () => {
    if (!repoUrl) return;
    setLoadingUml(true);

    try {
      const response = await axios.post("http://127.0.0.1:5000/generate-uml-images", {
        repo_url: repoUrl,
      });

      setUmlDiagrams(response.data.uml_diagrams);
    } catch (error) {
      console.error("UML generation error:", error);
    } finally {
      setLoadingUml(false);
    }
  };

  return (
    <div className="uml-section">
      <button className="download-btn" onClick={handleGenerateUML} disabled={loadingUml}>
        {loadingUml ? "Generating UML..." : "📊 Generate UML Diagrams"}
      </button>

      {umlDiagrams && (
        <div className="uml-images">
          {Object.entries(umlDiagrams).map(([type, data]) => (
            <div key={type} className="uml-diagram">
              <h4>{type.replace("_", " ").toUpperCase()} Diagram</h4>
              <img
                src={data.image_url}
                alt={`${type} diagram`}
                style={{ width: "100%", borderRadius: "12px", marginBottom: "20px" }}
              />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default UmlDiagrams;
