import React from "react";
import { Link } from "react-router-dom";
import "../styliing/home.css";

function Home() {
  return (
    <div className="home">
      <div className="hero-section">
        <h1>Welcome to DocGen</h1>
        <p>Generate documentation for your projects effortlessly.</p>
        <Link to="/upload" className="cta-button">
          Get Started
        </Link>
      </div>
      <div className="features-section">
        <h2>Features</h2>
        <div className="features-grid">
          <div className="feature">
            <h3>Folder Upload</h3>
            <p>
              Upload your project folder and generate documentation instantly.
            </p>
          </div>
          <div className="feature">
            <h3>GitHub Integration</h3>
            <p>Analyze GitHub repositories and generate docs automatically.</p>
          </div>
          <div className="feature">
            <h3>Download as PDF</h3>
            <p>Export your documentation as a PDF for easy sharing.</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Home;
