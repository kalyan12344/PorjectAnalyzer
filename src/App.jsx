import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";

import FolderUpload from "./frontend/components/folderupload";

function App() {
  return (
    <Router>
      <div className="app">
        <Routes>
          <Route path="/" element={<FolderUpload />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
