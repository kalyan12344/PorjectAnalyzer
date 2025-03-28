import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Navbar from "./frontend/components/Navbar";
import Footer from "./frontend/components/footer";
import Home from "./frontend/components/Homepage";
import FolderUpload from "./frontend/components/folderupload";
import About from "./frontend/components/about";
import Contact from "./frontend/components/contact";
import ImageUploader from "./frontend/components/imageupload";
// import FolderUpload from "./frontend/components/DocUml";
function App() {
  return (
    <Router>
      <div className="app">
        <Routes>
          {/* <Route path="/imageUpload" element={<ImageUploader />} /> */}
          {/* <Route path="/" element={<Home />} /> */}
          <Route path="/" element={<FolderUpload />} />
          {/* <Route path="/about" element={<About />} /> */}
          {/* <Route path="/contact" element={<Contact />} /> */}
        </Routes>
      </div>
    </Router>
  );
}

export default App;
