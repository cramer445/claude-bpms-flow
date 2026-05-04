import { Routes, Route } from "react-router-dom";
import ProcessList from "./components/ProcessList";
import ProcessEditor from "./components/ProcessEditor";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<ProcessList />} />
      <Route path="/editor/new" element={<ProcessEditor />} />
      <Route path="/editor/:id" element={<ProcessEditor />} />
    </Routes>
  );
}
